def canonical_portal_query(query: str) -> str:
    """Mirrors the portal: with a comma the text is `last, first`, without it `first last`."""
    text = " ".join(query.lower().split())
    if "," in text:
        last_name, _, first_name = text.partition(",")
    else:
        first_name, _, last_name = text.partition(" ")
    return f"{last_name.strip()}, {first_name.strip()}"
