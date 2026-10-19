# Buscador de empleo automatizado

Bot que busca ofertas de **Full Stack / Software Engineer** para un perfil junior
recién graduado en **Zaragoza** (presencial/híbrido) o **100% remoto** (España/Europa),
las filtra, las puntúa con IA y te envía un resumen por **Telegram**.

Corre íntegramente en **GitHub Actions** (gratis): no necesitas tener el ordenador
encendido ni un servidor propio.

## Cómo funciona

```
GitHub Actions (07:17, 12:17, 17:17 UTC, L-V)
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

## Comprobar que Telegram funciona

Antes de esperar ofertas, verifica la conexión:

- **Desde GitHub:** Actions → Job alerts → *Run workflow* → marca **test_telegram** → Run.
  Deberías recibir un mensaje de prueba y en el log ver `[test] RESULTADO: correcto`.
- **En local:** `TELEGRAM_BOT_TOKEN=... TELEGRAM_CHAT_ID=... python -m src.main --test-telegram`

## Si la ejecución termina bien pero no recibes nada

El log del workflow (Actions → Job alerts → última ejecución → paso "Buscar ofertas y notificar")
indica el motivo. Casos típicos:

- `[aviso] Telegram no está configurado`: nombres de secretos mal escritos o sin crear.
- `[test] token detectado` no aparece: el workflow no ve los secretos (revisa Settings → Secrets).
- `[telegram] respuesta: HTTP 400: chat not found`: `TELEGRAM_CHAT_ID` incorrecto, o no has
  enviado `/start` al bot.
- `[dedupe] 0 ofertas nuevas`: no hay ofertas nuevas desde la última ejecución (normal).
- `[resultado] ninguna oferta nueva pasa el filtro por reglas` / `ninguna oferta supera MIN_SCORE`:
  baja `MIN_SCORE` o amplía `LINKEDIN_QUERIES`/`INFOJOBS_QUERIES` en `src/config.py`.

> Nota: si una ejecución no logra enviar por Telegram, **no** marca las ofertas como vistas,
> así que se reintentan en la siguiente ejecución.

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

### Modelos de Gemini

El código detecta automáticamente los modelos disponibles (`generateContent`) y elige el
**flash** más reciente, así que no hay que actualizar nombres cuando Google retira versiones.
Si quieres forzar uno concreto, define la variable de entorno `GEMINI_MODEL` (p. ej.
`gemini-3.8-flash`); si falla, cae al resto de candidatos y, en último caso, al filtro por reglas.

## Notas

- **InfoJobs** puede responder con captcha si se hacen muchas peticiones seguidas.
  El bot espera entre peticiones y, si falla, simplemente usa las demás fuentes.
- Si Gemini falla o agota cuota, se envían las ofertas que pasan el filtro por reglas.
- `data/seen_jobs.json` lo actualiza el propio workflow en cada ejecución para no
  repetir ofertas.
