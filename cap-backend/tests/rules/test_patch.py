import pytest

from app.rules.healing.patch import InvalidPatch, RuleEdit, apply_patch
from app.rules.models import PortalRules

RULES = PortalRules().complete_fields()


def test_an_existing_rule_can_change() -> None:
    patched = apply_patch(RULES, [RuleEdit(path="ui.party_name_button", value="Search by Name")])

    assert patched.ui.party_name_button == "Search by Name"
    assert patched.ui.search_button == RULES.ui.search_button


def test_a_field_name_can_be_remapped() -> None:
    patched = apply_patch(RULES, [RuleEdit(path="fields.search_item.caseNumber", value="caseNo")])

    assert patched.fields.search_item["caseNumber"] == "caseNo"
    assert patched.fields.search_item["caseId"] == "caseId"


def test_numbers_are_converted() -> None:
    patched = apply_patch(RULES, [RuleEdit(path="responses.success_result", value="3")])

    assert patched.responses.success_result == 3


@pytest.mark.parametrize(
    "path",
    ["version", "schema_version", "ui", "ui.unknown_rule", "ui.search_button.x", "other.thing"],
)
def test_paths_outside_the_rules_are_refused(path: str) -> None:
    with pytest.raises(InvalidPatch):
        apply_patch(RULES, [RuleEdit(path=path, value="x")])


@pytest.mark.parametrize(
    ("path", "value"),
    [
        ("ui.search_button", "button; alert(1)"),
        ("ui.query_input", "<script>"),
        ("api.search_path", "https://evil.example/steal"),
        ("api.search_path", "api/no-leading-slash"),
        ("responses.success_result", "not-a-number"),
        ("fields.search_item.caseNumber", "bad key!"),
    ],
)
def test_values_that_could_carry_code_or_leave_the_portal_are_refused(
    path: str, value: str
) -> None:
    with pytest.raises(InvalidPatch):
        apply_patch(RULES, [RuleEdit(path=path, value=value)])


def test_unknown_canonical_field_names_are_refused() -> None:
    with pytest.raises(InvalidPatch):
        apply_patch(RULES, [RuleEdit(path="fields.search_item.password", value="x")])


@pytest.mark.parametrize("count", [0, 11])
def test_a_patch_must_stay_small(count: int) -> None:
    edits = [RuleEdit(path="ui.search_button", value="button")] * count

    with pytest.raises(InvalidPatch):
        apply_patch(RULES, edits)
