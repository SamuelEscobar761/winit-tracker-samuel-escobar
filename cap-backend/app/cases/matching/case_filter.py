from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum

from app.cases.matching.caption import ParsedCaption, parse_caption
from app.cases.models import CaseSummary
from app.people.models import Person
from app.people.variants.forms import NameForms


class DiscardReason(StrEnum):
    NOT_A_PERSON = "not_a_person"
    LAST_NAME_MISMATCH = "last_name_mismatch"
    FIRST_NAME_MISMATCH = "first_name_mismatch"
    DATE_OF_BIRTH_MISMATCH = "date_of_birth_mismatch"


@dataclass(frozen=True)
class FilteredCases:
    kept: tuple[CaseSummary, ...]
    discarded_counts: Mapping[DiscardReason, int]

    @property
    def discarded_total(self) -> int:
        return sum(self.discarded_counts.values())


class PersonCaseFilter:
    def __init__(self, person: Person, name_forms: NameForms | None = None) -> None:
        self._person = person
        self._forms = name_forms or NameForms.exact(person)

    def apply(self, cases: Iterable[CaseSummary]) -> FilteredCases:
        kept: list[CaseSummary] = []
        discarded: Counter[DiscardReason] = Counter()
        for case in cases:
            reason = self.discard_reason(case)
            if reason is None:
                kept.append(case)
            else:
                discarded[reason] += 1
        return FilteredCases(kept=tuple(kept), discarded_counts=dict(discarded))

    def discard_reason(self, case: CaseSummary) -> DiscardReason | None:
        caption = parse_caption(case.caption)
        if caption is None:
            return DiscardReason.NOT_A_PERSON
        if caption.last_name not in self._forms.last_names:
            return DiscardReason.LAST_NAME_MISMATCH
        if not self._starts_with_first_names(caption):
            return DiscardReason.FIRST_NAME_MISMATCH
        if self._has_conflicting_birth_date(case):
            return DiscardReason.DATE_OF_BIRTH_MISMATCH
        return None

    def _starts_with_first_names(self, caption: ParsedCaption) -> bool:
        return any(
            caption.given_names[: len(prefix)] == prefix
            for prefix in self._forms.first_name_prefixes
        )

    def _has_conflicting_birth_date(self, case: CaseSummary) -> bool:
        expected = self._person.date_of_birth
        actual = case.date_of_birth
        return expected is not None and actual is not None and expected != actual
