from collections import Counter
from datetime import date

from app.cases.matching.analyzer import analyze_person_cases
from app.cases.matching.assessment import MatchLabel
from app.cases.matching.case_filter import DiscardReason
from app.cases.models import CaseSummary
from app.cases.parsing.search_parser import parse_search_response
from tests.support.builders import make_person
from tests.support.fixtures import load_fixture


def load_cases(fixture_name: str) -> list[CaseSummary]:
    return parse_search_response(load_fixture(fixture_name))


def test_john_smith_without_birth_date_keeps_every_homonym_as_possible() -> None:
    analysis = analyze_person_cases(make_person(), load_cases("search_john_smith.json"))

    assert len(analysis.cases) == 224
    assert analysis.discarded_counts[DiscardReason.LAST_NAME_MISMATCH] == 59
    assert analysis.discarded_counts[DiscardReason.NOT_A_PERSON] == 3
    assert {assessed.assessment.label for assessed in analysis.cases} == {MatchLabel.POSSIBLE}


def test_john_smith_cases_split_into_many_possible_identities() -> None:
    analysis = analyze_person_cases(make_person(), load_cases("search_john_smith.json"))

    assert len(analysis.identity_groups) > 100
    assert analysis.identity_groups[0].case_count == 13


def test_john_smith_with_birth_date_keeps_only_that_person() -> None:
    person = make_person(date_of_birth=date(1959, 10, 19))

    analysis = analyze_person_cases(person, load_cases("search_john_smith.json"))

    labels = Counter(assessed.assessment.label for assessed in analysis.cases)
    assert len(analysis.cases) == 19
    assert labels[MatchLabel.CONFIRMED] == 13
    assert analysis.discarded_counts[DiscardReason.DATE_OF_BIRTH_MISMATCH] == 205


def test_pedro_rodriguez_discards_other_last_names_and_businesses() -> None:
    person = make_person("Pedro", "Rodriguez")

    analysis = analyze_person_cases(person, load_cases("search_pedro_rodriguez.json"))

    assert len(analysis.cases) == 188
    assert analysis.discarded_total == 5


def test_pedro_rodriguez_with_birth_date_keeps_only_that_person() -> None:
    person = make_person("Pedro", "Rodriguez", date(1985, 8, 30))

    analysis = analyze_person_cases(person, load_cases("search_pedro_rodriguez.json"))

    labels = Counter(assessed.assessment.label for assessed in analysis.cases)
    assert len(analysis.cases) == 10
    assert labels[MatchLabel.CONFIRMED] == 8
    assert labels[MatchLabel.PROBABLE] == 2
