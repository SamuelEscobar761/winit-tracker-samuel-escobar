from fastapi import HTTPException, Request, WebSocket

from app.auth.rate_limit import LoginRateLimiter
from app.auth.sessions import SessionStore
from app.config.settings import Settings

SESSION_COOKIE = "session"
STATE_CHANGING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


def get_session_store(request: Request) -> SessionStore:
    store: SessionStore = request.app.state.session_store
    return store


def get_login_limiter(request: Request) -> LoginRateLimiter:
    limiter: LoginRateLimiter = request.app.state.login_limiter
    return limiter


def require_session(request: Request) -> None:
    settings: Settings = request.app.state.settings
    if not settings.is_live:
        return
    store = get_session_store(request)
    if not store.is_valid(request.cookies.get(SESSION_COOKIE)):
        raise HTTPException(status_code=401, detail="Authentication required")


def check_origin(request: Request) -> None:
    """Browsers always send Origin on state-changing requests, so a foreign one is refused."""
    if request.method not in STATE_CHANGING_METHODS:
        return
    settings: Settings = request.app.state.settings
    origin = request.headers.get("origin")
    if origin is not None and not _is_allowed(origin, settings, request.headers.get("host")):
        raise HTTPException(status_code=403, detail="Origin not allowed")


def authorize_websocket(websocket: WebSocket) -> bool:
    settings: Settings = websocket.app.state.settings
    origin = websocket.headers.get("origin")
    if origin is not None and not _is_allowed(origin, settings, websocket.headers.get("host")):
        return False
    if not settings.is_live:
        return True
    store: SessionStore = websocket.app.state.session_store
    return origin is not None and store.is_valid(websocket.cookies.get(SESSION_COOKIE))


def _is_allowed(origin: str, settings: Settings, host: str | None) -> bool:
    if origin in settings.cors_origins:
        return True
    return host is not None and origin in (f"http://{host}", f"https://{host}")
