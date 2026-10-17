from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from app.providers.live.health import PortalHealthChecker
from app.providers.live.page_source import PlaywrightPageSource
from app.providers.live.provider import LiveCapProvider
from app.providers.throttle.action_throttle import ActionThrottle
from tests.support.fake_portal import FakePortal
from tests.support.fake_time import FakeTime

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"
ACTION_DELAY = 5.0


def chromium_is_available() -> bool:
    try:
        with sync_playwright() as playwright:
            playwright.chromium.launch(headless=True).close()
    except Exception:
        return False
    return True


BROWSER_AVAILABLE = chromium_is_available()


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    skip = pytest.mark.skip(reason="Chromium is not installed (playwright install chromium)")
    for item in items:
        if "tests/live" in item.nodeid.replace("\\", "/") and not BROWSER_AVAILABLE:
            item.add_marker(skip)


@pytest.fixture
def portal() -> Iterator[FakePortal]:
    fake_portal = FakePortal(FIXTURES)
    fake_portal.start()
    yield fake_portal
    fake_portal.stop()


@pytest.fixture
def fake_time() -> FakeTime:
    return FakeTime()


@pytest.fixture
async def live_provider(portal: FakePortal, fake_time: FakeTime) -> AsyncIterator[LiveCapProvider]:
    source = PlaywrightPageSource(headless=True)
    throttle = ActionThrottle(ACTION_DELAY, [], fake_time)
    health = PortalHealthChecker(source, portal.base_url, 5.0)
    provider = LiveCapProvider(source, throttle, health, portal.base_url, 5.0)
    yield provider
    await provider.aclose()
