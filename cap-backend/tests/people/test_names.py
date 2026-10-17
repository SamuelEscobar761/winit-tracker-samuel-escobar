import pytest

from app.people.names import (
    build_search_query,
    fold_accents,
    is_searchable_query,
    normalize_name,
)


@pytest.mark.parametrize("text", ["Rodríguez", "rodriguez", "RODRIGUEZ", "  Rodriguez  "])
def test_accent_and_case_variants_share_one_match_key(text: str) -> None:
    assert normalize_name(text) == "RODRIGUEZ"


def test_normalization_handles_hyphens_apostrophes_and_extra_spaces() -> None:
    assert normalize_name("de  la-Cruz") == "DE LA CRUZ"
    assert normalize_name("O'Brien") == "OBRIEN"


def test_fold_accents_removes_diacritics_only() -> None:
    assert fold_accents("Muñoz Ángel") == "Munoz Angel"


def test_search_query_uses_comma_form_without_accents() -> None:
    assert build_search_query("Pedro", "Rodríguez") == "rodriguez, pedro"
    assert build_search_query("John", "Smith") == "smith, john"


def test_search_query_collapses_whitespace_and_drops_symbols() -> None:
    assert build_search_query(" Maria   Jose ", "Lopez 3") == "lopez, maria jose"


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("li, a", True),
        ("abc", False),
        ("rodriguez, pedro", True),
        ("rodriguez hernandez, maria", False),
    ],
)
def test_query_length_follows_portal_limits(query: str, expected: bool) -> None:
    assert is_searchable_query(query) is expected
