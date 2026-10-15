"""Envío del resumen (digest) por Telegram."""

import html
import os

import requests

API = "https://api.telegram.org/bot{token}/sendMessage"
MAX_LEN = 4000


def _e(text: str) -> str:
    return html.escape(text or "", quote=False)


def _location_label(job) -> str:
    labels = {"remoto": "100% Remoto", "hibrido": "Híbrido", "zaragoza": "Zaragoza"}
    loc = labels.get(job.remote, job.location or "España")
    if job.remote == "zaragoza" and job.location:
        loc = job.location
    return loc


def _format_job(job) -> str:
    score = f" · {job.score}/10" if job.score is not None else ""
    lines = [f"🚀 <b>{_e(job.title)}</b>{score}"]
    parts = []
    if job.company:
        parts.append(f"🏢 {_e(job.company)}")
    parts.append(f"📍 {_e(_location_label(job))}")
    lines.append(" · ".join(parts))
    if job.stack:
        lines.append(f"🛠 {_e(', '.join(job.stack))}")
    if job.summary:
        lines.append(f"💡 {_e(job.summary)}")
    lines.append(f'🔗 <a href="{_e(job.url)}">Ver oferta</a> ({_e(job.source)})')
    return "\n".join(lines)


def _chunks(jobs: list) -> list[str]:
    messages: list[str] = []
    current = "🆕 <b>Nuevas ofertas para ti</b>\n"
    for job in jobs:
        block = "\n\n" + _format_job(job)
        if len(current) + len(block) > MAX_LEN:
            messages.append(current)
            current = "🆕 <b>Nuevas ofertas para ti (cont.)</b>\n"
        current += block
    if current.strip():
        messages.append(current)
    return messages


def send(jobs: list, error_note: str = "") -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        print("[telegram] faltan TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID")
        return

    messages = _chunks(jobs) if jobs else []
    if error_note and not messages:
        messages = [f"⚠️ <b>Buscador de empleo</b>\n{_e(error_note)}"]
    if not messages:
        print("[telegram] sin ofertas nuevas, no se envía nada")
        return

    for message in messages:
        resp = requests.post(
            API.format(token=token),
            json={"chat_id": chat_id, "text": message, "parse_mode": "HTML", "disable_web_page_preview": True},
            timeout=15,
        )
        if not resp.ok:
            print(f"[telegram] error {resp.status_code}: {resp.text[:200]}")
        else:
            print("[telegram] mensaje enviado")


def render(jobs: list) -> str:
    """Devuelve el texto que se enviaría (para modo dry-run)."""
    return "\n\n---\n\n".join(_chunks(jobs)) if jobs else "(sin ofertas nuevas)"
