import asyncio
from typing import Any, Protocol

from app.rules.healing.healer import RulesHealer
from app.rules.healing.incidents import DriftIncident, IncidentKind, IncidentLog
from app.rules.registry import RulesRegistry


class DriftReporter(Protocol):
    async def report(self, kind: IncidentKind, message: str, evidence: dict[str, Any]) -> None: ...


class DriftMonitor:
    """Records a portal change once and, when an agent is available, starts the repair."""

    def __init__(
        self, incidents: IncidentLog, registry: RulesRegistry, healer: RulesHealer | None
    ) -> None:
        self._incidents = incidents
        self._registry = registry
        self._healer = healer
        self._tasks: set[asyncio.Task[object]] = set()

    async def report(self, kind: IncidentKind, message: str, evidence: dict[str, Any]) -> None:
        if self._incidents.has_active_incident_for(message):
            return
        incident = self._incidents.add(
            DriftIncident(
                kind=kind,
                message=message,
                rules_version=self._registry.current.version,
                evidence=evidence,
            )
        )
        if self._healer is not None:
            self._start_repair(self._healer, incident)

    async def wait_for_repairs(self) -> None:
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

    def _start_repair(self, healer: RulesHealer, incident: DriftIncident) -> None:
        task: asyncio.Task[object] = asyncio.create_task(healer.repair(incident.id))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
