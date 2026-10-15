import time

import requests

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
)

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


def get(
    url: str,
    params: dict | None = None,
    timeout: int = 15,
    retries: int = 2,
    session: requests.Session | None = None,
) -> requests.Response:
    http = session or SESSION
    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            resp = http.get(url, params=params, timeout=timeout)
            resp.raise_for_status()
            return resp
        except Exception as exc:  # noqa: BLE001 - reintentamos ante errores transitorios
            last_exc = exc
            if attempt < retries:
                time.sleep(2 * (attempt + 1))
    raise last_exc  # type: ignore[misc]


def get_json(url: str, params: dict | None = None, timeout: int = 15) -> dict:
    return get(url, params=params, timeout=timeout).json()


def pause(seconds: float) -> None:
    time.sleep(seconds)
