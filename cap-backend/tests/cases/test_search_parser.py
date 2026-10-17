from collections import Counter
from datetime import date

import pytest

from app.cases.models import CaseSummary
from app.cases.parsing.errors import MalformedResponseError, PortalResponseError
from app.cases.parsing.search_parser import parse_search_response
from app.cases.status import CaseStatus
from tests.support.fixtures import load_fixture


def parse_pedro_cases() -> dict[str, CaseSummary]:
    cases = parse_search_response(load_fixture("search_pedro_rodriguez.json"))
    return {case.case_number: case for case in cases}


def test_pedro_rodriguez_search_is_fully_parsed() -> None:
    cases = parse_search_response(load_fixture("search_pedro_rodriguez.json"))

    assert len(cases) == 193
    assert Counter(case.status for case in cases)[CaseStatus.WARRANT] == 28


def test_john_smith_search_is_fully_parsed() -> None:
    cases = parse_search_response(load_fixture("search_john_smith.json"))

    assert len(cases) == 286
    assert CaseStatus.UNKNOWN not in {case.status for case in cases}


def test_case_fields_are_mapped_and_normalized() -> None:
    case = parse_pedro_cases()["000711MAPR"]

    assert case.caption == "RODRIGUEZ, PEDRO"
    assert case.file_date == date(2003, 8, 20)
    assert case.date_of_birth == date(1954, 5, 22)
    assert case.drivers_license == "C5763389"
    assert case.status is CaseStatus.CLOSED


def test_placeholder_license_and_empty_birth_date_become_none() -> None:
    by_number = parse_pedro_cases()

    assert by_number["016057PR"].drivers_license is None
    assert by_number["371943PR"].date_of_birth is None


def test_warrant_cases_are_restricted_and_not_detail_eligible() -> None:
    cases = parse_pedro_cases().values()
    warrant = next(case for case in cases if case.status is CaseStatus.WARRANT)
    closed = next(case for case in cases if case.status is CaseStatus.CLOSED)

    assert warrant.is_restricted
    assert warrant.public_status_label == "Restricted by portal"
    assert not warrant.is_detail_eligible
    assert not closed.is_detail_eligible
    assert closed.public_status_label == "Closed"


def test_failed_portal_result_raises_with_message() -> None:
    payload = {"data": [], "result": 1, "message": "Traffic Payment Session Expired."}

    with pytest.raises(PortalResponseError) as error:
        parse_search_response(payload)

    assert error.value.is_session_expired


def test_no_results_message_is_recognized() -> None:
    with pytest.raises(PortalResponseError) as error:
        parse_search_response({"data": None, "result": 1, "message": "No Case(s) Found"})

    assert error.value.is_no_results


def test_data_that_is_not_a_list_is_malformed() -> None:
    with pytest.raises(MalformedResponseError):
        parse_search_response({"data": {}, "result": 0, "message": ""})


def test_item_without_case_number_is_malformed() -> None:
    payload = {"data": [{"caseId": "1", "caseCaption": "SMITH, JOHN"}], "result": 0}

    with pytest.raises(MalformedResponseError):
        parse_search_response(payload)


def test_numeric_identifiers_are_accepted() -> None:
    payload = {"data": [{"caseId": 7, "caseNumber": "25IN-1", "caseStatus": "Active"}], "result": 0}

    cases = parse_search_response(payload)

    assert cases[0].portal_case_id == "7"
