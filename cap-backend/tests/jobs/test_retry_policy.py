import asyncio
import random

import pytest

from app.jobs.retry import RetryPolicy
from app.providers.errors import CapDown, ProviderError, ProviderTimeout, SessionExpired
from tests.support.fake_time import FakeTime


def build_policy(fake_time: FakeTime, max_retries: int = 3, base_delay: float = 1.0) -> RetryPolicy:
    return RetryPolicy(max_retries, base_delay, fake_time, random.Random(1))


class FlakyOperation:
    def __init__(self, failures: list[ProviderError]) -> None:
        self._failures = list(failures)
        self.calls = 0

    async def __call__(self) -> str:
        self.calls += 1
        if self._failures:
            raise self._failures.pop(0)
        return "ok"


async def ignore_retry(attempt: int, error: ProviderError, delay: float) -> None:
    return None


async def test_success_needs_no_retry() -> None:
    operation = FlakyOperation([])

    result = await build_policy(FakeTime()).run(operation, 1.0, ignore_retry)

    assert result == "ok"
    assert operation.calls == 1


async def test_retryable_errors_are_retried_until_success() -> None:
    operation = FlakyOperation([SessionExpired("a"), ProviderTimeout("b")])

    result = await build_policy(FakeTime()).run(operation, 1.0, ignore_retry)

    assert result == "ok"
    assert operation.calls == 3


async def test_backoff_doubles_with_jitter_between_attempts() -> None:
    fake_time = FakeTime()
    operation = FlakyOperation([SessionExpired("a"), SessionExpired("b"), SessionExpired("c")])

    await build_policy(fake_time, base_delay=1.0).run(operation, 1.0, ignore_retry)

    first, second, third = fake_time.sleeps
    assert 1.0 <= first < 2.0
    assert 2.0 <= second < 3.0
    assert 4.0 <= third < 5.0


async def test_retries_are_limited_and_the_last_error_is_raised() -> None:
    operation = FlakyOperation([SessionExpired(str(number)) for number in range(10)])

    with pytest.raises(SessionExpired):
        await build_policy(FakeTime(), max_retries=2).run(operation, 1.0, ignore_retry)

    assert operation.calls == 3


async def test_non_retryable_errors_are_raised_immediately() -> None:
    operation = FlakyOperation([CapDown("maintenance")])

    with pytest.raises(CapDown):
        await build_policy(FakeTime()).run(operation, 1.0, ignore_retry)

    assert operation.calls == 1


async def test_a_slow_operation_becomes_a_provider_timeout() -> None:
    async def slow() -> str:
        await asyncio.sleep(1.0)
        return "late"

    with pytest.raises(ProviderTimeout):
        await build_policy(FakeTime(), max_retries=0).run(slow, 0.01, ignore_retry)


async def test_listener_is_told_about_every_retry() -> None:
    notified: list[tuple[int, str]] = []

    async def listener(attempt: int, error: ProviderError, delay: float) -> None:
        notified.append((attempt, type(error).__name__))

    operation = FlakyOperation([SessionExpired("a"), ProviderTimeout("b")])
    await build_policy(FakeTime()).run(operation, 1.0, listener)

    assert notified == [(1, "SessionExpired"), (2, "ProviderTimeout")]
