from datetime import date

from app.cases.matching.assessment import MatchLabel, assess_case
from tests.support.builders import make_case, make_person

BIRTH_DATE = date(1978, 7, 24)


def test_without_csv_birth_date_a_case_is_never_confirmed() -> None:
    assessment = assess_case(make_person(), make_case(date_of_birth=BIRTH_DATE))

    assert assessment.label is MatchLabel.POSSIBLE
    assert assessment.reasons


def test_matching_birth_date_confirms_the_case() -> None:
    person = make_person(date_of_birth=BIRTH_DATE)

    assessment = assess_case(person, make_case(date_of_birth=BIRTH_DATE))

    assert assessment.label is MatchLabel.CONFIRMED


def test_record_without_birth_date_and_exact_given_names_is_probable() -> None:
    person = make_person(date_of_birth=BIRTH_DATE)

    assessment = assess_case(person, make_case(caption="SMITH, JOHN"))

    assert assessment.label is MatchLabel.PROBABLE


def test_record_without_birth_date_and_extra_given_names_is_only_possible() -> None:
    person = make_person(date_of_birth=BIRTH_DATE)

    assessment = assess_case(person, make_case(caption="SMITH, JOHN MICHAEL"))

    assert assessment.label is MatchLabel.POSSIBLE


def test_different_birth_date_is_unlikely() -> None:
    person = make_person(date_of_birth=BIRTH_DATE)

    assessment = assess_case(person, make_case(date_of_birth=date(1959, 10, 19)))

    assert assessment.label is MatchLabel.UNLIKELY
