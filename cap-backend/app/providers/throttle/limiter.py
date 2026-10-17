import asyncio
from collections import deque

from app.providers.throttle.clock import Clock, Sleeper


class SlidingWindowLimiter:
    def __init__(
        self, max_actions: int, window_seconds: float, clock: Clock, sleeper: Sleeper
    ) -> None:
        self._max_actions = max_actions
        self._window_seconds = window_seconds
        self._clock = clock
        self._sleeper = sleeper
        self._timestamps: deque[float] = deque()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            await self._wait_for_free_slot()
            self._timestamps.append(self._clock.monotonic())

    async def _wait_for_free_slot(self) -> None:
        while True:
            self._drop_expired_timestamps()
            if len(self._timestamps) < self._max_actions:
                return
            await self._sleeper.sleep(self._seconds_until_oldest_expires())

    def _drop_expired_timestamps(self) -> None:
        now = self._clock.monotonic()
        while self._timestamps and now - self._timestamps[0] >= self._window_seconds:
            self._timestamps.popleft()

    def _seconds_until_oldest_expires(self) -> float:
        remaining = self._timestamps[0] + self._window_seconds - self._clock.monotonic()
        return max(remaining, 0.0)
