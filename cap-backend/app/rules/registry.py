from datetime import UTC, datetime
from threading import RLock

from app.rules.diff import diff_rules
from app.rules.models import PortalRules, default_rules
from app.rules.store import Actor, ChangeEntry, RulesStore


class RulesRegistry:
    """Holds the rules in use; a change takes effect on the next portal action."""

    def __init__(self, store: RulesStore | None = None, initial: PortalRules | None = None) -> None:
        self._store = store
        self._lock = RLock()
        self._active = initial or (
            store.load_active() if store else default_rules().complete_fields()
        )
        self._log: list[ChangeEntry] = store.changelog() if store else []

    @property
    def current(self) -> PortalRules:
        return self._active

    def changelog(self) -> list[ChangeEntry]:
        return list(self._log)

    def versions(self) -> list[int]:
        if self._store is None:
            return [self._active.version]
        return self._store.versions() or [self._active.version]

    def get_version(self, version: int) -> PortalRules | None:
        if version == self._active.version:
            return self._active
        return self._store.load_version(version) if self._store else None

    def activate(
        self,
        candidate: PortalRules,
        actor: Actor,
        reason: str,
        incident_id: str | None = None,
        model: str | None = None,
        canary: str | None = None,
    ) -> PortalRules:
        with self._lock:
            previous = self._active
            new_rules = candidate.model_copy(
                update={"version": self._next_version()}
            ).complete_fields()
            entry = ChangeEntry(
                version=new_rules.version,
                previous_version=previous.version,
                at=datetime.now(UTC),
                actor=actor,
                reason=reason,
                incident_id=incident_id,
                model=model,
                canary=canary,
                changes=diff_rules(previous, new_rules),
            )
            if self._store is not None:
                self._store.save_active(new_rules, entry)
            self._active = new_rules
            self._log.append(entry)
            return new_rules

    def rollback(self, version: int, reason: str) -> PortalRules:
        target = self.get_version(version)
        if target is None:
            raise KeyError(f"Version {version} does not exist")
        return self.activate(target, "rollback", f"Rolled back to version {version}: {reason}")

    def _next_version(self) -> int:
        known = self.versions() + [entry.version for entry in self._log]
        return max(known + [self._active.version]) + 1
