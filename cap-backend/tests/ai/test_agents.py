from datetime import date
from decimal import Decimal

import pytest

from app.ai.errors import InvalidModelOutput
from app.ai.explain import ExplanationDraft, MatchExplainer
from app.ai.gate import AiGate
from app.ai.insight import Finding, InsightAgent, InsightDraft
from app.ai.offline import register_offline_handlers
from app.ai.offline_model import OfflineModel
from app.ai.structuring import NoticeDraft, NoticeItem, NoticeStructurer
from app.cases.matching.assessment import AssessedCase, MatchAssessment, MatchLabel, assess_case
from app.cases.models import CaseDetail, Charge
from app.config.settings import Settings
from tests.ai.fakes import ScriptedModel
from tests.support.builders import make_case, make_person


def assessed(label: MatchLabel = MatchLabel.UNLIKELY, number: str = "25IN-000001") -> AssessedCase:
    case = make_case(date_of_birth=date(1980, 1, 1), case_number=number)
    return AssessedCase(case, MatchAssessment(label, ("The date of birth differs",)))


def detail_for(case_key: str, amount: str | None) -> CaseDetail:
    return CaseDetail(
        case_key=case_key,
        portal_case_id=None,
        party_id=None,
        full_name=None,
        charges=(Charge(statute="VC 22350", description="Unsafe speed", raw=""),),
        proof_of_correction_required=False,
        proof_of_correction_charges=(),
        amount_due=Decimal(amount) if amount else None,
        payment_options=(),
        has_payment_plan=False,
        payment_plan=None,
        is_extension_eligible=False,
        original_date=None,
        extended_date=None,
        notices=(),
    )


def gate(**values: object) -> AiGate:
    return AiGate(Settings.model_validate(values))


def test_ai_is_off_by_default() -> None:
    status = gate().status()

    assert (status.enabled, status.available, status.mode) == (False, False, "off")
    assert status.reason == "AI_ENABLED is false"


def test_enabling_ai_without_a_key_keeps_it_off() -> None:
    status = gate(ai_enabled=True).status()

    assert status.available is False
    assert status.reason == "ANTHROPIC_API_KEY is not set"


@pytest.mark.parametrize(
    ("values", "mode"),
    [
        ({"ai_enabled": True, "anthropic_api_key": "sk-test"}, "anthropic"),
        ({"ai_enabled": True, "ai_offline_mock": True}, "offline-mock"),
    ],
)
def test_ai_turns_on_with_a_key_or_the_offline_mock(values: dict[str, object], mode: str) -> None:
    assert gate(**values).status().mode == mode


async def test_the_explainer_can_never_change_the_deterministic_label() -> None:
    draft = ExplanationDraft(
        summary="Definitely the same person", supports=["x"], weakens=[], next_step="None"
    )
    explainer = MatchExplainer(ScriptedModel(draft))

    result = await explainer.explain(make_person(), assessed(MatchLabel.UNLIKELY))

    assert result.label == "unlikely"
    assert result.ai_generated is True


async def test_the_explainer_prompt_leaves_out_licence_numbers() -> None:
    model = ScriptedModel(ExplanationDraft(summary="s", supports=[], weakens=[], next_step="n"))
    person = make_person(date_of_birth=date(1980, 1, 1))
    case = make_case(drivers_license="D1234567", date_of_birth=date(1990, 2, 2))
    item = AssessedCase(case, assess_case(person, case))

    await MatchExplainer(model).explain(person, item)

    assert "D1234567" not in model.prompts[0]
    assert "fixed_label" in model.prompts[0]


async def test_the_offline_explainer_uses_the_rule_reasons() -> None:
    model = OfflineModel()
    register_offline_handlers(model)

    result = await MatchExplainer(model).explain(make_person(), assessed())

    assert "The date of birth differs" in result.weakens
    assert "unlikely" in result.summary


async def test_insight_findings_must_cite_real_cases_and_real_amounts() -> None:
    cases = [assessed(number="25IN-000001")]
    key = cases[0].case.case_key
    details = {key: detail_for(key, "250.00")}
    draft = InsightDraft(
        headline="One open case",
        findings=[
            Finding(text="Case owes $250.00.", case_keys=[key]),
            Finding(text="Case owes $999.00.", case_keys=[key]),
            Finding(text="Invented case.", case_keys=["99XX-000009"]),
            Finding(text="No citation.", case_keys=[]),
        ],
    )

    insight = await InsightAgent(ScriptedModel(draft)).summarise(cases, details)

    assert [finding.text for finding in insight.findings] == ["Case owes $250.00."]
    assert insight.dropped_findings == 3


async def test_an_insight_without_any_grounded_finding_is_refused() -> None:
    cases = [assessed()]
    draft = InsightDraft(headline="x", findings=[Finding(text="Made up", case_keys=["nope"])])

    with pytest.raises(InvalidModelOutput):
        await InsightAgent(ScriptedModel(draft)).summarise(cases, {})


async def test_the_offline_insight_is_grounded_by_construction() -> None:
    model = OfflineModel()
    register_offline_handlers(model)
    cases = [assessed(number="25IN-000001"), assessed(number="25IN-000002")]
    key = cases[0].case.case_key
    details = {key: detail_for(key, "250.00")}

    insight = await InsightAgent(model).summarise(cases, details)

    assert insight.dropped_findings == 0
    assert "$250.00" in insight.findings[0].text


async def test_structured_notices_must_be_traceable_to_the_source_text() -> None:
    source = ["Payment of $120.00 is due by 11/30/2026."]
    draft = NoticeDraft(
        items=[
            NoticeItem(
                kind="payment_due", excerpt=source[0], date_text="11/30/2026", amount_text="$120.00"
            ),
            NoticeItem(
                kind="payment_due", excerpt=source[0], date_text="12/01/2026", amount_text=None
            ),
            NoticeItem(
                kind="warning", excerpt="Not in the source", date_text=None, amount_text=None
            ),
        ]
    )

    result = await NoticeStructurer(ScriptedModel(draft)).structure(source)

    assert len(result.items) == 1
    assert result.dropped_items == 2


async def test_the_offline_structurer_extracts_dates_and_amounts() -> None:
    model = OfflineModel()
    register_offline_handlers(model)

    result = await NoticeStructurer(model).structure(["Balance $85.50 due by 01/15/2027."])

    assert result.items[0].kind == "payment_due"
    assert (result.items[0].date_text, result.items[0].amount_text) == ("01/15/2027", "$85.50")
    assert result.dropped_items == 0
