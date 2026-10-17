from collections.abc import Awaitable
from typing import Annotated, TypeVar

from fastapi import APIRouter, Depends, HTTPException

from app.ai.errors import AiError
from app.ai.explain import MatchExplanation
from app.ai.gate import AiStatus
from app.ai.insight import Insight
from app.ai.services import AiServices
from app.ai.structuring import StructuredNotices
from app.api.dependencies import get_ai_services, get_job_service
from app.auth.dependencies import check_origin, require_session
from app.cases.matching.assessment import AssessedCase
from app.jobs.models import PersonRun
from app.jobs.service import JobNotFound, JobService, PersonNotFound

router = APIRouter(
    prefix="/ai",
    tags=["ai"],
    dependencies=[Depends(require_session), Depends(check_origin)],
)

AgentT = TypeVar("AgentT")
AnswerT = TypeVar("AnswerT")
ServiceDependency = Annotated[JobService, Depends(get_job_service)]
AiDependency = Annotated[AiServices, Depends(get_ai_services)]


@router.get("/status")
async def read_status(ai: AiDependency) -> AiStatus:
    return ai.gate.status()


@router.post("/jobs/{job_id}/people/{person_index}/cases/{case_key}/explain")
async def explain_match(
    job_id: str, person_index: int, case_key: str, service: ServiceDependency, ai: AiDependency
) -> MatchExplanation:
    explainer = _require(ai.explainer)
    run = _find_run(service, job_id, person_index)
    item = _find_case(run, case_key)
    return await _answer(explainer.explain(run.person, item))


@router.post("/jobs/{job_id}/people/{person_index}/insight")
async def summarise_person(
    job_id: str, person_index: int, service: ServiceDependency, ai: AiDependency
) -> Insight:
    agent = _require(ai.insight)
    run = _find_run(service, job_id, person_index)
    if run.analysis is None or not run.analysis.cases:
        raise HTTPException(status_code=409, detail="This person has no cases to summarise")
    return await _answer(agent.summarise(list(run.analysis.cases), run.details))


@router.post("/jobs/{job_id}/people/{person_index}/cases/{case_key}/notices")
async def structure_notices(
    job_id: str, person_index: int, case_key: str, service: ServiceDependency, ai: AiDependency
) -> StructuredNotices:
    structurer = _require(ai.structurer)
    run = _find_run(service, job_id, person_index)
    detail = run.details.get(case_key)
    if detail is None or not detail.notices:
        raise HTTPException(status_code=409, detail="This case has no notices")
    return await _answer(structurer.structure(list(detail.notices)))


def _require(agent: AgentT | None) -> AgentT:
    if agent is None:
        raise HTTPException(status_code=503, detail="AI is turned off")
    return agent


async def _answer(pending: Awaitable[AnswerT]) -> AnswerT:
    try:
        return await pending
    except AiError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


def _find_run(service: JobService, job_id: str, person_index: int) -> PersonRun:
    try:
        return service.get_person(job_id, person_index)[1]
    except (JobNotFound, PersonNotFound):
        raise HTTPException(status_code=404, detail="Person not found") from None


def _find_case(run: PersonRun, case_key: str) -> AssessedCase:
    cases = run.analysis.cases if run.analysis else []
    item = next((case for case in cases if case.case.case_key == case_key), None)
    if item is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return item
