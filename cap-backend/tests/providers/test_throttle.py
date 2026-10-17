import pytest

from app.providers.throttle.action_throttle import ActionThrottle
from app.providers.throttle.clock import ScaledSleeper
from app.providers.throttle.limiter import SlidingWindowLimiter
from tests.support.fake_time import FakeTime


def build_limiter(
    fake_time: FakeTime, max_actions: int = 3, window: float = 60.0
) -> SlidingWindowLimiter:
    return SlidingWindowLimiter(max_actions, window, fake_time, fake_time)


async def test_actions_within_the_cap_do_not_wait() -> None:
    fake_time = FakeTime()
    limiter = build_limiter(fake_time)

    for _ in range(3):
        await limiter.acquire()

    assert fake_time.sleeps == []


async def test_action_over_the_cap_waits_until_the_oldest_leaves_the_window() -> None:
    fake_time = FakeTime()
    limiter = build_limiter(fake_time)

    for _ in range(3):
        await limiter.acquire()
    fake_time.now = 10.0
    await limiter.acquire()

    assert fake_time.sleeps == [50.0]
    assert fake_time.now == 60.0


async def test_the_window_slides_instead_of_resetting() -> None:
    fake_time = FakeTime()
    limiter = build_limiter(fake_time, max_actions=2)

    await limiter.acquire()
    fake_time.now = 30.0
    await limiter.acquire()
    await limiter.acquire()

    assert fake_time.now == 60.0
    await limiter.acquire()
    assert fake_time.now == 90.0


async def test_delay_is_applied_after_each_action() -> None:
    fake_time = FakeTime()
    throttle = ActionThrottle(5.0, [], fake_time)

    async with throttle.action():
        assert fake_time.sleeps == []

    assert fake_time.sleeps == [5.0]


async def test_delay_is_applied_even_when_the_action_fails() -> None:
    fake_time = FakeTime()
    throttle = ActionThrottle(5.0, [], fake_time)

    with pytest.raises(RuntimeError):
        async with throttle.action():
            raise RuntimeError("click failed")

    assert fake_time.sleeps == [5.0]


async def test_default_pacing_never_exceeds_twelve_actions_per_minute() -> None:
    fake_time = FakeTime()
    throttle = ActionThrottle(5.0, [build_limiter(fake_time, max_actions=12)], fake_time)

    for _ in range(13):
        async with throttle.action():
            pass

    assert fake_time.now >= 65.0
    assert max(sleep for sleep in fake_time.sleeps) == 5.0


async def test_the_cap_wins_when_the_delay_is_lowered() -> None:
    fake_time = FakeTime()
    throttle = ActionThrottle(1.0, [build_limiter(fake_time, max_actions=2)], fake_time)

    for _ in range(3):
        async with throttle.action():
            pass

    assert fake_time.now >= 60.0


async def test_a_global_limiter_is_shared_by_several_throttles() -> None:
    fake_time = FakeTime()
    shared = build_limiter(fake_time, max_actions=2)
    first = ActionThrottle(0.0, [shared], fake_time)
    second = ActionThrottle(0.0, [shared], fake_time)

    async with first.action():
        pass
    async with second.action():
        pass
    async with first.action():
        pass

    assert fake_time.now == 60.0


async def test_scaled_sleeper_shortens_every_wait() -> None:
    fake_time = FakeTime()

    await ScaledSleeper(fake_time, 10.0).sleep(5.0)

    assert fake_time.sleeps == [0.5]
