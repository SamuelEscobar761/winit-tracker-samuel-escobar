import secrets

from app.providers.throttle.clock import Clock


class SessionStore:
    """Random session ids kept in memory; the id is the only thing the browser holds."""

    def __init__(self, ttl_seconds: float, clock: Clock) -> None:
        self._ttl_seconds = ttl_seconds
        self._clock = clock
        self._expires_at: dict[str, float] = {}

    def create(self) -> str:
        session_id = secrets.token_urlsafe(32)
        self._expires_at[session_id] = self._clock.monotonic() + self._ttl_seconds
        return session_id

    def is_valid(self, session_id: str | None) -> bool:
        if session_id is None or session_id not in self._expires_at:
            return False
        if self._expires_at[session_id] <= self._clock.monotonic():
            del self._expires_at[session_id]
            return False
        return True

    def revoke(self, session_id: str | None) -> None:
        if session_id is not None:
            self._expires_at.pop(session_id, None)
