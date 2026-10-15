import hashlib
import re
from dataclasses import dataclass, field


def normalize_url(url: str) -> str:
    """Quita query params/fragmentos y rastreadores para deduplicar."""
    url = url.split("#")[0].split("?")[0].strip()
    url = re.sub(r"/+$", "", url)
    m = re.search(r"linkedin\.com/jobs/view/(?:[^/?#]*?-)?(\d{9,})", url)
    if m:
        return f"linkedin:{m.group(1)}"
    m = re.search(r"jobPosting/(\d{6,})", url)
    if m:
        return f"linkedin:{m.group(1)}"
    return url.lower()


def make_id(source: str, url: str, title: str = "", company: str = "") -> str:
    base = normalize_url(url)
    if base.startswith("linkedin:") or base.startswith("http"):
        raw = base
    else:
        raw = f"{source}|{title.strip().lower()}|{company.strip().lower()}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


@dataclass
class Job:
    id: str
    source: str
    title: str
    company: str
    location: str
    url: str
    description: str = ""
    remote: str = ""  # "remoto" | "hibrido" | "presencial" | ""
    published_at: str = ""
    score: int | None = None
    stack: list[str] = field(default_factory=list)
    summary: str = ""
