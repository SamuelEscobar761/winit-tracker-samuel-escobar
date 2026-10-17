from datetime import date

from app.csv_import.models import ImportRow, RowIssue, RowIssueCode, RowStatus
from app.people.names import normalize_name

_PersonKey = tuple[str, str, date | None]


class DuplicateTracker:
    def __init__(self) -> None:
        self._first_line_by_key: dict[_PersonKey, int] = {}

    def check(self, row: ImportRow) -> ImportRow:
        if row.person is None:
            return row
        key = self._key_of(row)
        first_line = self._first_line_by_key.setdefault(key, row.line_number)
        if first_line == row.line_number:
            return row
        return self._as_duplicate(row, first_line)

    def _key_of(self, row: ImportRow) -> _PersonKey:
        assert row.person is not None
        person = row.person
        return (
            normalize_name(person.first_name),
            normalize_name(person.last_name),
            person.date_of_birth,
        )

    def _as_duplicate(self, row: ImportRow, first_line: int) -> ImportRow:
        issue = RowIssue(
            code=RowIssueCode.DUPLICATE,
            message=f"Same name and date of birth as line {first_line}",
        )
        return row.model_copy(
            update={
                "status": RowStatus.REJECTED,
                "person": None,
                "issues": (*row.issues, issue),
                "duplicate_of_line": first_line,
            }
        )
