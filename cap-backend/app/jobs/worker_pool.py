import asyncio
import contextlib
import logging
from collections.abc import Callable

from app.jobs.cap_gate import CapGate
from app.jobs.lifecycle import JobLifecycle
from app.jobs.person_processor import PersonProcessor
from app.jobs.scheduler import FairScheduler, PersonTask
from app.live.lanes import LaneRegistry
from app.providers.base import CapProvider
from app.providers.errors import CapDown

logger = logging.getLogger(__name__)

ProviderFactory = Callable[[int], CapProvider]


class WorkerPool:
    """One long-lived worker (one provider session) per lane, shared by every job."""

    def __init__(
        self,
        size: int,
        scheduler: FairScheduler,
        processor: PersonProcessor,
        lifecycle: JobLifecycle,
        cap_gate: CapGate,
        provider_factory: ProviderFactory,
        registry: LaneRegistry | None = None,
    ) -> None:
        self._size = size
        self._scheduler = scheduler
        self._processor = processor
        self._lifecycle = lifecycle
        self._cap_gate = cap_gate
        self._provider_factory = provider_factory
        self._registry = registry
        self._tasks: list[asyncio.Task[None]] = []

    def start(self) -> None:
        self._tasks = [asyncio.create_task(self._run_lane(lane)) for lane in range(self._size)]

    async def stop(self) -> None:
        await self._scheduler.close()
        for task in self._tasks:
            task.cancel()
        for task in self._tasks:
            with contextlib.suppress(asyncio.CancelledError):
                await task
        await self._cap_gate.aclose()

    async def _run_lane(self, lane: int) -> None:
        provider = self._provider_factory(lane)
        try:
            await self._serve(lane, provider)
        finally:
            await provider.aclose()

    async def _serve(self, lane: int, provider: CapProvider) -> None:
        while True:
            await self._cap_gate.wait_until_open()
            task = await self._scheduler.next_task()
            if task is None:
                return
            await self._handle(task, lane, provider)

    async def _handle(self, task: PersonTask, lane: int, provider: CapProvider) -> None:
        self._lifecycle.person_started(task.job)
        if self._registry is not None:
            self._registry.assign(lane, task.job, task.run)
        try:
            await self._processor.run(task.job, task.run, provider, lane)
        except CapDown as error:
            await self._scheduler.requeue(task)
            self._cap_gate.report_down(str(error))
        finally:
            if self._registry is not None:
                self._registry.release(lane)
            await self._scheduler.task_done(task)
        self._lifecycle.person_finished(task.job)
