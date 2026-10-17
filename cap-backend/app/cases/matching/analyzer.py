from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from app.cases.matching.assessment import AssessedCase, assess_case
from app.cases.matching.case_filter import DiscardReason, PersonCaseFilter
from app.cases.matching.identity import IdentityGroup, group_by_identity
from app.cases.models import CaseSummary
from app.people.models import Person
from app.people.variants.forms import NameForms


@dataclass(frozen=True)
class PersonCaseAnalysis:
    cases: tuple[AssessedCase, ...]
    identity_groups: tuple[IdentityGroup, ...]
    discarded_counts: Mapping[DiscardReason, int]

    @property
    def discarded_total(self) -> int:
        return sum(self.discarded_counts.values())


def limit_cases(analysis: PersonCaseAnalysis, max_cases: int) -> tuple[PersonCaseAnalysis, bool]:
    if len(analysis.cases) <= max_cases:
        return analysis, False
    kept = analysis.cases[:max_cases]
    limited = PersonCaseAnalysis(
        cases=kept,
        identity_groups=group_by_identity(kept),
        discarded_counts=analysis.discarded_counts,
    )
    return limited, True


def analyze_person_cases(
    person: Person,
    summaries: Iterable[CaseSummary],
    name_forms: NameForms | None = None,
) -> PersonCaseAnalysis:
    filtered = PersonCaseFilter(person, name_forms).apply(summaries)
    assessed = tuple(AssessedCase(case, assess_case(person, case)) for case in filtered.kept)
    return PersonCaseAnalysis(
        cases=assessed,
        identity_groups=group_by_identity(assessed),
        discarded_counts=filtered.discarded_counts,
    )
