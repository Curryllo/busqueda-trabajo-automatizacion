"""Ofertas de LinkedIn vía la API pública 'jobs-guest' (sin login)."""

import re
from html import unescape

from .. import config
from ..models import Job, make_id
from .base import get, pause

SEARCH_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
DETAIL_URL = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"


def _strip_tags(html: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", html)
    text = re.sub(r"</p>|</li>|</div>", "\n", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    return re.sub(r"[ \t]+", " ", re.sub(r"\n\s*\n+", "\n", text)).strip()


def _search_page(keywords: str, location: str, remote: bool, start: int = 0) -> list[Job]:
    params = {
        "keywords": keywords,
        "location": location,
        "f_TPR": "r604800",  # últimas 24h → r86400; 7 días → r604800
        "start": start,
    }
    if remote:
        params["f_WT"] = "4"  # teletrabajo
    html = get(SEARCH_URL, params=params).text

    jobs: list[Job] = []
    cards = re.split(r'data-entity-urn="urn:li:jobPosting:', html)[1:]
    for card in cards:
        job_id = card.split('"', 1)[0].strip()
        if not job_id.isdigit():
            continue

        def grab(pattern: str) -> str:
            m = re.search(pattern, card, re.DOTALL)
            return _strip_tags(m.group(1)) if m else ""

        title = grab(r'<h3 class="base-search-card__title">(.*?)</h3>')
        company = grab(r'<h4 class="base-search-card__subtitle">(.*?)</h4>')
        location = grab(r'<span class="job-search-card__location">(.*?)</span>')
        link_m = re.search(r'href="([^"]+)"', card)
        link = link_m.group(1).split("?")[0] if link_m else f"https://www.linkedin.com/jobs/view/{job_id}"
        if not title:
            continue
        jobs.append(
            Job(
                id=make_id("linkedin", link, title, company),
                source="LinkedIn",
                title=title,
                company=company,
                location=location,
                url=link,
                remote="remoto" if remote else "",
            )
        )
    return jobs


def _fetch_detail(job: Job) -> None:
    m = re.search(r"(\d{9,})", job.url)
    if not m:
        return
    html = get(DETAIL_URL.format(job_id=m.group(1))).text
    dm = re.search(
        r'class="description__text[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL
    )
    if dm:
        job.description = _strip_tags(dm.group(1))[: config.MAX_DESC_CHARS]
    cm = re.search(r'<code>(.*?)</code>', html, re.DOTALL)
    if cm and not job.company:
        job.company = _strip_tags(cm.group(1))


def fetch() -> list[Job]:
    """Devuelve ofertas de las consultas configuradas (1 página por consulta)."""
    jobs: list[Job] = []
    seen_urls: set[str] = set()
    for keywords, location, remote in config.LINKEDIN_QUERIES:
        found = _search_page(keywords, location, remote)
        for job in found:
            if job.url in seen_urls:
                continue
            seen_urls.add(job.url)
            jobs.append(job)
        pause(1.5)
    return jobs


def hydrate(jobs: list[Job], limit: int = 25) -> None:
    """Descarga la descripción completa (necesaria para el filtro y la IA)."""
    for job in jobs[:limit]:
        try:
            _fetch_detail(job)
            pause(1.0)
        except Exception:  # noqa: BLE001 - sin descripción seguimos adelante
            continue
