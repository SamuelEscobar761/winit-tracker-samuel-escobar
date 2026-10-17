import csv
from dataclasses import dataclass

from app.csv_import.decoding import CsvFileError, DecodedText, decode_csv_bytes
from app.csv_import.duplicates import DuplicateTracker
from app.csv_import.header import ColumnMap, build_column_map, detect_delimiter
from app.csv_import.models import (
    FileIssue,
    FileIssueCode,
    ImportReport,
    ImportRow,
    RowIssue,
    RowIssueCode,
    RowStatus,
    Severity,
)
from app.csv_import.row_validator import RowValidator

COMMENT_PREFIX = "#"

_NumberedLine = tuple[int, str]


@dataclass(frozen=True)
class _Layout:
    delimiter: str
    columns: ColumnMap
    data_lines: list[_NumberedLine]


class CsvImporter:
    def __init__(self, validator: RowValidator, max_bytes: int, max_rows: int) -> None:
        self._validator = validator
        self._max_bytes = max_bytes
        self._max_rows = max_rows

    def import_bytes(self, data: bytes) -> ImportReport:
        if len(data) > self._max_bytes:
            return _file_error(FileIssueCode.FILE_TOO_LARGE, "The file exceeds the size limit")
        try:
            decoded = decode_csv_bytes(data)
        except CsvFileError as error:
            return ImportReport(file_issues=(error.issue,))
        return self._import_text(decoded)

    def _import_text(self, decoded: DecodedText) -> ImportReport:
        issues = _encoding_issues(decoded)
        layout_or_issue = self._read_layout(_content_lines(decoded.text))
        if isinstance(layout_or_issue, FileIssue):
            return ImportReport(encoding=decoded.encoding, file_issues=(*issues, layout_or_issue))
        layout = layout_or_issue
        issues.extend(_layout_warnings(layout))
        return ImportReport(
            encoding=decoded.encoding,
            delimiter=layout.delimiter,
            rows=self._validate_rows(layout),
            file_issues=tuple(issues),
        )

    def _read_layout(self, lines: list[_NumberedLine]) -> _Layout | FileIssue:
        if not lines:
            return _issue(FileIssueCode.EMPTY_FILE, Severity.ERROR, "The file has no content")
        delimiter = detect_delimiter(lines[0][1])
        header_fields = next(csv.reader([lines[0][1]], delimiter=delimiter), [])
        columns = build_column_map(header_fields)
        problem = self._header_problem(columns, len(lines) - 1)
        if problem is not None:
            return problem
        return _Layout(delimiter, columns, lines[1:])

    def _header_problem(self, columns: ColumnMap, data_row_count: int) -> FileIssue | None:
        if columns.missing_required:
            names = ", ".join(columns.missing_required)
            message = f"Missing required columns: {names}"
            return _issue(FileIssueCode.MISSING_REQUIRED_COLUMNS, Severity.ERROR, message)
        if columns.has_duplicates:
            message = "The header repeats a column"
            return _issue(FileIssueCode.DUPLICATE_COLUMNS, Severity.ERROR, message)
        if data_row_count == 0:
            return _issue(FileIssueCode.NO_DATA_ROWS, Severity.ERROR, "The file has no data rows")
        if data_row_count > self._max_rows:
            message = f"The file has {data_row_count} rows; the limit is {self._max_rows}"
            return _issue(FileIssueCode.TOO_MANY_ROWS, Severity.ERROR, message)
        return None

    def _validate_rows(self, layout: _Layout) -> tuple[ImportRow, ...]:
        tracker = DuplicateTracker()
        rows = (self._validate_line(number, line, layout) for number, line in layout.data_lines)
        return tuple(tracker.check(row) for row in rows)

    def _validate_line(self, line_number: int, line: str, layout: _Layout) -> ImportRow:
        try:
            fields = next(csv.reader([line], delimiter=layout.delimiter), [])
        except csv.Error as error:
            return _malformed_row(line_number, line, str(error))
        return self._validator.validate(line_number, fields, layout.columns)


def _content_lines(text: str) -> list[_NumberedLine]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    numbered = enumerate(normalized.split("\n"), start=1)
    return [(number, line) for number, line in numbered if _is_content(line)]


def _is_content(line: str) -> bool:
    stripped = line.strip()
    return bool(stripped) and not stripped.startswith(COMMENT_PREFIX)


def _encoding_issues(decoded: DecodedText) -> list[FileIssue]:
    if not decoded.used_fallback:
        return []
    message = "The file is not valid UTF-8; it was read as latin-1"
    return [_issue(FileIssueCode.ENCODING_FALLBACK, Severity.WARNING, message)]


def _layout_warnings(layout: _Layout) -> list[FileIssue]:
    warnings: list[FileIssue] = []
    if layout.delimiter != ",":
        message = f"Delimiter {layout.delimiter!r} was detected instead of a comma"
        warnings.append(_issue(FileIssueCode.DELIMITER_DETECTED, Severity.WARNING, message))
    if layout.columns.unknown_columns:
        names = ", ".join(layout.columns.unknown_columns)
        message = f"Ignored unknown columns: {names}"
        warnings.append(_issue(FileIssueCode.UNKNOWN_COLUMNS_IGNORED, Severity.WARNING, message))
    return warnings


def _malformed_row(line_number: int, line: str, detail: str) -> ImportRow:
    issue = RowIssue(code=RowIssueCode.MALFORMED_ROW, message=f"The row cannot be read: {detail}")
    return ImportRow(
        line_number=line_number,
        status=RowStatus.REJECTED,
        original={"line": line},
        issues=(issue,),
    )


def _issue(code: FileIssueCode, severity: Severity, message: str) -> FileIssue:
    return FileIssue(code=code, severity=severity, message=message)


def _file_error(code: FileIssueCode, message: str) -> ImportReport:
    return ImportReport(file_issues=(_issue(code, Severity.ERROR, message),))
