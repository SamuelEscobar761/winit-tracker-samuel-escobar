import uuid
from collections.abc import Callable
from datetime import UTC, datetime

from app.config.settings import Settings
from app.csv_import.models import ImportReport
from app.jobs.event_log import EventLog
from app.jobs.events import EventType
from app.jobs.lifecycle import JobLifecycle
from app.jobs.models import (
    RETRYABLE_PERSON_STATES,
    Job,
    JobState,
    PersonRun,
    PersonState,
)
from app.jobs.progress import build_progress_data
from app.jobs.scheduler import FairScheduler


class JobNotFound(Exception):
    pass


class PersonNotFound(Exception):
    pass


class EmptyJob(Exception):
    pass


class JobNotRetryable(Exception):
    pass


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _new_job_id() -> str:
    return uuid.uuid4().hex[:12]


class JobService:
    def __init__(
        self,
        settings: Settings,
        scheduler: FairScheduler,
        lifecycle: JobLifecycle,
        now: Callable[[], datetime] = _utc_now,
        new_id: Callable[[], str] = _new_job_id,
    ) -> None:
        self._settings = settings
        self._scheduler = scheduler
        self._lifecycle = lifecycle
        self._now = now
        self._new_id = new_id
        self._jobs: dict[str, Job] = {}

    async def create_job(self, report: ImportReport, parallelism: int | None = None) -> Job:
        runs = [
            PersonRun(index=index, line_number=row.line_number, person=row.person)
            for index, row in enumerate(report.queueable_rows)
            if row.person is not None
        ]
        if not runs:
            raise EmptyJob("The file has no row that can be searched")
        job = self._build_job(report, runs, parallelism)
        self._jobs[job.id] = job
        job.event_log.append(
            EventType.JOB_CREATED,
            "Job created",
            {
                "total": len(runs),
                "rejected_rows": report.counts_of_rejected,
                "parallelism": job.parallelism,
            },
        )
        await self._scheduler.enqueue(job, runs)
        return job

    def get_job(self, job_id: str) -> Job:
        job = self._jobs.get(job_id)
        if job is None:
            raise JobNotFound(job_id)
        return job

    def get_person(self, job_id: str, person_index: int) -> tuple[Job, PersonRun]:
        job = self.get_job(job_id)
        if not 0 <= person_index < len(job.people):
            raise PersonNotFound(person_index)
        return job, job.people[person_index]

    def list_jobs(self) -> list[Job]:
        return sorted(self._jobs.values(), key=lambda job: job.created_at, reverse=True)

    async def cancel_job(self, job_id: str) -> Job:
        job = self.get_job(job_id)
        if job.state in (JobState.COMPLETED, JobState.CANCELLED):
            return job
        job.cancel_requested = True
        for run in await self._scheduler.clear_queue(job):
            run.state = PersonState.CANCELLED
        self._wake_captcha_waiters(job)
        self._lifecycle.person_finished(job)
        return job

    async def retry_failed(self, job_id: str) -> Job:
        job = self.get_job(job_id)
        if job.state is JobState.CANCELLED:
            raise JobNotRetryable("A cancelled job cannot be retried")
        runs = [run for run in job.people if run.state in RETRYABLE_PERSON_STATES]
        if not runs:
            return job
        for run in runs:
            run.reset_for_retry()
        job.state = JobState.RUNNING
        job.event_log.reopen()
        job.event_log.append(
            EventType.JOB_RETRY, "Retrying failed people", build_progress_data(job)
        )
        await self._scheduler.enqueue(job, runs)
        return job

    def resolve_captcha(self, job_id: str, person_index: int) -> None:
        _, run = self.get_person(job_id, person_index)
        run.captcha_resolved.set()

    def announce_cap_down(self, message: str) -> None:
        for job in self._active_jobs():
            job.event_log.append(
                EventType.CAP_DOWN, "The portal is down; searches are paused", {"reason": message}
            )

    def announce_cap_recovered(self) -> None:
        for job in self._active_jobs():
            job.event_log.append(EventType.CAP_RECOVERED, "The portal is back; searches resume")

    def _build_job(
        self, report: ImportReport, runs: list[PersonRun], parallelism: int | None
    ) -> Job:
        job_id = self._new_id()
        requested = parallelism or self._settings.default_parallelism
        return Job(
            id=job_id,
            created_at=self._now(),
            parallelism=max(1, min(requested, self._settings.max_workers, len(runs))),
            report=report,
            people=runs,
            event_log=EventLog(job_id, self._now),
        )

    def _active_jobs(self) -> list[Job]:
        return [
            job for job in self._jobs.values() if job.state in (JobState.QUEUED, JobState.RUNNING)
        ]

    def _wake_captcha_waiters(self, job: Job) -> None:
        for run in job.people:
            if run.state is PersonState.RUNNING:
                run.captcha_resolved.set()
