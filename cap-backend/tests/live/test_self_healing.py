from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path

import pytest

from app.ai.services import AiServices, build_ai_services
from app.config.settings import Settings
from app.providers.errors import ProviderTimeout, UnparsedLayout
from app.providers.live.health import PortalHealthChecker
from app.providers.live.page_source import PlaywrightPageSource
from app.providers.live.provider import LiveCapProvider
from app.providers.throttle.action_throttle import ActionThrottle
from app.rules.healing.incidents import IncidentLog
from app.rules.registry import RulesRegistry
from app.rules.store import RulesStore
from tests.live.conftest import ACTION_DELAY
from tests.support.fake_portal import FakePortal
from tests.support.fake_time import FakeTime


@dataclass
class Rig:
    provider: LiveCapProvider
    ai: AiServices
    rules: RulesRegistry


def build_provider(
    portal: FakePortal, fake_time: FakeTime, rules: RulesRegistry, ai: AiServices | None = None
) -> LiveCapProvider:
    source = PlaywrightPageSource(headless=True)
    throttle = ActionThrottle(ACTION_DELAY, [], fake_time)
    health = PortalHealthChecker(source, portal.base_url, 5.0, rules)
    drift = ai.monitor if ai else None
    return LiveCapProvider(source, throttle, health, portal.base_url, 5.0, rules=rules, drift=drift)


async def build_rig(
    portal: FakePortal, fake_time: FakeTime, tmp_path: Path, **settings: object
) -> Rig:
    rules = RulesRegistry(RulesStore(tmp_path / "rules"))
    app_settings = Settings.model_validate(settings)
    ai = build_ai_services(
        app_settings,
        rules,
        IncidentLog(),
        lambda candidate: build_provider(portal, fake_time, candidate),
    )
    return Rig(build_provider(portal, fake_time, rules, ai), ai, rules)


@pytest.fixture
async def rig(portal: FakePortal, fake_time: FakeTime, tmp_path: Path) -> AsyncIterator[Rig]:
    created = await build_rig(portal, fake_time, tmp_path, ai_enabled=True, ai_offline_mock=True)
    yield created
    await created.provider.aclose()


async def test_a_renamed_button_is_repaired_without_a_developer(
    rig: Rig, portal: FakePortal
) -> None:
    portal.state.party_label = "Search by Name"

    with pytest.raises(ProviderTimeout):
        await rig.provider.search("smith, john")
    await rig.ai.monitor.wait_for_repairs()

    assert rig.rules.current.version == 2
    assert rig.rules.current.ui.party_name_button == "Search by Name"
    assert rig.ai.incidents.all()[0].status == "repaired"
    response = await rig.provider.search("smith, john")
    assert len(response.cases) == 286


async def test_a_renamed_json_field_is_repaired_and_the_next_search_works(
    rig: Rig, portal: FakePortal
) -> None:
    portal.state.case_number_key = "caseNo"

    with pytest.raises(UnparsedLayout):
        await rig.provider.search("smith, john")
    await rig.ai.monitor.wait_for_repairs()

    assert rig.rules.current.fields.search_item["caseNumber"] == "caseNo"
    response = await rig.provider.search("smith, john")
    assert len(response.cases) == 286


async def test_a_moved_api_path_is_repaired(rig: Rig, portal: FakePortal) -> None:
    portal.state.search_path = "/api/traffic/lookup"

    with pytest.raises(ProviderTimeout):
        await rig.provider.search("smith, john")
    await rig.ai.monitor.wait_for_repairs()

    assert rig.rules.current.api.search_path == "/api/traffic/lookup"
    response = await rig.provider.search("smith, john")
    assert len(response.cases) == 286


async def test_the_change_log_explains_who_changed_what_and_why(
    rig: Rig, portal: FakePortal
) -> None:
    portal.state.party_label = "Search by Name"
    with pytest.raises(ProviderTimeout):
        await rig.provider.search("smith, john")
    await rig.ai.monitor.wait_for_repairs()

    entry = rig.rules.changelog()[-1]

    assert (entry.actor, entry.model, entry.previous_version) == ("agent", "offline-mock", 1)
    assert entry.canary is not None and "returned 286 cases" in entry.canary
    assert [(c.path, c.after) for c in entry.changes] == [
        ("ui.party_name_button", "Search by Name")
    ]


async def test_the_incident_evidence_contains_no_case_data(rig: Rig, portal: FakePortal) -> None:
    portal.state.case_number_key = "caseNo"
    with pytest.raises(UnparsedLayout):
        await rig.provider.search("rodriguez, pedro")
    await rig.ai.monitor.wait_for_repairs()

    evidence = str(rig.ai.incidents.all()[0].evidence)

    assert "RODRIGUEZ" not in evidence.upper()
    assert "payload_skeleton" in evidence


async def test_without_ai_the_incident_is_recorded_and_nothing_changes(
    portal: FakePortal, fake_time: FakeTime, tmp_path: Path
) -> None:
    rig = await build_rig(portal, fake_time, tmp_path)
    portal.state.party_label = "Search by Name"

    try:
        with pytest.raises(ProviderTimeout):
            await rig.provider.search("smith, john")
    finally:
        await rig.provider.aclose()

    assert rig.ai.healer is None
    assert rig.rules.current.version == 1
    assert [incident.status for incident in rig.ai.incidents.all()] == ["open"]
