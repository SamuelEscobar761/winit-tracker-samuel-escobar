from datetime import date
from decimal import Decimal

import pytest

from app.cases.keys import build_case_key
from app.cases.status import CaseStatus, parse_case_status
from app.cases.values import clean_drivers_license, parse_amount, parse_portal_date

KNOWN_PORTAL_STATUSES = [status.value for status in CaseStatus if status is not CaseStatus.UNKNOWN]


def test_portal_dates_are_parsed_to_dates() -> None:
    assert parse_portal_date("1/8/1995") == date(1995, 1, 8)
    assert parse_portal_date("10/16/2026") == date(2026, 10, 16)


@pytest.mark.parametrize("raw_date", [None, "", "  ", "31/02/1990", "2/30/2001", "not a date"])
def test_missing_or_invalid_dates_become_none(raw_date: str | None) -> None:
    assert parse_portal_date(raw_date) is None


def test_amounts_accept_thousand_separators_and_numbers() -> None:
    assert parse_amount("1,665.00") == Decimal("1665.00")
    assert parse_amount(93) == Decimal("93")
    assert parse_amount(None) is None
    assert parse_amount("n/a") is None


@pytest.mark.parametrize(
    "placeholder", ["", "UNKNOWN", "UNK", "NIP", "NONE", "A0000000", "0000000", None]
)
def test_license_placeholders_become_none(placeholder: str | None) -> None:
    assert clean_drivers_license(placeholder) is None


def test_real_licenses_are_kept_uppercase() -> None:
    assert clean_drivers_license(" d5878000 ") == "D5878000"


def test_case_key_ignores_hyphens_spaces_and_case() -> None:
    assert build_case_key("25IN-169374") == build_case_key("25in169374") == "25IN169374"


@pytest.mark.parametrize("portal_text", KNOWN_PORTAL_STATUSES)
def test_every_portal_status_is_recognized(portal_text: str) -> None:
    assert parse_case_status(portal_text).value == portal_text


def test_unexpected_status_is_unknown() -> None:
    assert parse_case_status("Something New") is CaseStatus.UNKNOWN
    assert parse_case_status(None) is CaseStatus.UNKNOWN
