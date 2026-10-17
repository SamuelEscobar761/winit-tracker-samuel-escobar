import json
from datetime import date

from pydantic import BaseModel

from app.ai.model import StructuredModel
from app.cases.matching.assessment import AssessedCase
from app.people.models import Person

SYSTEM_PROMPT = (
    "You help a court-records clerk understand why a court case was linked to a person from "
    "their spreadsheet. The match label was decided by deterministic rules and is FIXED: never "
    "contradict it or propose a different label. Explain in plain English using only the facts "
    "you are given, list what supports the match and what weakens it, and suggest one next "
    "step for the clerk. Do not guess facts that are not provided."
)


class ExplanationDraft(BaseModel):
    summary: str
    supports: list[str]
    weakens: list[str]
    next_step: str


class MatchExplanation(ExplanationDraft):
    case_key: str
    label: str
    model: str
    ai_generated: bool = True


class MatchExplainer:
    def __init__(self, model: StructuredModel) -> None:
        self._model = model

    async def explain(self, person: Person, item: AssessedCase) -> MatchExplanation:
        draft = await self._model.ask(SYSTEM_PROMPT, build_prompt(person, item), ExplanationDraft)
        return MatchExplanation(
            **draft.model_dump(),
            case_key=item.case.case_key,
            label=item.assessment.label.value,
            model=self._model.name,
        )


def build_prompt(person: Person, item: AssessedCase) -> str:
    case = item.case
    facts = {
        "person_from_csv": {
            "first_name": person.first_name,
            "last_name": person.last_name,
            "date_of_birth": _iso(person.date_of_birth),
        },
        "case_from_portal": {
            "caption": case.caption,
            "date_of_birth": _iso(case.date_of_birth),
            "status": case.public_status_label,
            "file_date": _iso(case.file_date),
        },
        "fixed_label": item.assessment.label.value,
        "rule_reasons": list(item.assessment.reasons),
    }
    return json.dumps(facts, indent=2)


def _iso(value: date | None) -> str | None:
    return value.isoformat() if value else None
