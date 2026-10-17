import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

PORTAL_DATE_FORMAT = "%m/%d/%Y"

_PLACEHOLDER_LICENSES = frozenset({"UNKNOWN", "UNK", "NIP", "NONE", "N/A", "NA"})
_ZERO_LICENSE = re.compile(r"^[A-Z]?0+$")
_AMOUNT_NOISE = re.compile(r"[,$\s]")


def parse_portal_date(raw_date: str | None) -> date | None:
    text = clean_text(raw_date)
    if text is None:
        return None
    try:
        return datetime.strptime(text, PORTAL_DATE_FORMAT).date()
    except ValueError:
        return None


def parse_amount(raw_amount: str | int | float | Decimal | None) -> Decimal | None:
    if raw_amount is None:
        return None
    text = _AMOUNT_NOISE.sub("", str(raw_amount))
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def clean_text(raw_text: str | None) -> str | None:
    if raw_text is None:
        return None
    stripped = raw_text.strip()
    return stripped or None


def clean_drivers_license(raw_license: str | None) -> str | None:
    """The portal fills missing licenses with placeholders such as NIP, UNK or A0000000."""
    text = clean_text(raw_license)
    if text is None:
        return None
    normalized = text.upper()
    if normalized in _PLACEHOLDER_LICENSES or _ZERO_LICENSE.match(normalized):
        return None
    return normalized
