from pathlib import Path

import pytest

from app.rules.models import PortalRules
from app.rules.registry import RulesRegistry
from app.rules.store import RulesStore


def changed(rules: PortalRules, label: str) -> PortalRules:
    return rules.model_copy(update={"ui": rules.ui.model_copy(update={"party_name_button": label})})


def test_first_start_writes_the_default_rules(tmp_path: Path) -> None:
    registry = RulesRegistry(RulesStore(tmp_path))

    assert registry.current.version == 1
    assert (tmp_path / "portal_rules.json").exists()
    assert registry.changelog()[0].actor == "bootstrap"


def test_activation_creates_a_new_version_with_a_readable_diff(tmp_path: Path) -> None:
    registry = RulesRegistry(RulesStore(tmp_path))

    rules = registry.activate(changed(registry.current, "Search by Name"), "agent", "Label moved")

    entry = registry.changelog()[-1]
    assert rules.version == 2
    assert registry.versions() == [1, 2]
    assert entry.actor == "agent"
    assert [(c.path, c.before, c.after) for c in entry.changes] == [
        ("ui.party_name_button", "Party Name", "Search by Name")
    ]


def test_rules_survive_a_restart(tmp_path: Path) -> None:
    registry = RulesRegistry(RulesStore(tmp_path))
    registry.activate(changed(registry.current, "Search by Name"), "manual", "Edited")

    restarted = RulesRegistry(RulesStore(tmp_path))

    assert restarted.current.version == 2
    assert restarted.current.ui.party_name_button == "Search by Name"
    assert len(restarted.changelog()) == 2


def test_rollback_restores_old_rules_as_a_new_version(tmp_path: Path) -> None:
    registry = RulesRegistry(RulesStore(tmp_path))
    registry.activate(changed(registry.current, "Search by Name"), "agent", "Label moved")

    rules = registry.rollback(1, "The change was wrong")

    assert rules.version == 3
    assert rules.ui.party_name_button == "Party Name"
    assert registry.changelog()[-1].actor == "rollback"


def test_rollback_to_an_unknown_version_fails(tmp_path: Path) -> None:
    with pytest.raises(KeyError):
        RulesRegistry(RulesStore(tmp_path)).rollback(9, "x")


def test_an_in_memory_registry_needs_no_files() -> None:
    registry = RulesRegistry()

    registry.activate(changed(registry.current, "Other"), "manual", "Edited")

    assert registry.current.version == 2
