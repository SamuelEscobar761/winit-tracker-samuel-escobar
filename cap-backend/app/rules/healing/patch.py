from typing import Any

from pydantic import BaseModel, ValidationError

from app.rules.models import SEARCH_ITEM_KEYS, SELECT_DATA_KEYS, PortalRules

MAX_EDITS = 10
EDITABLE_SECTIONS = ("ui", "api", "responses", "fields")
FIELD_GROUPS = {"search_item": SEARCH_ITEM_KEYS, "select_data": SELECT_DATA_KEYS}


class RuleEdit(BaseModel):
    path: str
    value: str


class RulesPatchProposal(BaseModel):
    diagnosis: str
    edits: list[RuleEdit]


class InvalidPatch(ValueError):
    pass


def apply_patch(rules: PortalRules, edits: list[RuleEdit]) -> PortalRules:
    """Only existing configuration keys can change and the result must pass the rules allowlists."""
    if not edits or len(edits) > MAX_EDITS:
        raise InvalidPatch(f"A patch needs between 1 and {MAX_EDITS} edits")
    data = rules.model_dump()
    for edit in edits:
        _apply_edit(data, edit)
    try:
        return PortalRules.model_validate(data).complete_fields()
    except ValidationError as error:
        message = error.errors()[0]["msg"]
        raise InvalidPatch(f"The patched rules are not valid: {message}") from error


def _apply_edit(data: dict[str, Any], edit: RuleEdit) -> None:
    parts = edit.path.split(".")
    if parts[0] not in EDITABLE_SECTIONS:
        raise InvalidPatch(f"{parts[0]!r} cannot be edited")
    container = _walk(data, parts[:-1], edit.path)
    key = parts[-1]
    if not _is_editable_key(parts, container, key):
        raise InvalidPatch(f"{edit.path!r} is not an existing rule")
    container[key] = _coerce(container.get(key), edit.value)


def _walk(data: dict[str, Any], parts: list[str], path: str) -> dict[str, Any]:
    node: dict[str, Any] = data
    for part in parts:
        child = node.get(part)
        if not isinstance(child, dict):
            raise InvalidPatch(f"{path!r} is not an existing rule")
        node = child
    return node


def _is_editable_key(parts: list[str], container: dict[str, Any], key: str) -> bool:
    if parts[0] == "fields":
        return len(parts) == 3 and key in FIELD_GROUPS.get(parts[1], ())
    return key in container and not isinstance(container[key], dict)


def _coerce(current: object, value: str) -> object:
    if not isinstance(current, int) or isinstance(current, bool):
        return value
    try:
        return int(value)
    except ValueError as error:
        raise InvalidPatch(f"{value!r} is not a number") from error
