import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

JsonObject = dict[str, Any]


@dataclass(frozen=True)
class MockCatalog:
    search_payloads: dict[str, JsonObject]
    detail_payloads: dict[str, JsonObject]
    proof_of_correction_template: JsonObject
    payment_plan_template: JsonObject

    def search_payload(self, canonical_query: str) -> JsonObject | None:
        return self.search_payloads.get(canonical_query)

    def detail_payload(self, case_key: str) -> JsonObject | None:
        return self.detail_payloads.get(case_key)


def load_mock_catalog(directory: Path) -> MockCatalog:
    index = _read_json(directory / "mock_catalog.json")
    return MockCatalog(
        search_payloads={
            entry["canonical_query"]: _read_json(directory / entry["file"])
            for entry in index["searches"]
        },
        detail_payloads={
            case_key: _read_json(directory / file_name)
            for case_key, file_name in index["details"].items()
        },
        proof_of_correction_template=_read_json(
            directory / index["templates"]["proof_of_correction"]
        ),
        payment_plan_template=_read_json(directory / index["templates"]["payment_plan"]),
    )


def _read_json(path: Path) -> JsonObject:
    loaded: JsonObject = json.loads(path.read_text(encoding="utf-8"))
    return loaded
