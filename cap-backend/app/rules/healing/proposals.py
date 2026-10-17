from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from app.rules.diff import RuleChange
from app.rules.models import PortalRules

ProposalStatus = Literal["pending", "applied", "rejected"]


class CanaryResult(BaseModel):
    passed: bool
    detail: str


class RulesProposal(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    incident_id: str
    diagnosis: str
    model: str
    changes: list[RuleChange]
    canary: CanaryResult
    candidate: PortalRules
    status: ProposalStatus = "pending"


class ProposalBoard:
    def __init__(self) -> None:
        self._proposals: dict[str, RulesProposal] = {}

    def add(self, proposal: RulesProposal) -> RulesProposal:
        self._proposals[proposal.id] = proposal
        return proposal

    def get(self, proposal_id: str) -> RulesProposal | None:
        return self._proposals.get(proposal_id)

    def mark(self, proposal_id: str, status: ProposalStatus) -> RulesProposal:
        updated = self._proposals[proposal_id].model_copy(update={"status": status})
        self._proposals[proposal_id] = updated
        return updated

    def all(self) -> list[RulesProposal]:
        return sorted(self._proposals.values(), key=lambda item: item.at, reverse=True)
