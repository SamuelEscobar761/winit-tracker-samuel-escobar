from datetime import date

import pytest

from app.cases.matching.case_filter import DiscardReason, PersonCaseFilter
from tests.support.builders import make_case, make_person


@pytest.mark.parametrize(
    "caption",
    ["SMITH, JOHN", "SMITH, JOHN MICHAEL", "Smith, John", "SMITH,JOHN A"],
)
def test_middle_names_and_casing_do_not_prevent_a_match(caption: str) -> None:
    case_filter = PersonCaseFilter(make_person())

    assert case_filter.discard_reason(make_case(caption=caption)) is None


@pytest.mark.parametrize(
    ("caption", "reason"),
    [
        ("ROBERTSON'S READY MIX", DiscardReason.NOT_A_PERSON),
        ("Bam Bam", DiscardReason.NOT_A_PERSON),
        ("JONES, TIMOTHY SCOTT", DiscardReason.LAST_NAME_MISMATCH),
        ("SMITHSON, JOHN", DiscardReason.LAST_NAME_MISMATCH),
        ("SMITH, JOHNNY", DiscardReason.FIRST_NAME_MISMATCH),
        ("SMITH, MARY JOHN", DiscardReason.FIRST_NAME_MISMATCH),
    ],
)
def test_other_people_and_businesses_are_discarded(caption: str, reason: DiscardReason) -> None:
    case_filter = PersonCaseFilter(make_person())

    assert case_filter.discard_reason(make_case(caption=caption)) is reason


def test_accents_in_the_csv_still_match_accent_free_records() -> None:
    case_filter = PersonCaseFilter(make_person("Pedro", "Rodríguez"))

    assert case_filter.discard_reason(make_case(caption="RODRIGUEZ, PEDRO LUIS")) is None


def test_a_person_whose_last_name_appears_as_a_middle_name_is_discarded() -> None:
    case_filter = PersonCaseFilter(make_person("Pedro", "Rodriguez"))

    assert (
        case_filter.discard_reason(make_case(caption="ROMERO, PEDRO RODRIGUEZ"))
        is DiscardReason.LAST_NAME_MISMATCH
    )


def test_different_birth_date_is_discarded_when_both_sides_have_one() -> None:
    case_filter = PersonCaseFilter(make_person(date_of_birth=date(1978, 7, 24)))

    different = make_case(date_of_birth=date(1959, 10, 19))
    same = make_case(date_of_birth=date(1978, 7, 24))
    missing = make_case(date_of_birth=None)

    assert case_filter.discard_reason(different) is DiscardReason.DATE_OF_BIRTH_MISMATCH
    assert case_filter.discard_reason(same) is None
    assert case_filter.discard_reason(missing) is None


def test_birth_dates_are_ignored_when_the_csv_has_none() -> None:
    case_filter = PersonCaseFilter(make_person())

    assert case_filter.discard_reason(make_case(date_of_birth=date(1959, 10, 19))) is None


def test_apply_keeps_matches_and_counts_discards_by_reason() -> None:
    cases = [
        make_case(caption="SMITH, JOHN"),
        make_case(caption="JONES, TIM"),
        make_case(caption="GREEN, GEROLD"),
        make_case(caption="Bam Bam"),
    ]

    result = PersonCaseFilter(make_person()).apply(cases)

    assert len(result.kept) == 1
    assert result.discarded_total == 3
    assert result.discarded_counts[DiscardReason.LAST_NAME_MISMATCH] == 2
    assert result.discarded_counts[DiscardReason.NOT_A_PERSON] == 1
