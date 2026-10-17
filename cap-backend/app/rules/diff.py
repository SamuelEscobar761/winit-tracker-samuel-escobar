from typing import Any

from pydantic import BaseModel, ConfigDict

from app.rules.models import PortalRules


class RuleChange(BaseModel):
    model_config = ConfigDict(frozen=True)

    path: str
    before: Any
    after: Any


def diff_rules(old: PortalRules, new: PortalRules) -> list[RuleChange]:
    left = _flatten(old.model_dump(exclude={"version"}))
    right = _flatten(new.model_dump(exclude={"version"}))
    keys = sorted(set(left) | set(right))
    return [
        RuleChange(path=key, before=left.get(key), after=right.get(key))
        for key in keys
        if left.get(key) != right.get(key)
    ]


def _flatten(value: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    flat: dict[str, Any] = {}
    for key, item in value.items():
        path = f"{prefix}{key}"
        if isinstance(item, dict):
            flat.update(_flatten(item, f"{path}."))
        else:
            flat[path] = item
    return flat
