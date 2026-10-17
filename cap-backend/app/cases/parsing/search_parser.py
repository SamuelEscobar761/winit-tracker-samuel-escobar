from collections.abc import Mapping

from pydantic import ValidationError

from app.cases.keys import build_case_key
from app.cases.models import CaseSummary
from app.cases.parsing.envelope import canonicalize, unwrap_data
from app.cases.parsing.errors import MalformedResponseError
from app.cases.parsing.raw_models import RawSearchItem
from app.cases.status import parse_case_status
from app.cases.values import clean_drivers_license, clean_text, parse_portal_date
from app.rules.models import PortalRules

DEFAULT_RULES = PortalRules().complete_fields()


def parse_search_response(
    payload: Mapping[str, object], rules: PortalRules = DEFAULT_RULES
) -> list[CaseSummary]:
    data = unwrap_data(payload, rules.responses)
    if not isinstance(data, list):
        raise MalformedResponseError("The search data is not a list")
    mapping = rules.fields.search_item
    return [_to_summary(_validate_item(canonicalize(item, mapping)), item) for item in data]


def _validate_item(item: object) -> RawSearchItem:
    try:
        return RawSearchItem.model_validate(item)
    except ValidationError as error:
        raise MalformedResponseError(f"Invalid search item: {error}") from error


def _to_summary(raw: RawSearchItem, original: object) -> CaseSummary:
    case_number = clean_text(raw.case_number)
    if case_number is None:
        raise MalformedResponseError("A search item has no case number")
    raw_status = clean_text(raw.case_status) or ""
    return CaseSummary(
        portal_case_id=clean_text(raw.case_id),
        case_number=case_number,
        case_key=build_case_key(case_number),
        citation_number=clean_text(raw.citation_number),
        file_date=parse_portal_date(raw.file_date),
        caption=clean_text(raw.case_caption) or "",
        drivers_license=clean_drivers_license(raw.drivers_license),
        date_of_birth=parse_portal_date(raw.date_of_birth),
        status=parse_case_status(raw_status),
        raw_status=raw_status,
        raw_item=dict(original) if isinstance(original, dict) else {},
    )
