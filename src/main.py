"""Orquestador: recoge ofertas, filtra, puntúa con IA y envía el resumen por Telegram."""

import argparse
from datetime import datetime

from . import config, dedupe, filters, telegram
from .providers import arbeitnow, infojobs, linkedin, remotive
from .scorer import score

PROVIDERS = [
    ("LinkedIn", linkedin.fetch),
    ("InfoJobs", infojobs.fetch),
    ("Remotive", remotive.fetch),
    ("Arbeitnow", arbeitnow.fetch),
]


def log(message: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] {message}", flush=True)


def collect() -> tuple[list, list[str]]:
    jobs: list = []
    errors: list[str] = []
    for name, fetch in PROVIDERS:
        try:
            found = fetch()
            log(f"{name}: {len(found)} ofertas obtenidas")
            jobs.extend(found)
        except Exception as exc:  # noqa: BLE001 - una fuente caída no rompe el resto
            errors.append(f"{name}: {exc}")
            log(f"{name}: error: {exc}")
    return jobs, errors


def run(dry_run: bool = False, limit: int | None = None) -> None:
    log("inicio de la ejecución")
    telegram_ok = telegram.is_configured()
    if not dry_run and not telegram_ok:
        log(
            "aviso: Telegram no está configurado (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID). "
            "No se enviará nada."
        )

    seen = dedupe.load()
    log(f"dedupe: {len(seen)} ofertas ya vistas")

    all_jobs, errors = collect()
    new_jobs = dedupe.filter_new(all_jobs, seen)
    log(f"dedupe: {len(new_jobs)} ofertas nuevas de {len(all_jobs)}")

    linkedin_jobs = [j for j in new_jobs if j.source == "LinkedIn"]
    linkedin.hydrate(linkedin_jobs, limit=limit or config.LINKEDIN_DETAIL_LIMIT)

    relevant = filters.apply(new_jobs)
    log(f"filtros: {len(relevant)} ofertas pasan el filtro por reglas")

    to_score = relevant[: config.MAX_SCORE_JOBS]
    if len(relevant) > len(to_score):
        log(f"scorer: se puntúan las primeras {len(to_score)} de {len(relevant)}")
    to_score = score(to_score)

    any_scored = any(job.score is not None for job in to_score)
    if any_scored:
        selected = [
            job for job in to_score if job.score is None or job.score >= config.MIN_SCORE
        ]
    else:
        selected = list(to_score)  # sin IA: nos quedamos con todo lo que pasa reglas

    selected.sort(key=lambda j: (j.score if j.score is not None else 0), reverse=True)
    selected = selected[: config.MAX_DIGEST_ITEMS]

    if not new_jobs:
        detail = "no hay ofertas nuevas desde la última ejecución"
    elif not relevant:
        detail = "ninguna oferta nueva pasa el filtro por reglas"
    elif not selected and any_scored:
        detail = f"ninguna oferta supera MIN_SCORE ({config.MIN_SCORE})"
    else:
        detail = f"{len(selected)} ofertas para notificar"
    log(f"resultado: {detail}")

    if dry_run:
        print("\n===== DIGEST (dry-run) =====\n")
        print(telegram.render(selected))
        if errors and not selected:
            print("\n[aviso] Fuentes con error: " + "; ".join(errors))
        print("\n============================")
        return

    error_note = ""
    if errors and not selected:
        error_note = "Fuentes con error: " + "; ".join(errors)

    if telegram_ok:
        sent = telegram.send(selected, error_note)
        # Solo marcamos como vistas si hemos podido notificar, para no perder ofertas.
        if sent or not selected:
            dedupe.save(seen | {job.id for job in relevant})
        else:
            print("[aviso] no se pudo enviar; no se marcan ofertas como vistas")


def main() -> None:
    parser = argparse.ArgumentParser(description="Buscador de empleo automatizado")
    parser.add_argument("--dry-run", action="store_true", help="no envía ni guarda estado")
    parser.add_argument("--limit", type=int, default=None, help="máx. ofertas LinkedIn a detallar")
    parser.add_argument(
        "--test-telegram",
        action="store_true",
        help="comprueba la configuración de Telegram y envía un mensaje de prueba",
    )
    args = parser.parse_args()
    if args.test_telegram:
        telegram.test()
        return
    run(dry_run=args.dry_run, limit=args.limit)


if __name__ == "__main__":
    main()
