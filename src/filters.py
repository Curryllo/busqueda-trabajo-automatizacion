"""Filtro por reglas: descarta puestos no técnicos, demasiado senior o fuera de zona."""

import re

from . import config
from .models import Job

_include = [re.compile(p, re.I) for p in config.INCLUDE_ROLE_PATTERNS]
_exclude_title = [re.compile(p, re.I) for p in config.EXCLUDE_TITLE_PATTERNS]
_exclude_desc = [re.compile(p, re.I) for p in config.EXCLUDE_DESC_PATTERNS]
_remote_hint = [re.compile(p, re.I) for p in config.REMOTE_HINT_PATTERNS]
_zaragoza = re.compile(config.ZARAGOZA_HINT, re.I)


def _matches_any(patterns, text: str) -> bool:
    return any(p.search(text) for p in patterns)


def classify_location(job: Job) -> str | None:
    """Devuelve 'remoto', 'hibrido' o 'zaragoza' si encaja; None si no."""
    location = f"{job.location} {job.remote}"
    if job.remote in ("remoto", "hibrido"):
        return job.remote
    if _zaragoza.search(job.location):
        return "zaragoza"
    if _matches_any(_remote_hint, location):
        return "remoto"
    if job.source in ("Remotive", "Arbeitnow"):
        return "remoto"
    return None


def is_relevant(job: Job) -> bool:
    text_title = job.title
    text_full = f"{job.title}\n{job.description}"

    if not _matches_any(_include, text_full):
        return False
    if _matches_any(_exclude_title, text_title):
        return False
    if job.description and _matches_any(_exclude_desc, job.description):
        return False
    return classify_location(job) is not None


def apply(jobs: list[Job]) -> list[Job]:
    return [job for job in jobs if is_relevant(job)]
