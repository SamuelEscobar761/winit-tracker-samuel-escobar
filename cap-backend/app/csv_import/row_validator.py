from dataclasses import dataclass, field
from datetime import date

from app.csv_import.dates import BirthDateProblem, parse_birth_date
from app.csv_import.fields import clean_name_field, clean_reference
from app.csv_import.header import (
    DATE_OF_BIRTH,
    EXTERNAL_REF,
    FIRST_NAME,
    LAST_NAME,
    ColumnMap,
)
from app.csv_import.models import ImportRow, RowChange, RowIssue, RowIssueCode, RowStatus
from app.people.models import Person
from app.people.variants.config import NameVariantConfig
from app.people.variants.queries import generate_search_attempts

_WRONG_DELIMITER_MARKS = (";", "\t", "|")

_DATE_PROBLEM_ISSUES = {
    BirthDateProblem.INVALID: (RowIssueCode.INVALID_DATE, "The date of birth is not a real date"),
    BirthDateProblem.AMBIGUOUS: (
        RowIssueCode.AMBIGUOUS_DATE,
        "The date can be read as MM/DD/YYYY and DD/MM/YYYY; use YYYY-MM-DD",
    ),
    BirthDateProblem.OUT_OF_RANGE: (
        RowIssueCode.DATE_OUT_OF_RANGE,
        "The date of birth is before 1900 or in the future",
    ),
}


@dataclass
class _RowFindings:
    issues: list[RowIssue] = field(default_factory=list)
    changes: list[RowChange] = field(default_factory=list)

    def add_issue(self, code: RowIssueCode, message: str, field_name: str | None = None) -> None:
        self.issues.append(RowIssue(code=code, message=message, field=field_name))

    def add_change(self, field_name: str, before: str, after: str, reason: str) -> None:
        self.changes.append(RowChange(field=field_name, before=before, after=after, reason=reason))


class RowValidator:
    def __init__(self, variant_config: NameVariantConfig, today: date) -> None:
        self._variant_config = variant_config
        self._today = today

    def validate(self, line_number: int, fields: list[str], columns: ColumnMap) -> ImportRow:
        original = dict(zip(columns.raw_names, fields, strict=False))
        if len(fields) != len(columns.canonical_names):
            return self._rejected_for_column_count(line_number, fields, columns, original)
        cells = {
            name: value for name, value in zip(columns.canonical_names, fields, strict=True) if name
        }
        return self._validate_cells(line_number, cells, original)

    def _rejected_for_column_count(
        self, line_number: int, fields: list[str], columns: ColumnMap, original: dict[str, str]
    ) -> ImportRow:
        message = f"Expected {len(columns.canonical_names)} columns but found {len(fields)}"
        if any(mark in field_value for field_value in fields for mark in _WRONG_DELIMITER_MARKS):
            message += " (possible wrong delimiter)"
        issue = RowIssue(code=RowIssueCode.WRONG_COLUMN_COUNT, message=message)
        return ImportRow(
            line_number=line_number,
            status=RowStatus.REJECTED,
            original=original,
            issues=(issue,),
        )

    def _validate_cells(
        self, line_number: int, cells: dict[str, str], original: dict[str, str]
    ) -> ImportRow:
        findings = _RowFindings()
        first_name = self._read_name(cells.get(FIRST_NAME, ""), FIRST_NAME, findings)
        last_name = self._read_name(cells.get(LAST_NAME, ""), LAST_NAME, findings)
        birth_date = self._read_birth_date(cells.get(DATE_OF_BIRTH, ""), findings)
        person = self._build_person(first_name, last_name, birth_date, cells, findings)
        return self._to_row(line_number, original, person, findings)

    def _read_name(self, raw_value: str, field_name: str, findings: _RowFindings) -> str:
        cleaned = clean_name_field(raw_value)
        if not cleaned.value:
            code = (
                RowIssueCode.EMPTY_FIRST_NAME
                if field_name == FIRST_NAME
                else RowIssueCode.EMPTY_LAST_NAME
            )
            findings.add_issue(code, f"{field_name} is empty", field_name)
        elif cleaned.has_invalid_characters:
            message = f"{field_name} contains characters that are not letters"
            findings.add_issue(RowIssueCode.INVALID_CHARACTERS, message, field_name)
        elif cleaned.was_changed:
            reason = "Whitespace trimmed or collapsed"
            findings.add_change(field_name, raw_value, cleaned.value, reason)
        return cleaned.value

    def _read_birth_date(self, raw_value: str, findings: _RowFindings) -> date | None:
        result = parse_birth_date(raw_value, self._today)
        if result.problem is not None:
            code, message = _DATE_PROBLEM_ISSUES[result.problem]
            findings.add_issue(code, message, DATE_OF_BIRTH)
        elif result.was_reformatted and result.value is not None:
            reason = f"{result.note}; stored as ISO 8601"
            findings.add_change(DATE_OF_BIRTH, raw_value, result.value.isoformat(), reason)
        return result.value

    def _build_person(
        self,
        first_name: str,
        last_name: str,
        birth_date: date | None,
        cells: dict[str, str],
        findings: _RowFindings,
    ) -> Person | None:
        if findings.issues:
            return None
        person = Person(
            first_name=first_name,
            last_name=last_name,
            date_of_birth=birth_date,
            external_ref=clean_reference(cells.get(EXTERNAL_REF, "")),
        )
        if generate_search_attempts(person, self._variant_config):
            return person
        message = "No search text of 4 to 20 characters can be built from this name"
        findings.add_issue(RowIssueCode.NOT_SEARCHABLE, message)
        return None

    def _to_row(
        self,
        line_number: int,
        original: dict[str, str],
        person: Person | None,
        findings: _RowFindings,
    ) -> ImportRow:
        if person is None:
            status = RowStatus.REJECTED
        else:
            status = RowStatus.NORMALIZED if findings.changes else RowStatus.ACCEPTED
        return ImportRow(
            line_number=line_number,
            status=status,
            original=original,
            person=person,
            changes=tuple(findings.changes),
            issues=tuple(findings.issues),
        )
