import asyncio
import time
from typing import Protocol


class Clock(Protocol):
    def monotonic(self) -> float: ...


class Sleeper(Protocol):
    async def sleep(self, seconds: float) -> None: ...


class SystemClock:
    def monotonic(self) -> float:
        return time.monotonic()


class AsyncioSleeper:
    async def sleep(self, seconds: float) -> None:
        await asyncio.sleep(seconds)


class ScaledSleeper:
    """Shortens every wait by a constant factor so demos run faster than the real portal."""

    def __init__(self, inner: Sleeper, speed_factor: float) -> None:
        self._inner = inner
        self._speed_factor = speed_factor

    async def sleep(self, seconds: float) -> None:
        await self._inner.sleep(seconds / self._speed_factor)
