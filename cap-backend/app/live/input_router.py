from enum import StrEnum

from app.jobs.service import JobService
from app.live.input import InputEvent
from app.live.lanes import LaneRegistry


class InputOutcome(StrEnum):
    IGNORED = "ignored"
    FORWARDED = "forwarded"
    CAPTCHA_RESOLVED = "captcha_resolved"


class InputRouter:
    """Only a human's input is forwarded, and only while that lane waits for a CAPTCHA."""

    def __init__(self, registry: LaneRegistry, service: JobService) -> None:
        self._registry = registry
        self._service = service

    async def route(self, lane: int, event: InputEvent) -> InputOutcome:
        assignment = self._registry.assignment(lane)
        handler = self._registry.channel_for(lane).input_handler
        if assignment is None or handler is None or not assignment.run.captcha_pending:
            return InputOutcome.IGNORED
        await handler.handle(event)
        if not await handler.captcha_cleared():
            return InputOutcome.FORWARDED
        self._service.resolve_captcha(assignment.job.id, assignment.run.index)
        return InputOutcome.CAPTCHA_RESOLVED
