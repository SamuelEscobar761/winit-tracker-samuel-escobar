import re
from dataclasses import dataclass
from datetime import date
from enum import StrEnum

MIN_BIRTH_YEAR = 1900

_ISO_DATE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
_SLASHED_DATE = re.compile(r"^(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})$")


class BirthDateProblem(StrEnum):
    INVALID = "invalid"
    AMBIGUOUS = "ambiguous"
    OUT_OF_RANGE = "out_of_range"


@dataclass(frozen=True)
class BirthDateResult:
    value: date | None
    problem: BirthDateProblem | None = None
    was_reformatted: bool = False
    note: str | None = None


def parse_birth_date(raw_date: str, today: date) -> BirthDateResult:
    """Slashed dates are read as MM/DD/YYYY or DD/MM/YYYY only when one reading is impossible."""
    text = raw_date.strip()
    if not text:
        return BirthDateResult(value=None)
    parsed = (
        _parse_iso(text) or _parse_slashed(text) or BirthDateResult(None, BirthDateProblem.INVALID)
    )
    return _check_range(parsed, today)


def _parse_iso(text: str) -> BirthDateResult | None:
    match = _ISO_DATE.match(text)
    if match is None:
        return None
    year, month, day = (int(group) for group in match.groups())
    value = _build_date(year, month, day)
    if value is None:
        return BirthDateResult(None, BirthDateProblem.INVALID)
    return BirthDateResult(value)


def _parse_slashed(text: str) -> BirthDateResult | None:
    match = _SLASHED_DATE.match(text)
    if match is None:
        return None
    first, second, year = (int(group) for group in match.groups())
    month_first = _build_date(year, first, second)
    day_first = _build_date(year, second, first)
    return _choose_reading(month_first, day_first)


def _choose_reading(month_first: date | None, day_first: date | None) -> BirthDateResult:
    if month_first is not None and day_first is not None and month_first != day_first:
        return BirthDateResult(None, BirthDateProblem.AMBIGUOUS)
    if month_first is not None:
        return BirthDateResult(month_first, was_reformatted=True, note="Read as MM/DD/YYYY")
    if day_first is not None:
        return BirthDateResult(day_first, was_reformatted=True, note="Read as DD/MM/YYYY")
    return BirthDateResult(None, BirthDateProblem.INVALID)


def _check_range(result: BirthDateResult, today: date) -> BirthDateResult:
    value = result.value
    if value is None or (value.year >= MIN_BIRTH_YEAR and value <= today):
        return result
    return BirthDateResult(None, BirthDateProblem.OUT_OF_RANGE)


def _build_date(year: int, month: int, day: int) -> date | None:
    try:
        return date(year, month, day)
    except ValueError:
        return None
