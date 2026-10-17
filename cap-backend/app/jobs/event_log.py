import asyncio
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from app.jobs.events import EventType, JobEvent


def _utc_now() -> datetime:
    return datetime.now(UTC)


class EventLog:
    """Append-only per-job log; ids are 1, 2, 3… so a client resumes with the last id it saw."""

    def __init__(self, job_id: str, now: Callable[[], datetime] = _utc_now) -> None:
        self._job_id = job_id
        self._now = now
        self._events: list[JobEvent] = []
        self._waiters: list[asyncio.Future[None]] = []
        self._is_closed = False

    @property
    def is_closed(self) -> bool:
        return self._is_closed

    def append(
        self,
        event_type: EventType,
        message: str,
        data: dict[str, Any] | None = None,
        person_index: int | None = None,
        lane: int | None = None,
    ) -> JobEvent:
        event = JobEvent(
            id=len(self._events) + 1,
            type=event_type,
            job_id=self._job_id,
            timestamp=self._now(),
            message=message,
            person_index=person_index,
            lane=lane,
            data=data or {},
        )
        self._events.append(event)
        self._wake_waiters()
        return event

    def events_after(self, last_event_id: int) -> list[JobEvent]:
        return self._events[max(last_event_id, 0) :]

    def close(self) -> None:
        self._is_closed = True
        self._wake_waiters()

    def reopen(self) -> None:
        self._is_closed = False

    async def wait_for_more(self, last_event_id: int, timeout: float) -> bool:
        """Returns True when there is something new to read or the log was closed."""
        if self._has_news(last_event_id):
            return True
        waiter: asyncio.Future[None] = asyncio.get_running_loop().create_future()
        self._waiters.append(waiter)
        try:
            await asyncio.wait_for(waiter, timeout)
        except TimeoutError:
            return False
        finally:
            self._discard_waiter(waiter)
        return True

    def _has_news(self, last_event_id: int) -> bool:
        return len(self._events) > last_event_id or self._is_closed

    def _wake_waiters(self) -> None:
        for waiter in self._waiters:
            if not waiter.done():
                waiter.set_result(None)

    def _discard_waiter(self, waiter: asyncio.Future[None]) -> None:
        if waiter in self._waiters:
            self._waiters.remove(waiter)
