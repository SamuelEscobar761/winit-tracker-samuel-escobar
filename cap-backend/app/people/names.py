import re
import unicodedata

SEARCH_QUERY_MIN_LENGTH = 4
SEARCH_QUERY_MAX_LENGTH = 20

_NON_NAME_CHARACTERS = re.compile(r"[^A-Z ]")
_NON_SEARCH_CHARACTERS = re.compile(r"[^a-z '\-]")
_WHITESPACE = re.compile(r"\s+")


def fold_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(character for character in decomposed if not unicodedata.combining(character))


def normalize_name(text: str) -> str:
    folded = fold_accents(text).upper().replace("-", " ").replace("'", "")
    letters_only = _NON_NAME_CHARACTERS.sub("", folded)
    return _collapse_whitespace(letters_only)


def build_search_query(first_name: str, last_name: str) -> str:
    return f"{_to_search_token(last_name)}, {_to_search_token(first_name)}"


def is_searchable_query(query: str) -> bool:
    """The portal input rejects shorter or longer text before any request is made."""
    return SEARCH_QUERY_MIN_LENGTH <= len(query) <= SEARCH_QUERY_MAX_LENGTH


def _to_search_token(name: str) -> str:
    lowered = fold_accents(name).lower()
    return _collapse_whitespace(_NON_SEARCH_CHARACTERS.sub("", lowered))


def _collapse_whitespace(text: str) -> str:
    return _WHITESPACE.sub(" ", text).strip()
