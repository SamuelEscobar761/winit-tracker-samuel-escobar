from datetime import date

import pytest

from app.csv_import.dates import BirthDateProblem, parse_birth_date

TODAY = date(2026, 10, 16)


def test_blank_date_is_allowed_and_empty() -> None:
    result = parse_birth_date("  ", TODAY)

    assert result.value is None
    assert result.problem is None


def test_iso_date_is_accepted_without_reformatting() -> None:
    result = parse_birth_date("1978-07-24", TODAY)

    assert result.value == date(1978, 7, 24)
    assert not result.was_reformatted


@pytest.mark.parametrize(
    ("raw_date", "expected", "note"),
    [
        ("7/24/1978", date(1978, 7, 24), "Read as MM/DD/YYYY"),
        ("24/07/1978", date(1978, 7, 24), "Read as DD/MM/YYYY"),
        ("24.07.1978", date(1978, 7, 24), "Read as DD/MM/YYYY"),
        ("5/5/1990", date(1990, 5, 5), "Read as MM/DD/YYYY"),
    ],
)
def test_slashed_dates_are_read_only_when_one_reading_is_possible(
    raw_date: str, expected: date, note: str
) -> None:
    result = parse_birth_date(raw_date, TODAY)

    assert result.value == expected
    assert result.was_reformatted
    assert result.note == note


@pytest.mark.parametrize("raw_date", ["03/04/1990", "12/11/1985"])
def test_dates_readable_both_ways_are_ambiguous(raw_date: str) -> None:
    result = parse_birth_date(raw_date, TODAY)

    assert result.value is None
    assert result.problem is BirthDateProblem.AMBIGUOUS


@pytest.mark.parametrize(
    "raw_date", ["31/02/1990", "2/30/2001", "1990-13-01", "1990-02-30", "yesterday", "90/1/1"]
)
def test_impossible_or_unknown_formats_are_invalid(raw_date: str) -> None:
    assert parse_birth_date(raw_date, TODAY).problem is BirthDateProblem.INVALID


@pytest.mark.parametrize("raw_date", ["1850-01-01", "2999-01-01", "2026-10-17"])
def test_dates_before_1900_or_in_the_future_are_out_of_range(raw_date: str) -> None:
    assert parse_birth_date(raw_date, TODAY).problem is BirthDateProblem.OUT_OF_RANGE


def test_today_is_a_valid_date() -> None:
    assert parse_birth_date("2026-10-16", TODAY).value == TODAY
