from pathlib import Path

import pytest

from app.config.settings import Settings
from app.providers.factory import create_provider
from app.providers.live.provider import LiveCapProvider
from app.providers.mock.provider import MockCapProvider
from app.providers.throttle.clock import SystemClock
from app.providers.throttle.factory import create_global_limiter
from tests.support.fake_time import FakeTime

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"


def build_settings(**overrides: object) -> Settings:
    return Settings.model_validate({"mock_fixtures_dir": FIXTURES, **overrides})


def test_mock_provider_is_created_by_default() -> None:
    assert isinstance(create_provider(build_settings()), MockCapProvider)


def test_live_provider_is_created_without_starting_a_browser() -> None:
    settings = build_settings(cap_provider="live", admin_token="secret")

    assert isinstance(create_provider(settings), LiveCapProvider)


async def test_demo_speed_shortens_a_search_from_seconds_to_a_fraction() -> None:
    fake_time = FakeTime()
    settings = build_settings(mock_failure_rate=0, mock_speed_factor=10)
    provider = create_provider(settings, clock=fake_time, sleeper=fake_time)

    await provider.search("smith, john")

    assert fake_time.now == pytest.approx((3 * 5 + 0.5) / 10)


async def test_global_limiter_is_only_created_when_configured() -> None:
    clock = SystemClock()
    fake_time = FakeTime()

    assert create_global_limiter(build_settings(), clock, fake_time) is None
    configured = build_settings(cap_global_max_actions_per_minute=6)
    assert create_global_limiter(configured, clock, fake_time) is not None
