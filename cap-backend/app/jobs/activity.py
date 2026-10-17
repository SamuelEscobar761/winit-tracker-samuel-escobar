from contextvars import ContextVar
from dataclasses import dataclass

from app.jobs.event_log import EventLog
from app.jobs.events import EventType


@dataclass(frozen=True)
class Activity:
    log: EventLog
    person_index: int
    lane: int


current_activity: ContextVar[Activity | None] = ContextVar("current_activity", default=None)


class JobWaitObserver:
    """Turns the throttle's pauses into events of whichever person the worker is serving."""

    def waiting(self, seconds: float) -> None:
        activity = current_activity.get()
        if activity is None:
            return
        activity.log.append(
            EventType.WAITING,
            f"Waiting {seconds:g} s between portal actions",
            {"seconds": seconds},
            activity.person_index,
            activity.lane,
        )
