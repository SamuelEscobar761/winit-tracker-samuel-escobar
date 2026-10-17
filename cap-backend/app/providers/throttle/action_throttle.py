from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager

from app.providers.throttle.clock import Sleeper
from app.providers.throttle.limiter import SlidingWindowLimiter
from app.providers.throttle.observer import WaitObserver


class ActionThrottle:
    def __init__(
        self,
        delay_seconds: float,
        limiters: Sequence[SlidingWindowLimiter],
        sleeper: Sleeper,
        observer: WaitObserver | None = None,
    ) -> None:
        self._delay_seconds = delay_seconds
        self._limiters = tuple(limiters)
        self._sleeper = sleeper
        self._observer = observer

    @asynccontextmanager
    async def action(self) -> AsyncIterator[None]:
        """The wait after the action also applies when the action fails."""
        for limiter in self._limiters:
            await limiter.acquire()
        try:
            yield
        finally:
            if self._observer is not None:
                self._observer.waiting(self._delay_seconds)
            await self._sleeper.sleep(self._delay_seconds)
