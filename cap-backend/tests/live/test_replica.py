from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config.settings import Settings
from app.live.input import InputEvent, InputKind
from app.live.page_input import PageInput
from app.main import create_app
from app.providers.errors import CaptchaRequired, ProviderError
from app.providers.live.provider import LiveCapProvider
from tests.api.test_jobs_api import upload, wait_until_finished
from tests.support.engine_harness import CSV_HEADER, PROJECT_ROOT
from tests.support.fake_portal import FakePortal


async def test_a_human_click_on_the_replica_captcha_lets_the_search_continue(
    live_provider: LiveCapProvider, portal: FakePortal
) -> None:
    portal.state.captcha_rate = 1.0

    with pytest.raises(CaptchaRequired):
        await live_provider.search("smith, john")

    portal.state.captcha_rate = 0.0
    page = await live_provider._page_source.get_page()
    box = await page.locator(".g-recaptcha").first.bounding_box()
    assert box is not None
    click = InputEvent(type=InputKind.CLICK, x=box["x"] + 20, y=box["y"] + 20)
    await PageInput(page).handle(click)
    assert await PageInput(page).captcha_cleared()

    response = await live_provider.search("smith, john")
    assert len(response.cases) == 286


def test_the_replica_provider_runs_a_whole_job_in_chromium(tmp_path: Path) -> None:
    values: dict[str, object] = {
        "cap_provider": "replica",
        "mock_fixtures_dir": PROJECT_ROOT / "fixtures",
        "name_variants_file": PROJECT_ROOT / "config" / "name_variants.json",
        "portal_rules_dir": tmp_path / "rules",
        "mock_failure_rate": 0,
        "replica_captcha_rate": 0,
        "cap_action_delay_seconds": 0,
        "cap_max_details_per_person": 2,
        "max_workers": 1,
        "sse_heartbeat_seconds": 0.05,
    }
    with TestClient(create_app(Settings.model_validate(values))) as client:
        job_id = upload(client, CSV_HEADER + "Pedro,Rodriguez,,r\n").json()["job_id"]

        snapshot = wait_until_finished(client, job_id, timeout=120)

        person = client.get(f"/jobs/{job_id}/people/0").json()
        assert snapshot["state"] == "completed"
        assert person["cases_found"] == 188
        assert person["details_loaded"] == 2


async def test_injected_replica_failures_are_retryable_never_a_layout_change(
    live_provider: LiveCapProvider, portal: FakePortal
) -> None:
    portal.state.failure_rate = 1.0
    portal.state.generator.seed(7)

    for _ in range(6):
        with pytest.raises(ProviderError) as caught:
            await live_provider.search("smith, john")
        assert caught.value.retryable
