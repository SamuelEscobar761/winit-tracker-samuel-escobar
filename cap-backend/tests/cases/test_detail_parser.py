from datetime import date
from decimal import Decimal

import pytest

from app.cases.parsing.detail_parser import parse_select_response
from app.cases.parsing.errors import MalformedResponseError, PortalResponseError
from tests.support.fixtures import load_fixture


def test_case_with_proof_of_correction_is_parsed() -> None:
    detail = parse_select_response(load_fixture("select_26IN-055186.json"))

    assert detail.case_key == "26IN055186"
    assert detail.full_name == "RODRIGUEZ, PEDRO LUIS"
    assert detail.amount_due == Decimal("1665.00")
    assert detail.proof_of_correction_required
    assert not detail.has_payment_plan


def test_charges_are_split_into_statute_and_description() -> None:
    detail = parse_select_response(load_fixture("select_26IN-055186.json"))

    assert len(detail.charges) == 4
    assert detail.charges[1].statute == "VC12500(A)-I"
    assert detail.charges[1].description == "No Operator License"
    assert detail.charges[3].statute == "VC40508(A)-I"


def test_proof_of_correction_charges_drop_the_charge_prefix() -> None:
    detail = parse_select_response(load_fixture("select_26IN-055186.json"))

    assert [charge.statute for charge in detail.proof_of_correction_charges] == [
        "VC4000(A)(1)-I",
        "VC12500(A)-I",
        "VC16028(a)-I",
    ]


def test_payment_options_keep_text_and_amount() -> None:
    detail = parse_select_response(load_fixture("select_26IN-055186.json"))

    assert len(detail.payment_options) == 1
    assert detail.payment_options[0].amount == Decimal("1665.00")
    assert detail.payment_options[0].text.startswith("Proof of Correction")


def test_payment_plan_offer_is_not_stored_when_the_case_has_no_plan() -> None:
    detail = parse_select_response(load_fixture("select_26IN-055186.json"))

    assert detail.payment_plan is None


def test_real_case_with_active_payment_plan_is_parsed() -> None:
    detail = parse_select_response(load_fixture("select_25IN-169374.json"))

    assert detail.full_name == "RODRIGUEZ, PEDRO"
    assert detail.has_payment_plan
    assert detail.payment_plan is not None
    assert detail.payment_plan.monthly_amount == Decimal("93")
    assert detail.payment_plan.past_amount_due == Decimal("0")
    assert detail.payment_plan.remaining_balance == Decimal("186.00")
    assert detail.is_extension_eligible
    assert detail.original_date == date(2026, 11, 13)
    assert detail.extended_date == date(2026, 12, 13)


def test_payment_plan_options_keep_their_codes() -> None:
    detail = parse_select_response(load_fixture("select_25IN-169374.json"))

    assert [option.code for option in detail.payment_options] == ["PPE", "PAYP", "PAYF", "PAYC"]
    assert detail.payment_options[0].amount == Decimal("0")


def test_plan_case_without_charges_falls_back_to_proof_of_correction_charges() -> None:
    detail = parse_select_response(load_fixture("select_25IN-169374.json"))

    assert detail.charges == ()
    assert [charge.statute for charge in detail.displayed_charges] == ["VC16028(a)-I"]


def test_expired_session_response_raises() -> None:
    with pytest.raises(PortalResponseError) as error:
        parse_select_response(load_fixture("select_session_expired.json"))

    assert error.value.is_session_expired


def test_response_without_case_number_is_malformed() -> None:
    payload = {"data": {"charges": []}, "result": 0, "message": ""}

    with pytest.raises(MalformedResponseError):
        parse_select_response(payload)
