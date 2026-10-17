from app.cases.models import Charge

_CHARGE_PREFIX = "Charge:"
_STATUTE_SEPARATOR = ": "


def parse_charge(raw_charge: str) -> Charge:
    text = _strip_prefix(raw_charge.strip())
    statute, separator, description = text.partition(_STATUTE_SEPARATOR)
    if not separator:
        return Charge(statute=text, description="", raw=raw_charge)
    return Charge(statute=statute.strip(), description=description.strip(), raw=raw_charge)


def _strip_prefix(text: str) -> str:
    if text.startswith(_CHARGE_PREFIX):
        return text[len(_CHARGE_PREFIX) :].strip()
    return text
