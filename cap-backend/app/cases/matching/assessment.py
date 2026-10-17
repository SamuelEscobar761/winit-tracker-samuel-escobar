from dataclasses import dataclass
from enum import StrEnum

from app.cases.matching.caption import parse_caption
from app.cases.models import CaseSummary
from app.people.models import Person
from app.people.names import normalize_name


class MatchLabel(StrEnum):
    CONFIRMED = "confirmed"
    PROBABLE = "probable"
    POSSIBLE = "possible"
    UNLIKELY = "unlikely"


@dataclass(frozen=True)
class MatchAssessment:
    label: MatchLabel
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class AssessedCase:
    case: CaseSummary
    assessment: MatchAssessment


def assess_case(person: Person, case: CaseSummary) -> MatchAssessment:
    assessment = _assess_by_birth_date(person, case)
    if not _is_variant_match(person, case):
        return assessment
    return _downgrade_for_variant(assessment)


def _assess_by_birth_date(person: Person, case: CaseSummary) -> MatchAssessment:
    """Without a date of birth in the CSV a case can never be confirmed."""
    if person.date_of_birth is None:
        return MatchAssessment(MatchLabel.POSSIBLE, ("The CSV row has no date of birth",))
    if case.date_of_birth is None:
        return _assess_without_record_birth_date(person, case)
    if case.date_of_birth == person.date_of_birth:
        return MatchAssessment(MatchLabel.CONFIRMED, ("Name and date of birth match",))
    return MatchAssessment(MatchLabel.UNLIKELY, ("The date of birth differs",))


def _assess_without_record_birth_date(person: Person, case: CaseSummary) -> MatchAssessment:
    reason = "The case record has no date of birth"
    if _has_exact_given_names(person, case):
        return MatchAssessment(MatchLabel.PROBABLE, (reason, "Given names match exactly"))
    return MatchAssessment(MatchLabel.POSSIBLE, (reason, "The caption has extra given names"))


def _is_variant_match(person: Person, case: CaseSummary) -> bool:
    caption = parse_caption(case.caption)
    if caption is None:
        return False
    first_names = tuple(normalize_name(person.first_name).split())
    written_last_name = normalize_name(person.last_name)
    return (
        caption.last_name != written_last_name
        or caption.given_names[: len(first_names)] != first_names
    )


_DOWNGRADED_LABELS = {
    MatchLabel.CONFIRMED: MatchLabel.PROBABLE,
    MatchLabel.PROBABLE: MatchLabel.POSSIBLE,
}


def _downgrade_for_variant(assessment: MatchAssessment) -> MatchAssessment:
    label = _DOWNGRADED_LABELS.get(assessment.label, assessment.label)
    return MatchAssessment(label, (*assessment.reasons, "Matched through a name variant"))


def _has_exact_given_names(person: Person, case: CaseSummary) -> bool:
    caption = parse_caption(case.caption)
    expected = tuple(normalize_name(person.first_name).split())
    return caption is not None and caption.given_names == expected
