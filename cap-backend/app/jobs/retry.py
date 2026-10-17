import asyncio
import random
from collections.abc import Awaitable, Callable
from typing import TypeVar

from app.providers.errors import ProviderError, ProviderTimeout
from app.providers.throttle.clock import Sleeper

T = TypeVar("T")

RetryListener = Callable[[int, ProviderError, float], Awaitable[None]]


class RetryPolicy:
    def __init__(
        self,
        max_retries: int,
        base_delay_seconds: float,
        sleeper: Sleeper,
        generator: random.Random,
    ) -> None:
        self._max_retries = max_retries
        self._base_delay_seconds = base_delay_seconds
        self._sleeper = sleeper
        self._generator = generator

    async def run(
        self,
        operation: Callable[[], Awaitable[T]],
        timeout_seconds: float,
        on_retry: RetryListener,
    ) -> T:
        retries_done = 0
        while True:
            try:
                return await self._call_with_timeout(operation, timeout_seconds)
            except ProviderError as error:
                if not error.retryable or retries_done >= self._max_retries:
                    raise
                delay = self._delay_for(retries_done)
                retries_done += 1
                await on_retry(retries_done, error, delay)
                await self._sleeper.sleep(delay)

    async def _call_with_timeout(
        self, operation: Callable[[], Awaitable[T]], timeout_seconds: float
    ) -> T:
        try:
            return await asyncio.wait_for(operation(), timeout_seconds)
        except TimeoutError:
            raise ProviderTimeout(f"No answer within {timeout_seconds:g} s") from None

    def _delay_for(self, retries_done: int) -> float:
        backoff = self._base_delay_seconds * float(2**retries_done)
        jitter = float(self._generator.uniform(0, self._base_delay_seconds))
        return backoff + jitter
