from collections import defaultdict, deque

from app.providers.throttle.clock import Clock

WINDOW_SECONDS = 60.0


class LoginRateLimiter:
    def __init__(self, max_failures: int, clock: Clock) -> None:
        self._max_failures = max_failures
        self._clock = clock
        self._failures: defaultdict[str, deque[float]] = defaultdict(deque)

    def is_blocked(self, client: str) -> bool:
        self._drop_old(client)
        return len(self._failures[client]) >= self._max_failures

    def record_failure(self, client: str) -> None:
        self._failures[client].append(self._clock.monotonic())

    def reset(self, client: str) -> None:
        self._failures.pop(client, None)

    def _drop_old(self, client: str) -> None:
        failures = self._failures[client]
        now = self._clock.monotonic()
        while failures and now - failures[0] >= WINDOW_SECONDS:
            failures.popleft()
