import asyncio
import json
from datetime import date
from pathlib import Path
from typing import Any

from app.people.variants.config import NameVariantStrategy


class ObservationRecorder:
    """Writes the first real evidence for each name variant into the configuration file."""

    def __init__(self, path: Path, today: date) -> None:
        self._path = path
        self._today = today
        self._lock = asyncio.Lock()

    async def record(
        self, csv_name: str, query: str, caption_seen: str, strategy: NameVariantStrategy
    ) -> bool:
        async with self._lock:
            document = json.loads(self._path.read_text(encoding="utf-8"))
            observations: list[dict[str, Any]] = document.setdefault("observations", [])
            if self._is_known(observations, csv_name, query):
                return False
            observations.append(self._build_entry(csv_name, query, caption_seen, strategy))
            self._path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
            return True

    def _is_known(self, observations: list[dict[str, Any]], csv_name: str, query: str) -> bool:
        return any(
            entry["csv_name"] == csv_name and entry["query_that_worked"] == query
            for entry in observations
        )

    def _build_entry(
        self, csv_name: str, query: str, caption_seen: str, strategy: NameVariantStrategy
    ) -> dict[str, Any]:
        return {
            "csv_name": csv_name,
            "query_that_worked": query,
            "caption_seen": caption_seen,
            "strategy": strategy.value,
            "observed_on": self._today.isoformat(),
        }
