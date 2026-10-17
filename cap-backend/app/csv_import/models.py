from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from app.people.models import Person


class RowStatus(StrEnum):
    ACCEPTED = "accepted"
    NORMALIZED = "normalized"
    REJECTED = "rejected"


class RowIssueCode(StrEnum):
    EMPTY_FIRST_NAME = "empty_first_name"
    EMPTY_LAST_NAME = "empty_last_name"
    INVALID_CHARACTERS = "invalid_characters"
    INVALID_DATE = "invalid_date"
    AMBIGUOUS_DATE = "ambiguous_date"
    DATE_OUT_OF_RANGE = "date_out_of_range"
    WRONG_COLUMN_COUNT = "wrong_column_count"
    MALFORMED_ROW = "malformed_row"
    NOT_SEARCHABLE = "not_searchable"
    DUPLICATE = "duplicate"


class FileIssueCode(StrEnum):
    EMPTY_FILE = "empty_file"
    FILE_TOO_LARGE = "file_too_large"
    BINARY_FILE = "binary_file"
    MISSING_REQUIRED_COLUMNS = "missing_required_columns"
    DUPLICATE_COLUMNS = "duplicate_columns"
    TOO_MANY_ROWS = "too_many_rows"
    NO_DATA_ROWS = "no_data_rows"
    DELIMITER_DETECTED = "delimiter_detected"
    ENCODING_FALLBACK = "encoding_fallback"
    UNKNOWN_COLUMNS_IGNORED = "unknown_columns_ignored"


class Severity(StrEnum):
    ERROR = "error"
    WARNING = "warning"


class RowIssue(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: RowIssueCode
    message: str
    field: str | None = None


class RowChange(BaseModel):
    model_config = ConfigDict(frozen=True)

    field: str
    before: str
    after: str
    reason: str


class FileIssue(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: FileIssueCode
    severity: Severity
    message: str


class ImportRow(BaseModel):
    model_config = ConfigDict(frozen=True)

    line_number: int
    status: RowStatus
    original: dict[str, str]
    person: Person | None = None
    changes: tuple[RowChange, ...] = ()
    issues: tuple[RowIssue, ...] = ()
    duplicate_of_line: int | None = None


class ImportReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    encoding: str | None = None
    delimiter: str | None = None
    rows: tuple[ImportRow, ...] = ()
    file_issues: tuple[FileIssue, ...] = ()

    @property
    def has_file_errors(self) -> bool:
        return any(issue.severity is Severity.ERROR for issue in self.file_issues)

    @property
    def queueable_rows(self) -> tuple[ImportRow, ...]:
        return tuple(row for row in self.rows if row.status is not RowStatus.REJECTED)

    @property
    def queueable_people(self) -> tuple[Person, ...]:
        return tuple(row.person for row in self.queueable_rows if row.person is not None)

    @property
    def counts_of_rejected(self) -> int:
        return self.counts[RowStatus.REJECTED]

    @property
    def counts(self) -> dict[RowStatus, int]:
        return {status: sum(1 for row in self.rows if row.status is status) for status in RowStatus}
