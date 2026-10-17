from datetime import UTC, datetime

from app.config.settings import Settings
from app.csv_import.models import ImportReport
from app.jobs.event_log import EventLog
from app.jobs.lifecycle import JobLifecycle
from app.jobs.models import Job, PersonRun
from app.jobs.scheduler import FairScheduler
from app.jobs.service import JobService
from app.live.input import InputEvent, InputKind
from app.live.input_router import InputOutcome, InputRouter
from app.live.lanes import LaneRegistry
from tests.support.builders import make_person


class RecordingHandler:
    def __init__(self, clears_captcha: bool) -> None:
        self.events: list[InputEvent] = []
        self._clears_captcha = clears_captcha

    async def handle(self, event: InputEvent) -> None:
        self.events.append(event)

    async def captcha_cleared(self) -> bool:
        return self._clears_captcha


def build_router(
    clears_captcha: bool,
) -> tuple[InputRouter, LaneRegistry, PersonRun, RecordingHandler]:
    registry = LaneRegistry()
    handler = RecordingHandler(clears_captcha)
    registry.channel_for(0).input_handler = handler
    run = PersonRun(index=0, line_number=2, person=make_person())
    job = Job(
        id="job-1",
        created_at=datetime.now(UTC),
        parallelism=1,
        report=ImportReport(),
        people=[run],
        event_log=EventLog("job-1"),
    )
    service = JobService(Settings(), FairScheduler(), JobLifecycle())
    service._jobs["job-1"] = job  # noqa: SLF001
    registry.assign(0, job, run)
    return InputRouter(registry, service), registry, run, handler


CLICK = InputEvent(type=InputKind.CLICK, x=1, y=1)


async def test_input_is_ignored_while_no_captcha_is_waiting() -> None:
    router, _, _, handler = build_router(clears_captcha=False)

    assert await router.route(0, CLICK) is InputOutcome.IGNORED
    assert handler.events == []


async def test_input_is_ignored_on_a_lane_without_a_person() -> None:
    router, registry, _, handler = build_router(clears_captcha=False)
    registry.release(0)

    assert await router.route(0, CLICK) is InputOutcome.IGNORED
    assert handler.events == []


async def test_input_is_forwarded_while_a_captcha_is_waiting() -> None:
    router, _, run, handler = build_router(clears_captcha=False)
    run.captcha_pending = True

    assert await router.route(0, CLICK) is InputOutcome.FORWARDED
    assert handler.events == [CLICK]
    assert not run.captcha_resolved.is_set()


async def test_solving_the_captcha_resumes_the_person() -> None:
    router, _, run, _ = build_router(clears_captcha=True)
    run.captcha_pending = True

    assert await router.route(0, CLICK) is InputOutcome.CAPTCHA_RESOLVED
    assert run.captcha_resolved.is_set()


async def test_a_lane_without_a_handler_ignores_input() -> None:
    router, registry, run, _ = build_router(clears_captcha=True)
    run.captcha_pending = True
    registry.channel_for(0).input_handler = None

    assert await router.route(0, CLICK) is InputOutcome.IGNORED
