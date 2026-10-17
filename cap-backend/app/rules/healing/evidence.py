from typing import Any

MAX_DEPTH = 4
MAX_KEYS = 60


def json_skeleton(value: Any, depth: int = 0) -> Any:
    """Keeps keys and value types only, so no personal data from the portal leaves the server."""
    if isinstance(value, dict) and depth < MAX_DEPTH:
        keys = list(value)[:MAX_KEYS]
        return {key: json_skeleton(value[key], depth + 1) for key in keys}
    if isinstance(value, list):
        return [json_skeleton(value[0], depth + 1)] if value and depth < MAX_DEPTH else []
    return type(value).__name__
