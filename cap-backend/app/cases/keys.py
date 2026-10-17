import re

_NON_ALPHANUMERIC = re.compile(r"[^A-Z0-9]")


def build_case_key(case_number: str) -> str:
    """The results table shows `25IN-169374` while the case request returns `25IN169374`."""
    return _NON_ALPHANUMERIC.sub("", case_number.upper())
