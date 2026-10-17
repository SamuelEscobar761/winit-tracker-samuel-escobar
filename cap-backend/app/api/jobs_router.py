from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Header,
    HTTPException,
    Query,
    Request,
    UploadFile,
)
from fastapi.responses import JSONResponse, StreamingResponse

from app.api.dependencies import get_csv_importer, get_job_service
from app.api.sse import SSE_HEADERS, parse_last_event_id, stream_events
from app.api.views import (
    JobListItem,
    JobSnapshot,
    PersonView,
    RawCaseView,
    ValidationView,
    to_job_list_item,
    to_job_snapshot,
    to_person_view,
    to_raw_case_view,
    to_report_view,
)
from app.auth.dependencies import check_origin, require_session
from app.config.settings import Settings
from app.csv_import.importer import CsvImporter
from app.csv_import.models import ImportReport
from app.jobs.models import Job
from app.jobs.service import (
    EmptyJob,
    JobNotFound,
    JobNotRetryable,
    JobService,
    PersonNotFound,
)

router = APIRouter(
    prefix="/jobs",
    tags=["jobs"],
    dependencies=[Depends(require_session), Depends(check_origin)],
)

ServiceDependency = Annotated[JobService, Depends(get_job_service)]


@router.post("/validate")
async def validate_file(
    request: Request,
    importer: Annotated[CsvImporter, Depends(get_csv_importer)],
    file: Annotated[UploadFile, File()],
) -> ValidationView:
    settings: Settings = request.app.state.settings
    report = importer.import_bytes(await file.read(settings.csv_max_bytes + 1))
    return ValidationView(
        report=to_report_view(report),
        ready_people=len(report.queueable_people),
        max_parallelism=max(1, min(settings.max_workers, len(report.queueable_people))),
        default_parallelism=min(settings.default_parallelism, settings.max_workers),
    )


@router.post("", status_code=201)
async def create_job(
    request: Request,
    service: ServiceDependency,
    importer: Annotated[CsvImporter, Depends(get_csv_importer)],
    file: Annotated[UploadFile, File()],
    parallelism: Annotated[int | None, Form(ge=1)] = None,
) -> JSONResponse:
    settings: Settings = request.app.state.settings
    data = await file.read(settings.csv_max_bytes + 1)
    report = importer.import_bytes(data)
    if report.has_file_errors:
        return _unprocessable("The file cannot be imported", report)
    try:
        job = await service.create_job(report, parallelism)
    except EmptyJob as error:
        return _unprocessable(str(error), report)
    body = {
        "job_id": job.id,
        "state": job.state.value,
        "parallelism": job.parallelism,
        "total_people": len(job.people),
        "events_url": f"/jobs/{job.id}/events",
        "report": to_report_view(report).model_dump(mode="json"),
    }
    return JSONResponse(body, status_code=201)


@router.get("")
async def list_jobs(service: ServiceDependency) -> list[JobListItem]:
    return [to_job_list_item(job) for job in service.list_jobs()]


@router.get("/{job_id}")
async def read_job(job_id: str, service: ServiceDependency) -> JobSnapshot:
    return to_job_snapshot(_find_job(service, job_id))


@router.get("/{job_id}/people/{person_index}")
async def read_person(job_id: str, person_index: int, service: ServiceDependency) -> PersonView:
    try:
        _, run = service.get_person(job_id, person_index)
    except JobNotFound:
        raise HTTPException(status_code=404, detail="Job not found") from None
    except PersonNotFound:
        raise HTTPException(status_code=404, detail="Person not found") from None
    return to_person_view(run)


@router.get("/{job_id}/people/{person_index}/cases/{case_key}/raw")
async def read_raw_case(
    job_id: str, person_index: int, case_key: str, service: ServiceDependency
) -> RawCaseView:
    try:
        _, run = service.get_person(job_id, person_index)
    except (JobNotFound, PersonNotFound):
        raise HTTPException(status_code=404, detail="Person not found") from None
    item = (
        next((c for c in run.analysis.cases if c.case.case_key == case_key), None)
        if run.analysis
        else None
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return to_raw_case_view(run, item)


@router.get("/{job_id}/events")
async def read_events(
    job_id: str,
    request: Request,
    service: ServiceDependency,
    last_event_id: Annotated[str | None, Header()] = None,
    after: Annotated[int | None, Query(ge=0)] = None,
) -> StreamingResponse:
    job = _find_job(service, job_id)
    settings: Settings = request.app.state.settings
    cursor = after if after is not None else parse_last_event_id(last_event_id)
    stream = stream_events(job.event_log, cursor, settings.sse_heartbeat_seconds)
    return StreamingResponse(stream, media_type="text/event-stream", headers=SSE_HEADERS)


@router.post("/{job_id}/cancel")
async def cancel_job(job_id: str, service: ServiceDependency) -> JobSnapshot:
    _find_job(service, job_id)
    return to_job_snapshot(await service.cancel_job(job_id))


@router.post("/{job_id}/people/{person_index}/captcha-solved", status_code=204)
async def captcha_solved(job_id: str, person_index: int, service: ServiceDependency) -> None:
    try:
        service.resolve_captcha(job_id, person_index)
    except JobNotFound:
        raise HTTPException(status_code=404, detail="Job not found") from None
    except PersonNotFound:
        raise HTTPException(status_code=404, detail="Person not found") from None


@router.post("/{job_id}/retry-failed")
async def retry_failed(job_id: str, service: ServiceDependency) -> JobSnapshot:
    _find_job(service, job_id)
    try:
        return to_job_snapshot(await service.retry_failed(job_id))
    except JobNotRetryable as error:
        raise HTTPException(status_code=409, detail=str(error)) from None


def _find_job(service: JobService, job_id: str) -> Job:
    try:
        return service.get_job(job_id)
    except JobNotFound:
        raise HTTPException(status_code=404, detail="Job not found") from None


def _unprocessable(message: str, report: ImportReport) -> JSONResponse:
    body = {"detail": message, "report": to_report_view(report).model_dump(mode="json")}
    return JSONResponse(body, status_code=422)
