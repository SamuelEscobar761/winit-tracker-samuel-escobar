from collections.abc import Mapping
from datetime import date
from decimal import Decimal

from pydantic import ValidationError

from app.cases.keys import build_case_key
from app.cases.models import CaseDetail, PaymentOption, PaymentPlan
from app.cases.parsing.charges import parse_charge
from app.cases.parsing.envelope import canonicalize, unwrap_data
from app.cases.parsing.errors import MalformedResponseError
from app.cases.parsing.raw_models import RawBailOption, RawSelectData
from app.cases.values import clean_text, parse_amount, parse_portal_date
from app.rules.models import PortalRules

PAY_IN_FULL_CODE = "PAYF"
DEFAULT_RULES = PortalRules().complete_fields()


def parse_select_response(
    payload: Mapping[str, object], rules: PortalRules = DEFAULT_RULES
) -> CaseDetail:
    data = canonicalize(unwrap_data(payload, rules.responses), rules.fields.select_data)
    raw = _validate_data(data)
    case_number = clean_text(raw.case_number)
    if case_number is None:
        raise MalformedResponseError("The case request has no case number")
    return CaseDetail(
        case_key=build_case_key(case_number),
        portal_case_id=clean_text(raw.case_id),
        party_id=clean_text(raw.party_id),
        full_name=clean_text(raw.full_name),
        charges=tuple(parse_charge(charge) for charge in raw.charges),
        proof_of_correction_required=raw.is_poc,
        proof_of_correction_charges=tuple(parse_charge(charge) for charge in raw.poc_changes),
        amount_due=parse_amount(raw.bf_amount),
        payment_options=tuple(_to_payment_option(option) for option in raw.bail_options),
        has_payment_plan=raw.has_payment_plan,
        payment_plan=_to_payment_plan(raw),
        is_extension_eligible=raw.is_extension_eligible,
        original_date=parse_portal_date(raw.original_date),
        extended_date=parse_portal_date(raw.extended_date),
        notices=_collect_notices(raw),
    )


def _validate_data(data: object) -> RawSelectData:
    try:
        return RawSelectData.model_validate(data)
    except ValidationError as error:
        raise MalformedResponseError(f"Invalid case data: {error}") from error


def _to_payment_option(option: RawBailOption) -> PaymentOption:
    return PaymentOption(
        code=clean_text(option.code),
        text=clean_text(option.text) or "",
        amount=parse_amount(option.amount),
    )


def _to_payment_plan(raw: RawSelectData) -> PaymentPlan | None:
    """The payment fields describe an offer unless the case already has a plan."""
    if not raw.has_payment_plan:
        return None
    return PaymentPlan(
        past_amount_due=raw.payment_past_amount,
        monthly_amount=raw.payment_monthly_amount,
        remaining_balance=_find_remaining_balance(raw.bail_options),
        total=raw.payment_total,
        months=raw.payment_months,
        due_day=clean_text(raw.payment_due_on),
        start_date=parse_portal_date(raw.payment_start_date),
        final_due_date=parse_portal_date(raw.payment_final_due_date),
        due_dates=_parse_due_dates(raw.payment_due_dates),
    )


def _find_remaining_balance(options: list[RawBailOption]) -> Decimal | None:
    """The balance is only reported as the amount of the pay-in-full option (code PAYF)."""
    for option in options:
        if clean_text(option.code) == PAY_IN_FULL_CODE:
            return parse_amount(option.amount)
    return None


def _parse_due_dates(raw_dates: list[str] | None) -> tuple[date, ...]:
    parsed = (parse_portal_date(raw_date) for raw_date in raw_dates or [])
    return tuple(due_date for due_date in parsed if due_date is not None)


def _collect_notices(raw: RawSelectData) -> tuple[str, ...]:
    messages = (clean_text(raw.ma_message), clean_text(raw.user_message))
    return tuple(message for message in messages if message is not None)
