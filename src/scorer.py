"""Puntuación con IA: compara cada oferta contra tu perfil con Gemini (capa gratuita)."""

import json
import os
import re

from . import config
from .models import Job

# Se usan como respaldo si no se pueden listar los modelos disponibles.
# El orden importa: se prueban de arriba a abajo.
FALLBACK_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.5-flash",
    "gemini-3-flash",
    "gemini-2.5-flash",
]


def _version(name: str) -> tuple[int, int]:
    m = re.search(r"gemini-(\d+)(?:\.(\d+))?", name)
    if not m:
        return (0, 0)
    return (int(m.group(1)), int(m.group(2) or 0))


def _usable(name: str, allow_thinking: bool = False) -> bool:
    low = name.lower()
    if "flash" not in low:
        return False
    if any(x in low for x in ("image", "embedding", "tts", "live", "vision", "audio", "video")):
        return False
    if not allow_thinking and "thinking" in low:
        return False
    return True


def _discover_models(client) -> list[str]:
    """Pregunta a la API qué modelos aceptan generateContent y devuelve los flash más nuevos."""
    names: list[str] = []
    try:
        for m in client.models.list():
            raw = getattr(m, "name", "") or ""
            actions = getattr(m, "supported_actions", None)
            if actions is None:
                actions = getattr(m, "supported_generation_methods", None)
            if actions is not None and "generateContent" not in actions:
                continue
            if raw:
                names.append(raw.split("models/")[-1])
    except Exception as exc:  # noqa: BLE001 - si falla, usamos la lista fija
        print(f"[scorer] no se pudo listar modelos disponibles ({exc}); uso lista de respaldo")
        return []

    candidates = [n for n in names if _usable(n)]
    if not candidates:
        candidates = [n for n in names if _usable(n, allow_thinking=True)]
    candidates.sort(key=_version, reverse=True)
    return candidates


def _candidate_models(client) -> list[str]:
    preferred: list[str] = []
    env_model = os.environ.get("GEMINI_MODEL", "").strip().split("models/")[-1]
    if env_model:
        preferred.append(env_model)
    preferred += _discover_models(client)
    preferred += FALLBACK_MODELS
    unique = list(dict.fromkeys(m for m in preferred if m))
    print(f"[scorer] modelos candidatos: {', '.join(unique[:5])}")
    return unique

PROMPT = """Eres un asistente que ayuda a un candidato a filtrar ofertas de empleo.

PERFIL DEL CANDIDATO:
{profile}

PUNTÚA cada oferta de 1 a 10 según lo bien que encaja con el perfil (10 = encaje perfecto).
Reglas:
- Penaliza si exige más de 3 años de experiencia o seniority alto (nivel aceptable: junior/entrada/recién graduado).
- Valora positivamente puestos de desarrollador/software engineer/full stack.
- Ubicación válida: Zaragoza (presencial/híbrido) o remoto España/Europa.
- No importa el stack concreto.

OFERTAS:
{jobs}

Devuelve EXCLUSIVAMENTE un JSON (sin markdown) con esta forma:
[{{"index": <int>, "score": <int 1-10>, "stack": ["tech", ...], "summary": "<2 frases en español>"}}]
Incluye TODAS las ofertas, ordenadas con el mismo índice."""


def _job_block(index: int, job: Job) -> str:
    desc = job.description[:1500] if job.description else "(sin descripción)"
    return (
        f"#{index} TÍTULO: {job.title}\n"
        f"EMPRESA: {job.company}\n"
        f"UBICACIÓN: {job.location} {job.remote}\n"
        f"FUENTE: {job.source}\n"
        f"DESCRIPCIÓN: {desc}\n"
    )


def _clean_json(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    m = re.search(r"(\[.*\])", text, re.DOTALL)
    return m.group(1) if m else text


def _score_batch(client, types, model: str, jobs: list[Job]) -> dict[int, dict]:
    prompt = PROMPT.format(
        profile=config.PROFILE_TEXT.strip(),
        jobs="\n".join(_job_block(i, job) for i, job in enumerate(jobs)),
    )
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    parsed = json.loads(_clean_json(response.text))
    result: dict[int, dict] = {}
    for item in parsed:
        if isinstance(item, dict) and "index" in item:
            result[int(item["index"])] = item
    return result


def score(jobs: list[Job]) -> list[Job]:
    """Rellena score/stack/summary. Si no hay API key o falla, deja las ofertas sin puntuar."""
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("[scorer] GEMINI_API_KEY no configurada: se omite la puntuación con IA")
        return jobs
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print("[scorer] google-genai no instalado: se omite la puntuación con IA")
        return jobs

    client = genai.Client(api_key=api_key)
    models = _candidate_models(client)
    batch_size = 4
    model = models[0]

    for start in range(0, len(jobs), batch_size):
        batch = jobs[start : start + batch_size]
        scored = None
        last_error = None
        for candidate in models:
            try:
                scored = _score_batch(client, types, candidate, batch)
                model = candidate
                # El modelo que funciona pasa al frente para los siguientes lotes.
                models.remove(candidate)
                models.insert(0, candidate)
                break
            except Exception as exc:  # noqa: BLE001
                last_error = exc
        if scored is None:
            print(f"[scorer] error al puntuar lote ({last_error}); se dejan sin puntuar")
            continue
        for i, job in enumerate(batch):
            item = scored.get(i, {})
            try:
                job.score = int(item.get("score"))
            except (TypeError, ValueError):
                job.score = None
            stack = item.get("stack") or []
            job.stack = [str(s) for s in stack][:8] if isinstance(stack, list) else []
            job.summary = str(item.get("summary") or "").strip()

    print(f"[scorer] puntuadas {sum(1 for j in jobs if j.score is not None)}/{len(jobs)} ofertas con {model}")
    return jobs
