import json
import re

from app.ai.explain import ExplanationDraft
from app.ai.insight import Finding, InsightDraft
from app.ai.offline_model import OfflineModel
from app.ai.structuring import NoticeDraft, NoticeItem, NoticeKind

DATE_PATTERN = re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b")
MONEY_PATTERN = re.compile(r"\$\s?[\d,]+(?:\.\d{1,2})?")
KIND_KEYWORDS: tuple[tuple[str, NoticeKind], ...] = (
    ("extension", "extension"),
    ("proof of correction", "proof_of_correction"),
    ("due", "payment_due"),
    ("warning", "warning"),
)


async def explain_offline(prompt: str) -> ExplanationDraft:
    facts = json.loads(prompt)
    reasons: list[str] = facts["rule_reasons"]
    label: str = facts["fixed_label"]
    weak = [reason for reason in reasons if _is_weakness(reason)]
    return ExplanationDraft(
        summary=f"The case is labelled {label}: " + "; ".join(reasons) + ".",
        supports=[reason for reason in reasons if reason not in weak],
        weakens=weak,
        next_step=_next_step(label),
    )


async def insight_offline(prompt: str) -> InsightDraft:
    facts: list[dict[str, object]] = json.loads(prompt)
    open_cases = [fact for fact in facts if fact["amount_due"]]
    findings = [
        Finding(text=_describe(fact), case_keys=[str(fact["case_key"])]) for fact in open_cases
    ]
    headline = f"{len(facts)} cases found, {len(open_cases)} with an amount due"
    return InsightDraft(headline=headline, findings=findings or _fallback(facts))


async def notices_offline(prompt: str) -> NoticeDraft:
    notices: list[str] = json.loads(prompt)["notices"]
    return NoticeDraft(items=[_notice_item(text) for text in notices if text.strip()])


def register_offline_handlers(model: OfflineModel) -> None:
    model.register(ExplanationDraft, explain_offline)
    model.register(InsightDraft, insight_offline)
    model.register(NoticeDraft, notices_offline)


def _is_weakness(reason: str) -> bool:
    lowered = reason.lower()
    return any(word in lowered for word in ("differs", "no date of birth", "variant", "extra"))


def _next_step(label: str) -> str:
    steps = {
        "confirmed": "No action needed.",
        "probable": "Check the date of birth on the original record if it is available.",
        "possible": "Verify the identity manually before relying on this case.",
        "unlikely": "Treat as a different person unless other evidence appears.",
    }
    return steps.get(label, "Review manually.")


def _describe(fact: dict[str, object]) -> str:
    return f"Case {fact['case_key']} ({fact['status']}) has {fact['amount_due']} due."


def _fallback(facts: list[dict[str, object]]) -> list[Finding]:
    return [
        Finding(
            text=f"Case {fact['case_key']} is {fact['status']}.", case_keys=[str(fact["case_key"])]
        )
        for fact in facts[:3]
    ]


def _notice_item(text: str) -> NoticeItem:
    lowered = text.lower()
    kind = next((kind for word, kind in KIND_KEYWORDS if word in lowered), "other")
    date_match = DATE_PATTERN.search(text)
    money_match = MONEY_PATTERN.search(text)
    return NoticeItem(
        kind=kind,
        excerpt=text.strip(),
        date_text=date_match.group(0) if date_match else None,
        amount_text=money_match.group(0) if money_match else None,
    )
