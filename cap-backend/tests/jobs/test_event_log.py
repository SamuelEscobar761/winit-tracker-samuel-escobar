import asyncio

from app.api.sse import HEARTBEAT_FRAME, format_sse, parse_last_event_id, stream_events
from app.jobs.event_log import EventLog
from app.jobs.events import EventType


def build_log() -> EventLog:
    return EventLog("job-1")


def test_event_ids_are_monotonic_starting_at_one() -> None:
    log = build_log()

    ids = [log.append(EventType.SEARCHING, "a").id for _ in range(3)]

    assert ids == [1, 2, 3]


def test_events_after_returns_only_what_the_client_missed() -> None:
    log = build_log()
    for _ in range(4):
        log.append(EventType.SEARCHING, "a")

    assert [event.id for event in log.events_after(2)] == [3, 4]
    assert log.events_after(4) == []
    assert len(log.events_after(0)) == 4
    assert len(log.events_after(-5)) == 4


async def test_waiting_returns_as_soon_as_an_event_is_appended() -> None:
    log = build_log()
    waiter = asyncio.create_task(log.wait_for_more(0, 5.0))
    await asyncio.sleep(0)

    log.append(EventType.FOUND, "found")

    assert await waiter is True


async def test_waiting_times_out_without_news() -> None:
    assert await build_log().wait_for_more(0, 0.01) is False


async def test_waiting_returns_when_the_log_is_closed() -> None:
    log = build_log()
    waiter = asyncio.create_task(log.wait_for_more(0, 5.0))
    await asyncio.sleep(0)

    log.close()

    assert await waiter is True


async def test_reopened_log_waits_again() -> None:
    log = build_log()
    log.close()
    log.reopen()

    assert await log.wait_for_more(0, 0.01) is False


def test_sse_frame_has_id_event_and_json_data() -> None:
    event = build_log().append(EventType.JOB_COMPLETE, "Job complete", {"total": 2})

    frame = format_sse(event)

    assert frame.startswith("id: 1\nevent: job_complete\ndata: {")
    assert frame.endswith("\n\n")
    assert '"total":2' in frame


def test_last_event_id_header_is_parsed_defensively() -> None:
    assert parse_last_event_id("7") == 7
    assert parse_last_event_id(None) == 0
    assert parse_last_event_id("abc") == 0
    assert parse_last_event_id("-3") == 0


async def collect(log: EventLog, last_event_id: int) -> list[str]:
    return [frame async for frame in stream_events(log, last_event_id, 0.01)]


async def test_stream_replays_missed_events_and_ends_when_the_log_is_closed() -> None:
    log = build_log()
    for _ in range(3):
        log.append(EventType.SEARCHING, "a")
    log.close()

    frames = await collect(log, 1)

    assert [frame.split("\n")[0] for frame in frames] == ["id: 2", "id: 3"]


async def test_stream_sends_heartbeats_while_the_job_is_quiet() -> None:
    log = build_log()
    frames: list[str] = []

    async def read() -> None:
        async for frame in stream_events(log, 0, 0.01):
            frames.append(frame)

    reader = asyncio.create_task(read())
    await asyncio.sleep(0.08)
    log.append(EventType.JOB_COMPLETE, "done")
    log.close()
    await asyncio.wait_for(reader, 2.0)

    assert HEARTBEAT_FRAME in frames
    assert frames[-1].startswith("id: 1")


async def test_stream_follows_new_events_live() -> None:
    log = build_log()
    reader = asyncio.create_task(collect(log, 0))
    await asyncio.sleep(0)

    log.append(EventType.SEARCHING, "a")
    log.append(EventType.FOUND, "b")
    log.close()

    frames = await asyncio.wait_for(reader, 2.0)
    assert [frame for frame in frames if frame != HEARTBEAT_FRAME][-1].startswith("id: 2")
