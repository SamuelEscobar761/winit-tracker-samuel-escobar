import asyncio
from collections import deque
from dataclasses import dataclass

from app.jobs.models import Job, PersonRun


@dataclass(frozen=True)
class PersonTask:
    job: Job
    run: PersonRun


class FairScheduler:
    """Hands out people round-robin across jobs, never exceeding a job's own parallelism."""

    def __init__(self) -> None:
        self._jobs: list[Job] = []
        self._queues: dict[str, deque[PersonRun]] = {}
        self._cursor = 0
        self._changed = asyncio.Condition()
        self._is_closed = False

    async def enqueue(self, job: Job, runs: list[PersonRun]) -> None:
        async with self._changed:
            if job.id not in self._queues:
                self._jobs.append(job)
                self._queues[job.id] = deque()
            self._queues[job.id].extend(runs)
            self._changed.notify_all()

    async def requeue(self, task: PersonTask) -> None:
        async with self._changed:
            self._queues[task.job.id].appendleft(task.run)
            self._changed.notify_all()

    async def next_task(self) -> PersonTask | None:
        async with self._changed:
            while not self._is_closed:
                task = self._pick_next()
                if task is not None:
                    return task
                await self._changed.wait()
            return None

    async def task_done(self, task: PersonTask) -> None:
        async with self._changed:
            task.job.running_count -= 1
            self._changed.notify_all()

    async def clear_queue(self, job: Job) -> list[PersonRun]:
        async with self._changed:
            queue = self._queues.get(job.id)
            removed = list(queue) if queue else []
            if queue is not None:
                queue.clear()
            self._changed.notify_all()
            return removed

    async def close(self) -> None:
        async with self._changed:
            self._is_closed = True
            self._changed.notify_all()

    def _pick_next(self) -> PersonTask | None:
        for offset in range(len(self._jobs)):
            position = (self._cursor + offset) % len(self._jobs)
            task = self._take_from(self._jobs[position])
            if task is not None:
                self._cursor = position + 1
                return task
        return None

    def _take_from(self, job: Job) -> PersonTask | None:
        queue = self._queues[job.id]
        if not queue or job.cancel_requested or job.running_count >= job.parallelism:
            return None
        job.running_count += 1
        return PersonTask(job, queue.popleft())
