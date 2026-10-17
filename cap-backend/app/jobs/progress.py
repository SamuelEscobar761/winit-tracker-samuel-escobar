from app.jobs.models import Job, PersonState


def build_progress_data(job: Job) -> dict[str, int]:
    total = len(job.people)
    finished = sum(1 for run in job.people if run.is_terminal)
    data = {state.value: job.count_people(state) for state in PersonState}
    data.update(
        total=total, finished=finished, percent=round(100 * finished / total) if total else 100
    )
    return data
