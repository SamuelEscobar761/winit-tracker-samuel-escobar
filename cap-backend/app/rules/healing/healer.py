import json
from collections import deque
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from pydantic import BaseModel

from app.ai.errors import AiError
from app.ai.model import StructuredModel
from app.rules.diff import diff_rules
from app.rules.healing.canary import Canary
from app.rules.healing.incidents import DriftIncident, IncidentLog, IncidentStatus
from app.rules.healing.patch import InvalidPatch, RulesPatchProposal, apply_patch
from app.rules.healing.proposals import CanaryResult, ProposalBoard, RulesProposal
from app.rules.models import PortalRules
from app.rules.registry import RulesRegistry

SYSTEM_PROMPT = (
    "You maintain the scraping rules of a court-case tracker. The public portal changed and a "
    "scraper step stopped working. You receive the current rules (JSON) and privacy-safe "
    "evidence of what the portal looks like now: control labels, element ids, API paths and "
    "the key structure of JSON answers. Propose the smallest set of edits that makes the "
    "rules match the evidence. Each edit has a dotted path to an EXISTING rule "
    "(for example ui.search_button, api.search_path, fields.search_item.caseNumber) and the "
    "new value. Never invent paths, never output code or scripts, and change nothing the "
    "evidence does not contradict. If the evidence does not explain the failure, return an "
    "empty edits list and say why in the diagnosis."
)
HOUR = timedelta(hours=1)


class RepairOutcome(BaseModel):
    incident_id: str
    status: IncidentStatus
    message: str
    proposal_id: str | None = None
    applied_version: int | None = None


class RulesHealer:
    def __init__(
        self,
        model: StructuredModel,
        registry: RulesRegistry,
        incidents: IncidentLog,
        proposals: ProposalBoard,
        canary: Canary,
        auto_apply: bool,
        max_repairs_per_hour: int,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._model = model
        self._registry = registry
        self._incidents = incidents
        self._proposals = proposals
        self._canary = canary
        self._auto_apply = auto_apply
        self._max_repairs_per_hour = max_repairs_per_hour
        self._now = now
        self._attempts: deque[datetime] = deque()

    async def repair(self, incident_id: str) -> RepairOutcome:
        incident = self._incidents.get(incident_id)
        if incident is None:
            raise KeyError(incident_id)
        if not self._take_attempt():
            return self._finish(incident, "open", "Repair rate limit reached; retry later")
        self._incidents.update(incident.id, "repairing")
        try:
            return await self._propose_and_verify(incident)
        except AiError as error:
            return self._finish(incident, "failed", f"The model could not help: {error}")
        except InvalidPatch as error:
            return self._finish(incident, "failed", f"The proposal was rejected: {error}")

    def approve(self, proposal_id: str) -> PortalRules:
        proposal = self._pending(proposal_id)
        rules = self._registry.activate(
            proposal.candidate,
            "manual",
            f"Approved agent proposal {proposal.id}: {proposal.diagnosis}",
            incident_id=proposal.incident_id,
            model=proposal.model,
            canary=proposal.canary.detail,
        )
        self._proposals.mark(proposal.id, "applied")
        self._incidents.update(
            proposal.incident_id, "repaired", f"Approved as version {rules.version}"
        )
        return rules

    def reject(self, proposal_id: str) -> None:
        proposal = self._pending(proposal_id)
        self._proposals.mark(proposal.id, "rejected")
        self._incidents.update(proposal.incident_id, "dismissed", "Proposal rejected by a person")

    async def _propose_and_verify(self, incident: DriftIncident) -> RepairOutcome:
        current = self._registry.current
        answer = await self._model.ask(
            SYSTEM_PROMPT, _build_prompt(current, incident), RulesPatchProposal
        )
        candidate = apply_patch(current, answer.edits)
        changes = diff_rules(current, candidate)
        if not changes:
            return self._finish(
                incident, "failed", f"No rule change explains it: {answer.diagnosis}"
            )
        canary = await self._canary.verify(candidate)
        proposal = self._proposals.add(
            RulesProposal(
                incident_id=incident.id,
                diagnosis=answer.diagnosis,
                model=self._model.name,
                changes=changes,
                canary=canary,
                candidate=candidate,
            )
        )
        return self._conclude(incident, proposal, canary)

    def _conclude(
        self, incident: DriftIncident, proposal: RulesProposal, canary: CanaryResult
    ) -> RepairOutcome:
        if not canary.passed:
            self._proposals.mark(proposal.id, "rejected")
            return self._finish(incident, "failed", f"Canary failed: {canary.detail}", proposal.id)
        if not self._auto_apply:
            return self._finish(
                incident, "awaiting_review", "Waiting for a person to approve", proposal.id
            )
        rules = self._registry.activate(
            proposal.candidate,
            "agent",
            proposal.diagnosis,
            incident_id=incident.id,
            model=proposal.model,
            canary=canary.detail,
        )
        self._proposals.mark(proposal.id, "applied")
        return self._finish(
            incident, "repaired", f"Applied as version {rules.version}", proposal.id, rules.version
        )

    def _finish(
        self,
        incident: DriftIncident,
        status: IncidentStatus,
        message: str,
        proposal_id: str | None = None,
        applied_version: int | None = None,
    ) -> RepairOutcome:
        self._incidents.update(incident.id, status, message)
        return RepairOutcome(
            incident_id=incident.id,
            status=status,
            message=message,
            proposal_id=proposal_id,
            applied_version=applied_version,
        )

    def _pending(self, proposal_id: str) -> RulesProposal:
        proposal = self._proposals.get(proposal_id)
        if proposal is None:
            raise KeyError(proposal_id)
        if proposal.status != "pending":
            raise ValueError(f"Proposal {proposal_id} is {proposal.status}")
        return proposal

    def _take_attempt(self) -> bool:
        now = self._now()
        while self._attempts and now - self._attempts[0] > HOUR:
            self._attempts.popleft()
        if len(self._attempts) >= self._max_repairs_per_hour:
            return False
        self._attempts.append(now)
        return True


def _build_prompt(rules: PortalRules, incident: DriftIncident) -> str:
    payload = {
        "failure": {"kind": incident.kind, "message": incident.message},
        "current_rules": rules.model_dump(exclude={"schema_version", "version"}),
        "evidence": incident.evidence,
    }
    return json.dumps(payload, indent=2)
