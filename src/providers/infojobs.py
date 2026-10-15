"""Ofertas de InfoJobs (España). Busca en el HTML y parsea el JSON embebido __INITIAL_PROPS__."""

import json
import re
from urllib.parse import urlencode

from .. import config
from ..models import Job, make_id
from .base import get, pause

SEARCH_URL = "https://www.infojobs.net/jobsearch/search-results/list.xhtml"
HOME_URL = "https://www.infojobs.net/"
CAPTCHA_RETRY_WAIT = 25

_warmed_up = False


def _warm_up() -> None:
    """Visita la portada una vez por ejecución para obtener cookies de sesión."""
    global _warmed_up
    if _warmed_up:
        return
    try:
        get(HOME_URL)
    except Exception:  # noqa: BLE001 - la portada es opcional
        pass
    _warmed_up = True


def _download(url: str) -> str:
    """Descarga una búsqueda; si sale captcha, espera y reintenta una vez."""
    _warm_up()
    html = get(url).text
    try:
        _extract_offers(html)
    except RuntimeError as exc:
        if "captcha" in str(exc):
            print(f"[InfoJobs] captcha detectado, reintento en {CAPTCHA_RETRY_WAIT}s")
            pause(CAPTCHA_RETRY_WAIT)
            html = get(url).text
    return html


def _extract_offers(html: str) -> list[dict]:
    m = re.search(r"window\.__INITIAL_PROPS__ = JSON\.parse\(\"(.+?)\"\);", html, re.DOTALL)
    if not m:
        if "captcha" in html.lower() or "challenge" in html.lower():
            raise RuntimeError("captcha de InfoJobs (rate limit), se omite esta fuente")
        raise RuntimeError("InfoJobs no devolvió resultados parseables")
    raw = m.group(1).encode("utf-8").decode("unicode_escape")
    data = json.loads(raw)
    return data.get("offers", []) or []


def _classify_remote(teleworking: str) -> str:
    t = (teleworking or "").lower()
    if "teletrabajo" in t and "solo" in t:
        return "remoto"
    if "híbrid" in t or "hibrid" in t:
        return "hibrido"
    if "presencial" in t:
        return "presencial"
    if "teletrabajo" in t:
        return "remoto"
    return ""


def fetch() -> list[Job]:
    jobs: list[Job] = []
    seen: set[str] = set()
    for i, query in enumerate(config.INFOJOBS_QUERIES):
        if i:
            pause(config.INFOJOBS_REQUEST_DELAY)
        params = {"sortBy": "PUBLICATION_DATE", **query}
        url = f"{SEARCH_URL}?{urlencode(params)}"
        html = _download(url)
        for offer in _extract_offers(html):
            link = (offer.get("link") or "").split("?")[0]
            if link.startswith("//"):
                link = "https:" + link
            title = (offer.get("title") or "").strip()
            company = (offer.get("companyName") or "").strip()
            if not title or not link:
                continue
            job_id = make_id("infojobs", link, title, company)
            if job_id in seen:
                continue
            seen.add(job_id)
            jobs.append(
                Job(
                    id=job_id,
                    source="InfoJobs",
                    title=title,
                    company=company,
                    location=(offer.get("city") or "").strip(),
                    url=link,
                    description=(offer.get("description") or "").strip()[: config.MAX_DESC_CHARS],
                    remote=_classify_remote(offer.get("teleworking") or ""),
                    published_at=(offer.get("publishedAt") or "").strip(),
                )
            )
    return jobs
