import hmac
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, SecretStr

from app.auth.dependencies import (
    SESSION_COOKIE,
    check_origin,
    get_login_limiter,
    get_session_store,
)
from app.auth.rate_limit import LoginRateLimiter
from app.auth.sessions import SessionStore
from app.config.settings import Settings

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    token: SecretStr


class SessionInfo(BaseModel):
    authentication_required: bool
    authenticated: bool


@router.post("/login", status_code=204, dependencies=[Depends(check_origin)])
def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    store: Annotated[SessionStore, Depends(get_session_store)],
    limiter: Annotated[LoginRateLimiter, Depends(get_login_limiter)],
) -> None:
    settings: Settings = request.app.state.settings
    client = request.client.host if request.client else "unknown"
    if limiter.is_blocked(client):
        raise HTTPException(status_code=429, detail="Too many attempts, try again later")
    if not _token_matches(body.token, settings):
        limiter.record_failure(client)
        raise HTTPException(status_code=401, detail="Invalid token")
    limiter.reset(client)
    response.set_cookie(
        SESSION_COOKIE,
        store.create(),
        max_age=int(settings.session_ttl_seconds),
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
        path="/",
    )


@router.post("/logout", status_code=204, dependencies=[Depends(check_origin)])
def logout(
    request: Request,
    response: Response,
    store: Annotated[SessionStore, Depends(get_session_store)],
) -> None:
    store.revoke(request.cookies.get(SESSION_COOKIE))
    response.delete_cookie(SESSION_COOKIE, path="/")


@router.get("/session")
def read_session(
    request: Request, store: Annotated[SessionStore, Depends(get_session_store)]
) -> SessionInfo:
    settings: Settings = request.app.state.settings
    authenticated = store.is_valid(request.cookies.get(SESSION_COOKIE))
    return SessionInfo(authentication_required=settings.is_live, authenticated=authenticated)


def _token_matches(provided: SecretStr, settings: Settings) -> bool:
    if not settings.has_admin_token or settings.admin_token is None:
        return False
    expected = settings.admin_token.get_secret_value().encode("utf-8")
    return hmac.compare_digest(provided.get_secret_value().encode("utf-8"), expected)
