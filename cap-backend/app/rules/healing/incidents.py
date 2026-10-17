import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

IncidentKind = Literal["ui", "response"]
IncidentStatus = Literal["open", "repairing", "repaired", "awaiting_review", "failed", "dismissed"]
ACTIVE_STATUSES: tuple[IncidentStatus, ...] = ("open", "repairing", "awaiting_review")


class DriftIncident(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    kind: IncidentKind
    message: str
    rules_version: int
    evidence: dict[str, Any]
    status: IncidentStatus = "open"
    outcome: str | None = None


class IncidentLog:
    def __init__(self, file: Path | None = None) -> None:
        self._file = file
        self._incidents: dict[str, DriftIncident] = {}

    def add(self, incident: DriftIncident) -> DriftIncident:
        self._incidents[incident.id] = incident
        self._persist(incident)
        return incident

    def get(self, incident_id: str) -> DriftIncident | None:
        return self._incidents.get(incident_id)

    def update(
        self, incident_id: str, status: IncidentStatus, outcome: str | None = None
    ) -> DriftIncident:
        updated = self._incidents[incident_id].model_copy(
            update={"status": status, "outcome": outcome}
        )
        self._incidents[incident_id] = updated
        self._persist(updated)
        return updated

    def all(self) -> list[DriftIncident]:
        return sorted(self._incidents.values(), key=lambda item: item.at, reverse=True)

    def has_active_incident_for(self, message: str) -> bool:
        return any(
            incident.message == message and incident.status in ACTIVE_STATUSES
            for incident in self._incidents.values()
        )

    def _persist(self, incident: DriftIncident) -> None:
        if self._file is None:
            return
        self._file.parent.mkdir(parents=True, exist_ok=True)
        with self._file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(incident.model_dump(mode="json")) + "\n")
