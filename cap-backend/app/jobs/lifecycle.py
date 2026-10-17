from app.jobs.events import EventType
from app.jobs.models import Job, JobState, PersonState
from app.jobs.progress import build_progress_data


class JobLifecycle:
    def person_started(self, job: Job) -> None:
        if job.state is not JobState.QUEUED:
            return
        job.state = JobState.RUNNING
        job.event_log.append(EventType.JOB_STARTED, "Job started", {"total": len(job.people)})

    def person_finished(self, job: Job) -> None:
        if job.state in (JobState.COMPLETED, JobState.CANCELLED):
            return
        if job.cancel_requested and job.running_count == 0:
            self._cancel(job)
        elif job.all_people_terminal:
            self._complete(job)

    def _complete(self, job: Job) -> None:
        job.state = JobState.COMPLETED
        job.event_log.append(EventType.JOB_COMPLETE, "Job complete", build_progress_data(job))
        job.event_log.close()

    def _cancel(self, job: Job) -> None:
        job.state = JobState.CANCELLED
        for run in job.people:
            if not run.is_terminal:
                run.state = PersonState.CANCELLED
        job.event_log.append(EventType.JOB_CANCELLED, "Job cancelled", build_progress_data(job))
        job.event_log.close()
