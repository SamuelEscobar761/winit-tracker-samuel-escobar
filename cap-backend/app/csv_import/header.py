import csv
import re
from dataclasses import dataclass

FIRST_NAME = "first_name"
LAST_NAME = "last_name"
DATE_OF_BIRTH = "date_of_birth"
EXTERNAL_REF = "external_ref"

REQUIRED_COLUMNS = (FIRST_NAME, LAST_NAME)
CANDIDATE_DELIMITERS = (",", ";", "\t", "|")

_COLUMN_ALIASES = {
    "firstname": FIRST_NAME,
    "lastname": LAST_NAME,
    "dateofbirth": DATE_OF_BIRTH,
    "dob": DATE_OF_BIRTH,
    "externalref": EXTERNAL_REF,
    "externalreference": EXTERNAL_REF,
}
_NON_LETTERS = re.compile(r"[^a-z]")


@dataclass(frozen=True)
class ColumnMap:
    canonical_names: tuple[str | None, ...]
    raw_names: tuple[str, ...]

    @property
    def unknown_columns(self) -> tuple[str, ...]:
        pairs = zip(self.canonical_names, self.raw_names, strict=True)
        return tuple(raw for canonical, raw in pairs if canonical is None)

    @property
    def missing_required(self) -> tuple[str, ...]:
        return tuple(name for name in REQUIRED_COLUMNS if name not in self.canonical_names)

    @property
    def has_duplicates(self) -> bool:
        known = [name for name in self.canonical_names if name is not None]
        return len(known) != len(set(known))


def canonical_column(raw_name: str) -> str | None:
    letters = _NON_LETTERS.sub("", raw_name.lower())
    return _COLUMN_ALIASES.get(letters)


def build_column_map(raw_names: list[str]) -> ColumnMap:
    return ColumnMap(
        canonical_names=tuple(canonical_column(name) for name in raw_names),
        raw_names=tuple(name.strip() for name in raw_names),
    )


def detect_delimiter(header_line: str) -> str:
    """The first delimiter that yields both required columns wins, comma first."""
    for delimiter in CANDIDATE_DELIMITERS:
        names = next(csv.reader([header_line], delimiter=delimiter), [])
        if not build_column_map(names).missing_required:
            return delimiter
    return ","
