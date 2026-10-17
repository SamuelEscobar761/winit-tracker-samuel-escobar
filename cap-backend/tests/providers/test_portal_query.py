import pytest

from app.providers.mock.portal_query import canonical_portal_query


@pytest.mark.parametrize(
    "query",
    ["rodriguez, pedro", "Rodriguez,Pedro", "pedro rodriguez", "  PEDRO   Rodriguez "],
)
def test_comma_form_and_first_last_form_reach_the_same_search(query: str) -> None:
    assert canonical_portal_query(query) == "rodriguez, pedro"


@pytest.mark.parametrize("query", ["rodriguez pedro", "pedro, rodriguez"])
def test_swapped_order_is_a_different_search(query: str) -> None:
    assert canonical_portal_query(query) == "pedro, rodriguez"


def test_accents_are_not_folded_like_the_portal() -> None:
    assert canonical_portal_query("rodríguez, pedro") == "rodríguez, pedro"
