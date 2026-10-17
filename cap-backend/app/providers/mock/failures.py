import random
from collections import deque
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from app.providers.errors import (
    CapDown,
    CaptchaRequired,
    ProviderError,
    ProviderTimeout,
    SessionExpired,
)


class Operation(StrEnum):
    SEARCH = "search"
    DETAIL = "detail"
    HEALTH = "health"


class FailureSchedule(Protocol):
    def failure_for(self, operation: Operation) -> ProviderError | None: ...


class NoFailures:
    def failure_for(self, operation: Operation) -> ProviderError | None:
        return None


class ScriptedFailures:
    """Each call consumes one entry: an error to raise, or None to succeed."""

    def __init__(self, script: Iterable[ProviderError | None]) -> None:
        self._script = deque(script)

    def failure_for(self, operation: Operation) -> ProviderError | None:
        return self._script.popleft() if self._script else None


@dataclass(frozen=True)
class FailureRates:
    session_expired: float
    timeout: float
    captcha: float
    cap_down: float

    @classmethod
    def from_total(cls, total_rate: float) -> "FailureRates":
        return cls(
            session_expired=total_rate * 0.5,
            timeout=total_rate * 0.3,
            captcha=total_rate * 0.15,
            cap_down=total_rate * 0.05,
        )


class RandomFailures:
    def __init__(self, rates: FailureRates, generator: random.Random) -> None:
        self._rates = rates
        self._generator = generator

    def failure_for(self, operation: Operation) -> ProviderError | None:
        roll = self._generator.random()
        threshold = 0.0
        for rate, error_factory in self._outcomes():
            threshold += rate
            if roll < threshold:
                return error_factory()
        return None

    def _outcomes(self) -> list[tuple[float, Callable[[], ProviderError]]]:
        return [
            (
                self._rates.session_expired,
                lambda: SessionExpired("Traffic Payment Session Expired."),
            ),
            (self._rates.timeout, lambda: ProviderTimeout("The portal did not answer in time")),
            (self._rates.captcha, lambda: CaptchaRequired("The portal asked for a CAPTCHA")),
            (self._rates.cap_down, lambda: CapDown("The portal is in maintenance")),
        ]
