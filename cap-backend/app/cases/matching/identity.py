from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from app.cases.matching.assessment import AssessedCase


@dataclass(frozen=True)
class IdentityGroup:
    date_of_birth: date | None
    drivers_license: str | None
    cases: tuple[AssessedCase, ...]

    @property
    def case_count(self) -> int:
        return len(self.cases)


_GroupKey = tuple[date | None, str | None]


def group_by_identity(assessed_cases: Sequence[AssessedCase]) -> tuple[IdentityGroup, ...]:
    grouped = _group_by_birth_date_and_license(assessed_cases)
    merged = _attach_unlicensed_cases(grouped)
    groups = [IdentityGroup(key[0], key[1], tuple(cases)) for key, cases in merged.items()]
    return tuple(sorted(groups, key=_sort_key))


def _group_by_birth_date_and_license(
    assessed_cases: Sequence[AssessedCase],
) -> dict[_GroupKey, list[AssessedCase]]:
    grouped: dict[_GroupKey, list[AssessedCase]] = defaultdict(list)
    for assessed in assessed_cases:
        grouped[(assessed.case.date_of_birth, assessed.case.drivers_license)].append(assessed)
    return grouped


def _attach_unlicensed_cases(
    grouped: dict[_GroupKey, list[AssessedCase]],
) -> dict[_GroupKey, list[AssessedCase]]:
    """A blank license is common, so it joins the only licensed group of the same birth date."""
    merged: dict[_GroupKey, list[AssessedCase]] = {}
    for key, cases in grouped.items():
        target = _single_licensed_sibling(grouped, key) if key[1] is None else key
        merged.setdefault(target, []).extend(cases)
    return merged


def _single_licensed_sibling(
    grouped: dict[_GroupKey, list[AssessedCase]], key: _GroupKey
) -> _GroupKey:
    siblings = [other for other in grouped if other[0] == key[0] and other[1] is not None]
    return siblings[0] if len(siblings) == 1 and key[0] is not None else key


def _sort_key(group: IdentityGroup) -> tuple[int, int, date]:
    has_birth_date = group.date_of_birth is not None
    return (-group.case_count, 0 if has_birth_date else 1, group.date_of_birth or date.min)
