# Buscador de empleo automatizado

Bot que busca ofertas de **Full Stack / Software Engineer** para un perfil junior
recién graduado en **Zaragoza** (presencial/híbrido) o **100% remoto** (España/Europa),
las filtra, las puntúa con IA y te envía un resumen por **Telegram**.

Corre íntegramente en **GitHub Actions** (gratis): no necesitas tener el ordenador
encendido ni un servidor propio.

## Cómo funciona

```
GitHub Actions (07:00, 12:00, 17:00 UTC, L-V)
  1. Recoge ofertas: LinkedIn, InfoJobs, Remotive, Arbeitnow
  2. Descarta las ya vistas (data/seen_jobs.json)
  3. Filtra por reglas: rol de desarrollo, no senior, ubicación válida
  4. Puntúa cada oferta con Gemini (1-10) y resume el stack
  5. Envía un mensaje digest a Telegram con las mejores (score >= 6)
  6. Guarda las ofertas vistas de vuelta en el repo (deduplicación)
```

## Configuración (una sola vez)

### 1. Crear el bot de Telegram
1. Abre Telegram y habla con **@BotFather** → `/newbot` → guarda el **token**.
2. Habla con **@userinfobot** → copia tu **chat id**.
3. Envía cualquier mensaje a tu nuevo bot para que pueda escribirte.

### 2. API key de Gemini (gratis)
1. Entra en https://aistudio.google.com/apikey
2. Crea una API key y cópiala.

### 3. Secretos en GitHub
En el repositorio → **Settings → Secrets and variables → Actions → New repository secret**:

| Secreto | Valor |
| --- | --- |
| `TELEGRAM_BOT_TOKEN` | token de BotFather |
| `TELEGRAM_CHAT_ID` | tu chat id |
| `GEMINI_API_KEY` | API key de Google AI Studio |

### 4. Activar
Push a `main` o ejecuta el workflow a mano desde **Actions → Job alerts → Run workflow**.

## Personalizar

Toda la configuración está en [`src/config.py`](src/config.py):

- `PROFILE_TEXT`: descripción de tu perfil que usa la IA.
- `INCLUDE_ROLE_PATTERNS` / `EXCLUDE_TITLE_PATTERNS`: qué puestos entran o se descartan.
- `MIN_SCORE`: nota mínima (1-10) para notificar.
- `MAX_DIGEST_ITEMS`: nº máximo de ofertas por mensaje.
- `LINKEDIN_QUERIES` / `INFOJOBS_QUERIES`: búsquedas realizadas.

## Probar en local

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Muestra el digest sin enviar nada ni guardar estado
GEMINI_API_KEY="tu_key" .venv/bin/python -m src.main --dry-run
```

Sin `GEMINI_API_KEY` funciona igual, pero sin puntuación (solo filtro por reglas).

## Notas

- **InfoJobs** puede responder con captcha si se hacen muchas peticiones seguidas.
  El bot espera entre peticiones y, si falla, simplemente usa las demás fuentes.
- Si Gemini falla o agota cuota, se envían las ofertas que pasan el filtro por reglas.
- `data/seen_jobs.json` lo actualiza el propio workflow en cada ejecución para no
  repetir ofertas.
