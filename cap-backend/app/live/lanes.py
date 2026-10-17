from dataclasses import dataclass

from app.jobs.models import Job, PersonRun
from app.live.frames import FrameBroadcaster
from app.live.input import InputHandler


class LaneChannel:
    """What a viewer can see of a worker (frames) and do to it (input)."""

    def __init__(self, lane: int) -> None:
        self.lane = lane
        self.frames = FrameBroadcaster(lane)
        self.input_handler: InputHandler | None = None


@dataclass(frozen=True)
class LaneAssignment:
    job: Job
    run: PersonRun


@dataclass(frozen=True)
class LaneStatus:
    lane: int
    job_id: str | None
    person_index: int | None
    person_state: str | None
    awaiting_captcha: bool


class LaneRegistry:
    def __init__(self) -> None:
        self._channels: dict[int, LaneChannel] = {}
        self._assignments: dict[int, LaneAssignment] = {}

    def channel_for(self, lane: int) -> LaneChannel:
        return self._channels.setdefault(lane, LaneChannel(lane))

    def assign(self, lane: int, job: Job, run: PersonRun) -> None:
        self._assignments[lane] = LaneAssignment(job, run)

    def release(self, lane: int) -> None:
        self._assignments.pop(lane, None)

    def assignment(self, lane: int) -> LaneAssignment | None:
        return self._assignments.get(lane)

    def lanes(self) -> list[int]:
        return sorted(self._channels)

    def status(self, lane: int) -> LaneStatus:
        assignment = self._assignments.get(lane)
        if assignment is None:
            return LaneStatus(lane, None, None, None, False)
        run = assignment.run
        return LaneStatus(lane, assignment.job.id, run.index, run.state.value, run.captcha_pending)
