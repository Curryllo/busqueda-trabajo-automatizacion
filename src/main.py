"""Orquestador: recoge ofertas, filtra, puntúa con IA y envía el resumen por Telegram."""

import argparse

from . import config, dedupe, filters, telegram
from .providers import arbeitnow, infojobs, linkedin, remotive
from .scorer import score

PROVIDERS = [
    ("LinkedIn", linkedin.fetch),
    ("InfoJobs", infojobs.fetch),
    ("Remotive", remotive.fetch),
    ("Arbeitnow", arbeitnow.fetch),
]


def collect() -> tuple[list, list[str]]:
    jobs: list = []
    errors: list[str] = []
    for name, fetch in PROVIDERS:
        try:
            found = fetch()
            print(f"[{name}] {len(found)} ofertas obtenidas")
            jobs.extend(found)
        except Exception as exc:  # noqa: BLE001 - una fuente caída no rompe el resto
            errors.append(f"{name}: {exc}")
            print(f"[{name}] error: {exc}")
    return jobs, errors


def run(dry_run: bool = False, limit: int | None = None) -> None:
    seen = dedupe.load()
    print(f"[dedupe] {len(seen)} ofertas ya vistas")

    all_jobs, errors = collect()
    new_jobs = dedupe.filter_new(all_jobs, seen)
    print(f"[dedupe] {len(new_jobs)} ofertas nuevas de {len(all_jobs)}")

    linkedin_jobs = [j for j in new_jobs if j.source == "LinkedIn"]
    linkedin.hydrate(linkedin_jobs, limit=limit or 25)

    relevant = filters.apply(new_jobs)
    print(f"[filtros] {len(relevant)} ofertas pasan el filtro por reglas")

    relevant = score(relevant)

    any_scored = any(job.score is not None for job in relevant)
    if any_scored:
        selected = [
            job for job in relevant if job.score is None or job.score >= config.MIN_SCORE
        ]
    else:
        selected = list(relevant)  # sin IA: nos quedamos con todo lo que pasa reglas

    selected.sort(key=lambda j: (j.score if j.score is not None else 0), reverse=True)
    selected = selected[: config.MAX_DIGEST_ITEMS]
    print(f"[resultado] {len(selected)} ofertas para notificar")

    if not dry_run:
        dedupe.save(seen | {job.id for job in relevant})

    error_note = ""
    if errors and not selected:
        error_note = "Fuentes con error: " + "; ".join(errors)

    if dry_run:
        print("\n===== DIGEST (dry-run) =====\n")
        print(telegram.render(selected))
        if error_note:
            print("\n[aviso]", error_note)
        print("\n============================")
    else:
        telegram.send(selected, error_note)


def main() -> None:
    parser = argparse.ArgumentParser(description="Buscador de empleo automatizado")
    parser.add_argument("--dry-run", action="store_true", help="no envía ni guarda estado")
    parser.add_argument("--limit", type=int, default=None, help="máx. ofertas LinkedIn a detallar")
    args = parser.parse_args()
    run(dry_run=args.dry_run, limit=args.limit)


if __name__ == "__main__":
    main()
