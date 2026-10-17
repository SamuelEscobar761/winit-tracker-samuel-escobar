import json
from difflib import get_close_matches
from typing import Any

from app.ai.offline_model import OfflineModel
from app.rules.healing.patch import RuleEdit, RulesPatchProposal

LABEL_RULES = ("party_name_button", "search_again_button", "select_button")
CLOSE_MATCH_CUTOFF = 0.6


async def heal_offline(prompt: str) -> RulesPatchProposal:
    """Looks for the closest label, id, path or JSON key to what the rules expect."""
    request = json.loads(prompt)
    rules, evidence = request["current_rules"], request["evidence"]
    edits = [
        *_label_edits(rules["ui"], evidence, request["failure"]["message"]),
        *_input_edits(rules["ui"], evidence),
        *_path_edits(rules["api"], evidence),
        *_field_edits(rules["fields"], evidence.get("payload_skeleton")),
    ]
    diagnosis = (
        "Matched the rules to the closest names in the evidence"
        if edits
        else ("Nothing in the evidence differs from the rules")
    )
    return RulesPatchProposal(diagnosis=diagnosis, edits=edits)


def register_healing_handler(model: OfflineModel) -> None:
    model.register(RulesPatchProposal, heal_offline)


def _label_edits(ui: dict[str, str], evidence: dict[str, Any], failure: str) -> list[RuleEdit]:
    labels = [str(button["label"]) for button in evidence.get("buttons", []) if button["label"]]
    lowered = {label.lower(): label for label in labels}
    edits = []
    for rule in LABEL_RULES:
        if ui[rule].lower() in lowered or ui[rule] not in failure:
            continue
        match = get_close_matches(ui[rule].lower(), list(lowered), 1, CLOSE_MATCH_CUTOFF)
        if match:
            edits.append(RuleEdit(path=f"ui.{rule}", value=lowered[match[0]]))
    return edits


def _input_edits(ui: dict[str, str], evidence: dict[str, Any]) -> list[RuleEdit]:
    ids = [str(field["id"]) for field in evidence.get("inputs", []) if field["id"]]
    current = ui["query_input"]
    if not ids or (current.startswith("#") and current[1:] in ids):
        return []
    text_ids = [str(f["id"]) for f in evidence["inputs"] if f["id"] and f["type"] == "text"]
    return [RuleEdit(path="ui.query_input", value=f"#{text_ids[0]}")] if len(text_ids) == 1 else []


def _path_edits(api: dict[str, str], evidence: dict[str, Any]) -> list[RuleEdit]:
    seen: list[str] = evidence.get("api_paths_seen", [])
    edits = []
    if seen and api["search_path"] not in seen:
        search = _only_unknown_path(api, seen)
        edits.extend([RuleEdit(path="api.search_path", value=search)] if search else [])
    return edits


def _only_unknown_path(api: dict[str, str], seen: list[str]) -> str | None:
    known = (api["maintenance_path"], api["application_mode_path"], api["select_path_prefix"])
    unknown = {
        path
        for path in seen
        if not path.endswith("/token") and not any(path.startswith(item) for item in known)
    }
    return unknown.pop() if len(unknown) == 1 else None


def _field_edits(fields: dict[str, dict[str, str]], skeleton: Any) -> list[RuleEdit]:
    item = _first_item(skeleton)
    if item is None:
        return []
    group = max(fields, key=lambda name: sum(actual in item for actual in fields[name].values()))
    used = set(fields[group].values()) & set(item)
    edits = []
    for canonical, actual in fields[group].items():
        if actual in item:
            continue
        candidates = [key for key in item if key not in used]
        match = get_close_matches(
            actual.lower(), [k.lower() for k in candidates], 1, CLOSE_MATCH_CUTOFF
        )
        if match:
            name = next(key for key in candidates if key.lower() == match[0])
            used.add(name)
            edits.append(RuleEdit(path=f"fields.{group}.{canonical}", value=name))
    return edits


def _first_item(skeleton: Any) -> dict[str, Any] | None:
    data = skeleton.get("data") if isinstance(skeleton, dict) else None
    if isinstance(data, list):
        data = data[0] if data else None
    return data if isinstance(data, dict) else None
