from datetime import date
from pathlib import Path

import pytest

from app.csv_import.importer import CsvImporter
from app.csv_import.models import (
    FileIssueCode,
    ImportReport,
    ImportRow,
    RowIssueCode,
    RowStatus,
)
from app.csv_import.row_validator import RowValidator
from app.people.variants.config import load_name_variant_config

TODAY = date(2026, 10, 16)
VARIANTS_FILE = Path(__file__).resolve().parents[2] / "config" / "name_variants.json"

BRIEF_SAMPLE = (
    "first_name,last_name,date_of_birth,external_ref\n"
    "John,Smith,,DRV-1001\n"
    "Pedro,Rodriguez,,DRV-1002\n"
    "# your validator must reject or flag the rows below gracefully\n"
    ",Smith,,DRV-1003\n"
    "Pedro;Rodriguez,,DRV-1004\n"
    "J0hn,Smith,31/02/1990,DRV-1005\n"
)
HEADER = "first_name,last_name,date_of_birth,external_ref\n"


def build_importer(max_bytes: int = 100_000, max_rows: int = 1000) -> CsvImporter:
    validator = RowValidator(load_name_variant_config(VARIANTS_FILE), TODAY)
    return CsvImporter(validator, max_bytes, max_rows)


def import_text(text: str, **limits: int) -> ImportReport:
    return build_importer(**limits).import_bytes(text.encode("utf-8"))


def row_at(report: ImportReport, line_number: int) -> ImportRow:
    return next(row for row in report.rows if row.line_number == line_number)


def issue_codes(row: ImportRow) -> set[RowIssueCode]:
    return {issue.code for issue in row.issues}


def file_issue_codes(report: ImportReport) -> set[FileIssueCode]:
    return {issue.code for issue in report.file_issues}


def test_brief_sample_accepts_good_rows_and_rejects_the_bad_ones() -> None:
    report = import_text(BRIEF_SAMPLE)

    assert [row.status for row in report.rows] == [
        RowStatus.ACCEPTED,
        RowStatus.ACCEPTED,
        RowStatus.REJECTED,
        RowStatus.REJECTED,
        RowStatus.REJECTED,
    ]
    assert not report.has_file_errors


def test_comment_lines_are_skipped_and_line_numbers_are_kept() -> None:
    report = import_text(BRIEF_SAMPLE)

    assert [row.line_number for row in report.rows] == [2, 3, 5, 6, 7]


def test_empty_first_name_is_rejected_with_its_reason() -> None:
    row = row_at(import_text(BRIEF_SAMPLE), 5)

    assert row.status is RowStatus.REJECTED
    assert issue_codes(row) == {RowIssueCode.EMPTY_FIRST_NAME}
    assert row.person is None


def test_wrong_delimiter_inside_a_row_is_reported_as_column_count() -> None:
    row = row_at(import_text(BRIEF_SAMPLE), 6)

    assert issue_codes(row) == {RowIssueCode.WRONG_COLUMN_COUNT}
    assert "possible wrong delimiter" in row.issues[0].message


def test_digits_in_a_name_and_an_impossible_date_are_both_reported() -> None:
    row = row_at(import_text(BRIEF_SAMPLE), 7)

    assert issue_codes(row) == {RowIssueCode.INVALID_CHARACTERS, RowIssueCode.INVALID_DATE}


def test_only_accepted_and_normalized_rows_are_queueable() -> None:
    report = import_text(BRIEF_SAMPLE)

    assert [person.last_name for person in report.queueable_people] == ["Smith", "Rodriguez"]
    assert report.counts[RowStatus.REJECTED] == 3


def test_blank_lines_are_ignored() -> None:
    report = import_text(HEADER + "\n\nJohn,Smith,,DRV-1\n\n")

    assert len(report.rows) == 1


def test_surrounding_whitespace_normalizes_the_row_and_lists_the_change() -> None:
    report = import_text(HEADER + "  John  ,Smith,,DRV-1\n")
    row = report.rows[0]

    assert row.status is RowStatus.NORMALIZED
    assert row.person is not None
    assert row.person.first_name == "John"
    assert row.changes[0].field == "first_name"
    assert row.changes[0].before == "  John  "


def test_slashed_birth_date_is_normalized_to_iso_with_a_note() -> None:
    row = import_text(HEADER + "John,Smith,24/07/1978,DRV-1\n").rows[0]

    assert row.status is RowStatus.NORMALIZED
    assert row.person is not None
    assert row.person.date_of_birth == date(1978, 7, 24)
    assert "DD/MM/YYYY" in row.changes[0].reason


def test_ambiguous_birth_date_is_rejected() -> None:
    row = import_text(HEADER + "John,Smith,03/04/1990,DRV-1\n").rows[0]

    assert issue_codes(row) == {RowIssueCode.AMBIGUOUS_DATE}


def test_future_birth_date_is_rejected() -> None:
    row = import_text(HEADER + "John,Smith,2999-01-01,DRV-1\n").rows[0]

    assert issue_codes(row) == {RowIssueCode.DATE_OUT_OF_RANGE}


def test_external_reference_is_optional() -> None:
    report = import_text("first_name,last_name\nJohn,Smith\n")

    assert report.rows[0].status is RowStatus.ACCEPTED
    assert report.rows[0].person is not None
    assert report.rows[0].person.external_ref is None


def test_header_names_are_matched_loosely_and_unknown_columns_are_ignored() -> None:
    report = import_text("Last Name,First-Name,DOB,Notes\nSmith,John,1978-07-24,vip\n")

    assert report.rows[0].status is RowStatus.ACCEPTED
    assert FileIssueCode.UNKNOWN_COLUMNS_IGNORED in file_issue_codes(report)


def test_semicolon_files_are_detected_and_warned() -> None:
    report = import_text("first_name;last_name;date_of_birth\nJohn;Smith;\n")

    assert report.delimiter == ";"
    assert report.rows[0].status is RowStatus.ACCEPTED
    assert FileIssueCode.DELIMITER_DETECTED in file_issue_codes(report)


def test_utf8_bom_is_removed() -> None:
    data = ("﻿" + HEADER + "José,Muñoz,,DRV-1\n").encode("utf-8")

    report = build_importer().import_bytes(data)

    assert report.rows[0].person is not None
    assert report.rows[0].person.first_name == "José"
    assert report.encoding == "utf-8"


def test_latin1_files_are_read_with_a_warning() -> None:
    data = (HEADER + "Pedro,Rodríguez,,DRV-1\n").encode("latin-1")

    report = build_importer().import_bytes(data)

    assert report.rows[0].person is not None
    assert report.rows[0].person.last_name == "Rodríguez"
    assert report.encoding == "latin-1"
    assert FileIssueCode.ENCODING_FALLBACK in file_issue_codes(report)


def test_duplicate_rows_are_rejected_and_point_to_the_first_one() -> None:
    report = import_text(HEADER + "Pedro,Rodríguez,,A\nPEDRO,rodriguez,,B\nPedro,Rodriguez,,C\n")

    assert [row.status for row in report.rows] == [RowStatus.ACCEPTED] + [RowStatus.REJECTED] * 2
    assert report.rows[1].duplicate_of_line == 2
    assert issue_codes(report.rows[2]) == {RowIssueCode.DUPLICATE}


def test_same_name_with_different_birth_dates_are_not_duplicates() -> None:
    report = import_text(
        HEADER + "John,Smith,1978-07-24,A\nJohn,Smith,1959-10-19,B\nJohn,Smith,,C\n"
    )

    assert all(row.status is RowStatus.ACCEPTED for row in report.rows)


def test_names_that_cannot_fit_the_portal_search_are_rejected() -> None:
    row = import_text(HEADER + "Maria Guadalupe,Hernandez Rodriguez,,A\n").rows[0]

    assert issue_codes(row) == {RowIssueCode.NOT_SEARCHABLE}


def test_compound_surname_is_searchable_through_a_variant() -> None:
    row = import_text(HEADER + "Maria,Rodriguez Hernandez,,A\n").rows[0]

    assert row.status is RowStatus.ACCEPTED


def test_unreadable_row_is_rejected_without_stopping_the_file() -> None:
    huge_cell = "A" * 200_000
    report = import_text(HEADER + f"John,{huge_cell},,A\nPedro,Rodriguez,,B\n", max_bytes=500_000)

    assert issue_codes(report.rows[0]) == {RowIssueCode.MALFORMED_ROW}
    assert report.rows[1].status is RowStatus.ACCEPTED


@pytest.mark.parametrize(
    ("text", "expected_code"),
    [
        ("", FileIssueCode.EMPTY_FILE),
        ("# only a comment\n\n", FileIssueCode.EMPTY_FILE),
        ("first_name,last_name\n", FileIssueCode.NO_DATA_ROWS),
        ("name,age\nJohn,3\n", FileIssueCode.MISSING_REQUIRED_COLUMNS),
        ("first_name,last_name,first_name\nJ,S,K\n", FileIssueCode.DUPLICATE_COLUMNS),
    ],
)
def test_file_level_problems_are_reported_instead_of_raised(
    text: str, expected_code: FileIssueCode
) -> None:
    report = import_text(text)

    assert report.has_file_errors
    assert expected_code in file_issue_codes(report)
    assert report.rows == ()


def test_binary_content_is_rejected() -> None:
    report = build_importer().import_bytes(b"first_name,last_name\n\x00\x01\x02")

    assert FileIssueCode.BINARY_FILE in file_issue_codes(report)


def test_oversized_file_is_rejected() -> None:
    report = import_text(HEADER + "John,Smith,,A\n", max_bytes=10)

    assert FileIssueCode.FILE_TOO_LARGE in file_issue_codes(report)


def test_file_with_too_many_rows_is_rejected_not_truncated() -> None:
    report = import_text(HEADER + "A B,Smith,,1\nC D,Jones,,2\nE F,Green,,3\n", max_rows=2)

    assert FileIssueCode.TOO_MANY_ROWS in file_issue_codes(report)
    assert report.rows == ()


def test_empty_cells_in_the_middle_do_not_break_the_row() -> None:
    report = import_text(HEADER + "John,Smith,,\n")

    assert report.rows[0].status is RowStatus.ACCEPTED
