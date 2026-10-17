from dataclasses import dataclass

from app.people.names import normalize_name


@dataclass(frozen=True)
class ParsedCaption:
    last_name: str
    given_names: tuple[str, ...]


def parse_caption(caption: str) -> ParsedCaption | None:
    """Captions without a comma are businesses or free text, never a `LAST, FIRST` person."""
    if "," not in caption:
        return None
    last_part, given_part = caption.split(",", 1)
    last_name = normalize_name(last_part)
    if not last_name:
        return None
    return ParsedCaption(last_name=last_name, given_names=tuple(normalize_name(given_part).split()))
