"""Memoria de ofertas ya vistas, persistida en data/seen_jobs.json (se versiona en git)."""

import json
from pathlib import Path

from .models import Job

SEEN_FILE = Path(__file__).resolve().parent.parent / "data" / "seen_jobs.json"
MAX_HISTORY = 5000


def load() -> set[str]:
    if not SEEN_FILE.exists():
        return set()
    try:
        data = json.loads(SEEN_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return set()
    if isinstance(data, list):
        return set(str(x) for x in data)
    return set(str(x) for x in data.get("seen", []))


def save(seen_ids: set[str]) -> None:
    ids = list(seen_ids)[-MAX_HISTORY:]
    SEEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    SEEN_FILE.write_text(
        json.dumps({"seen": ids}, ensure_ascii=False, indent=0),
        encoding="utf-8",
    )


def filter_new(jobs: list[Job], seen: set[str]) -> list[Job]:
    return [job for job in jobs if job.id not in seen]
