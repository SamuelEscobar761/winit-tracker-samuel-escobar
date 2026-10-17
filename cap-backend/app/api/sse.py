from collections.abc import AsyncIterator

from app.jobs.event_log import EventLog
from app.jobs.events import JobEvent

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}
HEARTBEAT_FRAME = ": heartbeat\n\n"


def format_sse(event: JobEvent) -> str:
    return f"id: {event.id}\nevent: {event.type.value}\ndata: {event.model_dump_json()}\n\n"


def parse_last_event_id(raw_value: str | None) -> int:
    try:
        return max(int(raw_value), 0) if raw_value is not None else 0
    except ValueError:
        return 0


async def stream_events(
    log: EventLog, last_event_id: int, heartbeat_seconds: float
) -> AsyncIterator[str]:
    """Replays what the client missed, then follows the log until the job is closed."""
    cursor = last_event_id
    while True:
        for event in log.events_after(cursor):
            cursor = event.id
            yield format_sse(event)
        if log.is_closed and not log.events_after(cursor):
            return
        if not await log.wait_for_more(cursor, heartbeat_seconds):
            yield HEARTBEAT_FRAME
