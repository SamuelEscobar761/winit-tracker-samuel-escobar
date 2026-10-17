import re
from dataclasses import dataclass

_WHITESPACE = re.compile(r"\s+")
_ALLOWED_NAME_SYMBOLS = frozenset(" -'.")


@dataclass(frozen=True)
class NameFieldResult:
    value: str
    was_changed: bool
    has_invalid_characters: bool


def clean_name_field(raw_value: str) -> NameFieldResult:
    collapsed = _WHITESPACE.sub(" ", raw_value).strip()
    return NameFieldResult(
        value=collapsed,
        was_changed=collapsed != raw_value,
        has_invalid_characters=any(not _is_name_character(char) for char in collapsed),
    )


def clean_reference(raw_value: str) -> str | None:
    cleaned = _WHITESPACE.sub(" ", raw_value).strip()
    return cleaned or None


def _is_name_character(character: str) -> bool:
    return character.isalpha() or character in _ALLOWED_NAME_SYMBOLS
