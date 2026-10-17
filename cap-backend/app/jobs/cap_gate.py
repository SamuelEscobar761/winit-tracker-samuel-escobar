import asyncio
import contextlib
from collections.abc import Awaitable, Callable
from typing import Protocol

from app.providers.errors import ProviderError
from app.providers.throttle.clock import Sleeper


class CapStatusAnnouncer(Protocol):
    def announce_cap_down(self, message: str) -> None: ...

    def announce_cap_recovered(self) -> None: ...


class CapGate:
    """Stops every worker while the portal is down so people are not failed one by one."""

    def __init__(
        self,
        check_health: Callable[[], Awaitable[None]],
        recheck_seconds: float,
        sleeper: Sleeper,
        announcer: CapStatusAnnouncer,
    ) -> None:
        self._check_health = check_health
        self._recheck_seconds = recheck_seconds
        self._sleeper = sleeper
        self._announcer = announcer
        self._open = asyncio.Event()
        self._open.set()
        self._recovery_task: asyncio.Task[None] | None = None

    @property
    def is_open(self) -> bool:
        return self._open.is_set()

    async def wait_until_open(self) -> None:
        await self._open.wait()

    def report_down(self, message: str) -> None:
        if not self._open.is_set():
            return
        self._open.clear()
        self._announcer.announce_cap_down(message)
        self._recovery_task = asyncio.create_task(self._recover())

    async def aclose(self) -> None:
        if self._recovery_task is None:
            return
        self._recovery_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self._recovery_task

    async def _recover(self) -> None:
        while not await self._is_portal_healthy():
            await self._sleeper.sleep(self._recheck_seconds)
        self._open.set()
        self._announcer.announce_cap_recovered()

    async def _is_portal_healthy(self) -> bool:
        try:
            await self._check_health()
        except ProviderError:
            return False
        return True
