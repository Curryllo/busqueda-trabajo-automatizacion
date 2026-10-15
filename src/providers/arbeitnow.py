"""Ofertas remotas de Arbeitnow (API JSON gratuita)."""

import re

from .. import config
from ..models import Job, make_id
from .base import get_json

API_URL = "https://www.arbeitnow.com/api/job-board-api"

INCLUDE_LOCATION = re.compile(r"spain|españa|europe|europa|worldwide|anywhere|remote|global", re.I)
DEV_TITLE = re.compile(
    r"develop|engineer|programmer|full[\s\-]?stack|back[\s\-]?end|front[\s\-]?end|software|devops",
    re.I,
)
EXCLUDE_TITLE = re.compile(r"\bsenior\b|\blead\b|\bmanager\b|\brecruiter\b", re.I)


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def fetch() -> list[Job]:
    data = get_json(API_URL)
    jobs: list[Job] = []
    for item in data.get("data", []):
        if not item.get("remote"):
            continue
        title = (item.get("title") or "").strip()
        location = (item.get("location") or "").strip()
        if not DEV_TITLE.search(title) or EXCLUDE_TITLE.search(title):
            continue
        if location and not INCLUDE_LOCATION.search(location):
            continue
        url = item.get("url") or ""
        company = (item.get("company_name") or "").strip()
        if not url:
            continue
        jobs.append(
            Job(
                id=make_id("arbeitnow", url, title, company),
                source="Arbeitnow",
                title=title,
                company=company,
                location=location,
                url=url,
                description=_strip_html(item.get("description") or "")[: config.MAX_DESC_CHARS],
                remote="remoto",
                published_at=str(item.get("created_at") or ""),
            )
        )
    return jobs
