import asyncio
from datetime import UTC, datetime

import pytest

from app.csv_import.models import ImportReport
from app.jobs.event_log import EventLog
from app.jobs.models import Job, PersonRun
from app.jobs.scheduler import FairScheduler
from tests.support.builders import make_person


def build_job(job_id: str, people: int, parallelism: int = 5) -> Job:
    runs = [
        PersonRun(index=index, line_number=index + 2, person=make_person(f"Name{index}", job_id))
        for index in range(people)
    ]
    return Job(
        id=job_id,
        created_at=datetime.now(UTC),
        parallelism=parallelism,
        report=ImportReport(),
        people=runs,
        event_log=EventLog(job_id),
    )


async def test_people_are_handed_out_round_robin_across_jobs() -> None:
    scheduler = FairScheduler()
    first, second = build_job("a", 3), build_job("b", 3)
    await scheduler.enqueue(first, first.people)
    await scheduler.enqueue(second, second.people)

    order = []
    for _ in range(6):
        task = await scheduler.next_task()
        assert task is not None
        order.append((task.job.id, task.run.index))

    assert order == [("a", 0), ("b", 0), ("a", 1), ("b", 1), ("a", 2), ("b", 2)]


async def test_a_job_never_exceeds_its_own_parallelism() -> None:
    scheduler = FairScheduler()
    job = build_job("a", 3, parallelism=1)
    await scheduler.enqueue(job, job.people)
    first = await scheduler.next_task()
    assert first is not None

    with pytest.raises(TimeoutError):
        await asyncio.wait_for(scheduler.next_task(), 0.05)

    await scheduler.task_done(first)
    second = await asyncio.wait_for(scheduler.next_task(), 1.0)
    assert second is not None and second.run.index == 1


async def test_a_busy_job_does_not_starve_another_one() -> None:
    scheduler = FairScheduler()
    busy, other = build_job("busy", 3, parallelism=1), build_job("other", 1)
    await scheduler.enqueue(busy, busy.people)
    await scheduler.enqueue(other, other.people)
    first = await scheduler.next_task()
    second = await scheduler.next_task()

    assert first is not None and second is not None
    assert {first.job.id, second.job.id} == {"busy", "other"}


async def test_cancelled_jobs_hand_out_nothing_more() -> None:
    scheduler = FairScheduler()
    job = build_job("a", 2)
    await scheduler.enqueue(job, job.people)
    job.cancel_requested = True

    with pytest.raises(TimeoutError):
        await asyncio.wait_for(scheduler.next_task(), 0.05)


async def test_requeued_people_come_back_first() -> None:
    scheduler = FairScheduler()
    job = build_job("a", 2)
    await scheduler.enqueue(job, job.people)
    task = await scheduler.next_task()
    assert task is not None

    await scheduler.requeue(task)
    await scheduler.task_done(task)
    again = await scheduler.next_task()

    assert again is not None and again.run.index == task.run.index


async def test_closing_releases_waiting_workers() -> None:
    scheduler = FairScheduler()
    waiter = asyncio.create_task(scheduler.next_task())
    await asyncio.sleep(0)

    await scheduler.close()

    assert await asyncio.wait_for(waiter, 1.0) is None


async def test_clear_queue_returns_the_people_that_were_waiting() -> None:
    scheduler = FairScheduler()
    job = build_job("a", 3)
    await scheduler.enqueue(job, job.people)
    await scheduler.next_task()

    removed = await scheduler.clear_queue(job)

    assert [run.index for run in removed] == [1, 2]
