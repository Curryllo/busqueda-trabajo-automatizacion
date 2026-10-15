"""Envío del resumen (digest) por Telegram."""

import html
import os

import requests

BASE = "https://api.telegram.org/bot{token}/{method}"
MAX_LEN = 4000


def _e(text: str) -> str:
    return html.escape(text or "", quote=False)


def credentials() -> tuple[str, str]:
    return (
        os.environ.get("TELEGRAM_BOT_TOKEN", "").strip(),
        os.environ.get("TELEGRAM_CHAT_ID", "").strip(),
    )


def is_configured() -> bool:
    token, chat_id = credentials()
    return bool(token and chat_id)


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


def _describe(resp: requests.Response) -> str:
    try:
        data = resp.json()
    except ValueError:
        return f"HTTP {resp.status_code}: {resp.text[:200]}"
    if data.get("ok"):
        result = data.get("result", {})
        return f"ok (message_id={result.get('message_id')})"
    return f"HTTP {resp.status_code}: {data.get('description', resp.text[:200])}"


def send_message(text: str) -> bool:
    token, chat_id = credentials()
    if not token or not chat_id:
        print("[telegram] faltan TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID")
        return False
    resp = requests.post(
        BASE.format(token=token, method="sendMessage"),
        json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
        timeout=15,
    )
    ok = bool(resp.ok and resp.json().get("ok"))
    print(f"[telegram] respuesta: {_describe(resp)}")
    return ok


def send(jobs: list, error_note: str = "") -> bool:
    messages = _chunks(jobs) if jobs else []
    if error_note and not messages:
        messages = [f"⚠️ <b>Buscador de empleo</b>\n{_e(error_note)}"]
    if not messages:
        print("[telegram] sin ofertas nuevas, no se envía nada")
        return False
    sent_any = False
    for message in messages:
        sent_any = send_message(message) or sent_any
    return sent_any


def test() -> None:
    """Comprueba token, chat y envía un mensaje de prueba. Para depurar la configuración."""
    token, chat_id = credentials()
    if not token or not chat_id:
        print("[test] ERROR: define TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID")
        return

    print(f"[test] token detectado: ...{token[-6:]}  chat_id: {chat_id}")
    me = requests.get(BASE.format(token=token, method="getMe"), timeout=15)
    print(f"[test] getMe: {_describe(me)}")
    if not (me.ok and me.json().get("ok")):
        print("[test] El token no es válido. Revisa TELEGRAM_BOT_TOKEN.")
        return

    chat = requests.get(
        BASE.format(token=token, method="getChat"), params={"chat_id": chat_id}, timeout=15
    )
    print(f"[test] getChat: {_describe(chat)}")
    if not (chat.ok and chat.json().get("ok")):
        print(
            "[test] No se puede acceder al chat. Revisa TELEGRAM_CHAT_ID y envía /start al bot."
        )
        return

    ok = send_message(
        "✅ <b>Test del buscador de empleo</b>\n"
        "Si ves este mensaje, la conexión con Telegram funciona correctamente."
    )
    print("[test] RESULTADO:", "correcto" if ok else "fallido")


def render(jobs: list) -> str:
    """Devuelve el texto que se enviaría (para modo dry-run)."""
    return "\n\n---\n\n".join(_chunks(jobs)) if jobs else "(sin ofertas nuevas)"
