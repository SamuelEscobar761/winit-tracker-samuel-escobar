import json
import re
from decimal import Decimal

from pydantic import BaseModel

from app.ai.errors import InvalidModelOutput
from app.ai.model import StructuredModel
from app.cases.matching.assessment import AssessedCase
from app.cases.models import CaseDetail

SYSTEM_PROMPT = (
    "You summarise the court cases found for one person for a clerk. Use only the facts "
    "provided. Every finding must cite the case keys it is based on, and every dollar amount "
    "you write must appear in the facts. Restricted cases only say 'Restricted by portal'; "
    "never speculate about them. Keep the headline under 20 words."
)
MONEY = re.compile(r"\$\s?([\d,]+(?:\.\d{1,2})?)")


class Finding(BaseModel):
    text: str
    case_keys: list[str]


class InsightDraft(BaseModel):
    headline: str
    findings: list[Finding]


class Insight(InsightDraft):
    model: str
    dropped_findings: int
    ai_generated: bool = True


class InsightAgent:
    def __init__(self, model: StructuredModel) -> None:
        self._model = model

    async def summarise(self, cases: list[AssessedCase], details: dict[str, CaseDetail]) -> Insight:
        facts = build_facts(cases, details)
        draft = await self._model.ask(SYSTEM_PROMPT, json.dumps(facts, indent=2), InsightDraft)
        return verify_draft(draft, facts, self._model.name)


def build_facts(
    cases: list[AssessedCase], details: dict[str, CaseDetail]
) -> list[dict[str, object]]:
    return [_case_facts(item, details.get(item.case.case_key)) for item in cases]


def verify_draft(draft: InsightDraft, facts: list[dict[str, object]], model: str) -> Insight:
    known_keys = {str(fact["case_key"]) for fact in facts}
    known_amounts = {amount for fact in facts for amount in _amounts_in(fact)}
    kept = [f for f in draft.findings if _is_grounded(f, known_keys, known_amounts)]
    if not kept:
        raise InvalidModelOutput("No finding could be traced back to the cases")
    dropped = len(draft.findings) - len(kept)
    return Insight(headline=draft.headline, findings=kept, model=model, dropped_findings=dropped)


def _is_grounded(finding: Finding, known_keys: set[str], known_amounts: set[Decimal]) -> bool:
    if not finding.case_keys or not set(finding.case_keys) <= known_keys:
        return False
    return all(amount in known_amounts for amount in _amounts_in(finding.text))


def _amounts_in(value: object) -> set[Decimal]:
    return {Decimal(match.replace(",", "")) for match in MONEY.findall(json.dumps(value))}


def _case_facts(item: AssessedCase, detail: CaseDetail | None) -> dict[str, object]:
    case = item.case
    return {
        "case_key": case.case_key,
        "status": case.public_status_label,
        "match_label": item.assessment.label.value,
        "file_date": case.file_date.isoformat() if case.file_date else None,
        "amount_due": f"${detail.amount_due}" if detail and detail.amount_due is not None else None,
        "charges": [charge.description for charge in detail.displayed_charges] if detail else [],
    }
