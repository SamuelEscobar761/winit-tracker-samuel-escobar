import copy
import hashlib

from app.cases.models import CaseSummary
from app.cases.status import CaseStatus
from app.providers.mock.catalog import JsonObject, MockCatalog

_BASE_AMOUNT = 100
_AMOUNT_SPREAD = 1500


def build_synthetic_detail_payload(case: CaseSummary, catalog: MockCatalog) -> JsonObject:
    """Cases without a recorded detail reuse a recorded layout with deterministic values."""
    template = (
        catalog.payment_plan_template
        if case.status is CaseStatus.AR_FINE
        else catalog.proof_of_correction_template
    )
    payload: JsonObject = copy.deepcopy(template)
    _personalize(payload["data"], case)
    payload["message"] = f"Found Traffic Case {case.case_number}"
    return payload


def _personalize(data: JsonObject, case: CaseSummary) -> None:
    amount = _deterministic_amount(case.case_key)
    data["caseNumber"] = case.case_key
    data["caseId"] = case.portal_case_id
    data["fullName"] = case.caption
    data["bfAmount"] = amount
    for option in data["bailOptions"]:
        if option.get("amount") not in (None, "0"):
            option["amount"] = amount


def _deterministic_amount(case_key: str) -> str:
    digest = int(hashlib.sha256(case_key.encode("utf-8")).hexdigest(), 16)
    return f"{_BASE_AMOUNT + digest % _AMOUNT_SPREAD:,.2f}"
