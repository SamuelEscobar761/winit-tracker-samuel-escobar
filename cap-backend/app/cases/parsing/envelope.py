from collections.abc import Mapping

from app.cases.parsing.errors import MalformedResponseError, PortalResponseError
from app.rules.models import ResponseRules

DEFAULT_RESPONSES = ResponseRules()


def unwrap_data(payload: Mapping[str, object], rules: ResponseRules = DEFAULT_RESPONSES) -> object:
    result = payload.get(rules.result_key)
    if result != rules.success_result:
        message = str(payload.get(rules.message_key) or "")
        raise PortalResponseError(_as_result_code(result), message)
    if rules.data_key not in payload:
        raise MalformedResponseError(f"The response has no {rules.data_key} field")
    return payload[rules.data_key]


def canonicalize(item: object, mapping: Mapping[str, str]) -> object:
    """Renames the portal's current field names to the names this app uses."""
    if not isinstance(item, dict):
        return item
    return {canonical: item[actual] for canonical, actual in mapping.items() if actual in item}


def _as_result_code(result: object) -> int:
    return result if isinstance(result, int) else -1
