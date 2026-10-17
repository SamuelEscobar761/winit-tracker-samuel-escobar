import random

from app.config.settings import ProviderKind, Settings
from app.live.cdp_screencast import CdpScreencast
from app.live.lanes import LaneChannel
from app.live.mock_screen import MockScreen
from app.providers.base import CapProvider
from app.providers.live.health import PortalHealthChecker
from app.providers.live.page_source import PlaywrightPageSource
from app.providers.live.provider import LiveCapProvider
from app.providers.mock.catalog import load_mock_catalog
from app.providers.mock.failures import (
    FailureRates,
    FailureSchedule,
    NoFailures,
    RandomFailures,
)
from app.providers.mock.provider import MockCapProvider
from app.providers.mock.screen import Screen
from app.providers.throttle.clock import AsyncioSleeper, Clock, ScaledSleeper, Sleeper, SystemClock
from app.providers.throttle.factory import create_action_throttle
from app.providers.throttle.limiter import SlidingWindowLimiter
from app.providers.throttle.observer import WaitObserver
from app.replica.server import ReplicaPortal
from app.rules.healing.monitor import DriftReporter
from app.rules.registry import RulesRegistry


def create_provider(
    settings: Settings,
    global_limiter: SlidingWindowLimiter | None = None,
    clock: Clock | None = None,
    sleeper: Sleeper | None = None,
    observer: WaitObserver | None = None,
    channel: LaneChannel | None = None,
    failures: FailureSchedule | None = None,
    rules: RulesRegistry | None = None,
    drift: DriftReporter | None = None,
    replica: ReplicaPortal | None = None,
) -> CapProvider:
    used_clock, used_sleeper = clock or SystemClock(), sleeper or AsyncioSleeper()
    if settings.cap_provider is ProviderKind.REPLICA and replica is not None:
        return _create_live_provider(
            settings,
            global_limiter,
            used_clock,
            used_sleeper,
            observer,
            channel,
            rules,
            drift,
            replica.base_url,
        )
    if settings.cap_provider is ProviderKind.LIVE:
        return _create_live_provider(
            settings, global_limiter, used_clock, used_sleeper, observer, channel, rules, drift
        )
    return _create_mock_provider(
        settings, global_limiter, used_clock, used_sleeper, observer, channel, failures
    )


def _create_live_provider(
    settings: Settings,
    global_limiter: SlidingWindowLimiter | None,
    clock: Clock,
    sleeper: Sleeper,
    observer: WaitObserver | None,
    channel: LaneChannel | None,
    rules: RulesRegistry | None,
    drift: DriftReporter | None,
    base_url: str | None = None,
) -> LiveCapProvider:
    url = base_url or settings.cap_base_url
    source = PlaywrightPageSource(
        settings.live_headless,
        channel,
        _create_screencast(settings, channel),
        ("--no-sandbox",) if settings.live_no_sandbox else (),
    )
    throttle = create_action_throttle(settings, clock, sleeper, global_limiter, 1.0, observer)
    timeout = settings.live_response_timeout_seconds
    health = PortalHealthChecker(source, url, timeout, rules)
    return LiveCapProvider(source, throttle, health, url, timeout, rules=rules, drift=drift)


def _create_mock_provider(
    settings: Settings,
    global_limiter: SlidingWindowLimiter | None,
    clock: Clock,
    sleeper: Sleeper,
    observer: WaitObserver | None,
    channel: LaneChannel | None,
    failures: FailureSchedule | None,
) -> MockCapProvider:
    speed_factor = settings.mock_speed_factor
    throttle = create_action_throttle(
        settings, clock, sleeper, global_limiter, speed_factor, observer
    )
    return MockCapProvider(
        catalog=load_mock_catalog(settings.mock_fixtures_dir),
        throttle=throttle,
        sleeper=ScaledSleeper(sleeper, speed_factor),
        failures=failures or _create_failure_schedule(settings),
        screen=_create_mock_screen(settings, channel),
    )


def _create_screencast(settings: Settings, channel: LaneChannel | None) -> CdpScreencast | None:
    if channel is None:
        return None
    return CdpScreencast(
        channel.frames,
        settings.screencast_quality,
        settings.screencast_every_nth_frame,
        settings.screencast_max_width,
    )


def _create_mock_screen(settings: Settings, channel: LaneChannel | None) -> Screen | None:
    if channel is None:
        return None
    screen = MockScreen(channel.frames, settings.screencast_quality)
    channel.input_handler = screen
    return screen


def _create_failure_schedule(settings: Settings) -> FailureSchedule:
    if settings.mock_failure_rate == 0:
        return NoFailures()
    rates = FailureRates.from_total(settings.mock_failure_rate)
    return RandomFailures(rates, random.Random(settings.mock_seed))
