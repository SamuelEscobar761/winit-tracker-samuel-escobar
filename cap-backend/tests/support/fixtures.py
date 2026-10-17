import json
from pathlib import Path
from typing import Any

FIXTURES_DIRECTORY = Path(__file__).resolve().parents[2] / "fixtures"


def load_fixture(name: str) -> dict[str, Any]:
    with (FIXTURES_DIRECTORY / name).open(encoding="utf-8") as fixture_file:
        loaded: dict[str, Any] = json.load(fixture_file)
    return loaded
