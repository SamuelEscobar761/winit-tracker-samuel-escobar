import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.rules.diff import RuleChange
from app.rules.models import PortalRules, default_rules

Actor = Literal["bootstrap", "agent", "manual", "rollback"]


class ChangeEntry(BaseModel):
    model_config = ConfigDict(frozen=True)

    version: int
    previous_version: int | None
    at: datetime
    actor: Actor
    reason: str
    incident_id: str | None = None
    model: str | None = None
    canary: str | None = None
    changes: list[RuleChange] = []


class RulesStore:
    """Plain files: the active rules, every version ever activated and a change log."""

    def __init__(self, directory: Path) -> None:
        self._directory = directory
        self._active_file = directory / "portal_rules.json"
        self._history = directory / "portal_rules_history"
        self._log_file = directory / "portal_rules_log.jsonl"

    def load_active(self) -> PortalRules:
        if not self._active_file.exists():
            return self._bootstrap()
        return PortalRules.model_validate_json(
            self._active_file.read_text(encoding="utf-8")
        ).complete_fields()

    def load_version(self, version: int) -> PortalRules | None:
        path = self._version_file(version)
        if not path.exists():
            return None
        return PortalRules.model_validate_json(path.read_text(encoding="utf-8")).complete_fields()

    def versions(self) -> list[int]:
        if not self._history.exists():
            return []
        return sorted(int(path.stem.removeprefix("v")) for path in self._history.glob("v*.json"))

    def save_active(self, rules: PortalRules, entry: ChangeEntry) -> None:
        self._history.mkdir(parents=True, exist_ok=True)
        text = rules.model_dump_json(indent=2) + "\n"
        self._version_file(rules.version).write_text(text, encoding="utf-8")
        self._active_file.write_text(text, encoding="utf-8")
        with self._log_file.open("a", encoding="utf-8") as log:
            log.write(entry.model_dump_json() + "\n")

    def changelog(self) -> list[ChangeEntry]:
        if not self._log_file.exists():
            return []
        lines = self._log_file.read_text(encoding="utf-8").splitlines()
        return [ChangeEntry.model_validate(json.loads(line)) for line in lines if line.strip()]

    def _bootstrap(self) -> PortalRules:
        rules = default_rules().complete_fields()
        entry = ChangeEntry(
            version=rules.version,
            previous_version=None,
            at=datetime.now(UTC),
            actor="bootstrap",
            reason="Default rules written because no rules file existed",
        )
        self.save_active(rules, entry)
        return rules

    def _version_file(self, version: int) -> Path:
        return self._history / f"v{version:04d}.json"
