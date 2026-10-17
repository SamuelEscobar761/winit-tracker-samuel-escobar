from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.ai.gate import AiStatus
from app.ai.services import AiServices
from app.api.dependencies import get_ai_services
from app.auth.dependencies import check_origin, require_session
from app.rules.healing.healer import RepairOutcome, RulesHealer
from app.rules.healing.incidents import DriftIncident
from app.rules.healing.proposals import RulesProposal
from app.rules.models import PortalRules
from app.rules.store import ChangeEntry

router = APIRouter(
    prefix="/rules",
    tags=["rules"],
    dependencies=[Depends(require_session), Depends(check_origin)],
)

AiDependency = Annotated[AiServices, Depends(get_ai_services)]


class RulesOverview(BaseModel):
    active: PortalRules
    versions: list[int]
    changelog: list[ChangeEntry]
    incidents: list[DriftIncident]
    proposals: list[RulesProposal]
    ai: AiStatus


class RollbackRequest(BaseModel):
    version: int
    reason: str = "Requested from the rules screen"


@router.get("")
async def read_rules(ai: AiDependency) -> RulesOverview:
    return RulesOverview(
        active=ai.rules.current,
        versions=ai.rules.versions(),
        changelog=list(reversed(ai.rules.changelog())),
        incidents=ai.incidents.all(),
        proposals=ai.proposals.all(),
        ai=ai.gate.status(),
    )


@router.post("/incidents/{incident_id}/repair")
async def repair_incident(incident_id: str, ai: AiDependency) -> RepairOutcome:
    if ai.healer is None:
        raise HTTPException(status_code=503, detail="AI is turned off")
    if ai.incidents.get(incident_id) is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return await ai.healer.repair(incident_id)


@router.post("/proposals/{proposal_id}/approve")
async def approve_proposal(proposal_id: str, ai: AiDependency) -> PortalRules:
    healer = _require_healer(ai)
    try:
        return healer.approve(proposal_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Proposal not found") from None
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from None


@router.post("/proposals/{proposal_id}/reject", status_code=204)
async def reject_proposal(proposal_id: str, ai: AiDependency) -> None:
    healer = _require_healer(ai)
    try:
        healer.reject(proposal_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Proposal not found") from None
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from None


@router.post("/rollback")
async def rollback_rules(request: RollbackRequest, ai: AiDependency) -> PortalRules:
    try:
        return ai.rules.rollback(request.version, request.reason)
    except KeyError:
        raise HTTPException(status_code=404, detail="Version not found") from None


def _require_healer(ai: AiServices) -> RulesHealer:
    if ai.healer is None:
        raise HTTPException(status_code=503, detail="AI is turned off")
    return ai.healer
