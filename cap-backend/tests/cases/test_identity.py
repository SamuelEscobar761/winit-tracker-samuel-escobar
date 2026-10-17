from datetime import date

from app.cases.matching.assessment import AssessedCase, MatchAssessment, MatchLabel
from app.cases.matching.identity import group_by_identity
from app.cases.models import CaseSummary
from tests.support.builders import make_case

FIRST_BIRTH_DATE = date(1978, 7, 24)
SECOND_BIRTH_DATE = date(1959, 10, 19)


def assess(case: CaseSummary) -> AssessedCase:
    return AssessedCase(case, MatchAssessment(MatchLabel.POSSIBLE, ()))


def test_cases_with_different_birth_dates_form_different_groups() -> None:
    groups = group_by_identity(
        [
            assess(make_case(date_of_birth=FIRST_BIRTH_DATE)),
            assess(make_case(date_of_birth=SECOND_BIRTH_DATE)),
            assess(make_case(date_of_birth=SECOND_BIRTH_DATE)),
        ]
    )

    assert [group.date_of_birth for group in groups] == [SECOND_BIRTH_DATE, FIRST_BIRTH_DATE]
    assert [group.case_count for group in groups] == [2, 1]


def test_blank_license_joins_the_only_licensed_group_of_the_same_birth_date() -> None:
    groups = group_by_identity(
        [
            assess(make_case(date_of_birth=FIRST_BIRTH_DATE, drivers_license="D5878000")),
            assess(make_case(date_of_birth=FIRST_BIRTH_DATE, drivers_license=None)),
        ]
    )

    assert len(groups) == 1
    assert groups[0].drivers_license == "D5878000"
    assert groups[0].case_count == 2


def test_two_different_licenses_on_one_birth_date_stay_separate() -> None:
    groups = group_by_identity(
        [
            assess(make_case(date_of_birth=FIRST_BIRTH_DATE, drivers_license="D5878000")),
            assess(make_case(date_of_birth=FIRST_BIRTH_DATE, drivers_license="A6075650")),
            assess(make_case(date_of_birth=FIRST_BIRTH_DATE, drivers_license=None)),
        ]
    )

    assert len(groups) == 3


def test_cases_without_birth_date_form_their_own_group_sorted_after_dated_ones() -> None:
    groups = group_by_identity(
        [
            assess(make_case(date_of_birth=None)),
            assess(make_case(date_of_birth=None)),
            assess(make_case(date_of_birth=FIRST_BIRTH_DATE)),
        ]
    )

    assert groups[0].date_of_birth is None
    assert groups[0].case_count == 2
    assert groups[1].date_of_birth == FIRST_BIRTH_DATE


def test_no_cases_give_no_groups() -> None:
    assert group_by_identity([]) == ()
