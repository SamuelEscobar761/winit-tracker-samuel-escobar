from app.config.settings import Settings
from app.providers.throttle.action_throttle import ActionThrottle
from app.providers.throttle.clock import Clock, ScaledSleeper, Sleeper
from app.providers.throttle.limiter import SlidingWindowLimiter
from app.providers.throttle.observer import WaitObserver

WINDOW_SECONDS = 60.0


def create_action_throttle(
    settings: Settings,
    clock: Clock,
    sleeper: Sleeper,
    global_limiter: SlidingWindowLimiter | None = None,
    speed_factor: float = 1.0,
    observer: WaitObserver | None = None,
) -> ActionThrottle:
    scaled_sleeper = ScaledSleeper(sleeper, speed_factor)
    worker_limiter = SlidingWindowLimiter(
        settings.cap_max_actions_per_minute, WINDOW_SECONDS / speed_factor, clock, sleeper
    )
    limiters = [worker_limiter] + ([global_limiter] if global_limiter else [])
    return ActionThrottle(settings.cap_action_delay_seconds, limiters, scaled_sleeper, observer)


def create_global_limiter(
    settings: Settings, clock: Clock, sleeper: Sleeper, speed_factor: float = 1.0
) -> SlidingWindowLimiter | None:
    if settings.cap_global_max_actions_per_minute is None:
        return None
    return SlidingWindowLimiter(
        settings.cap_global_max_actions_per_minute, WINDOW_SECONDS / speed_factor, clock, sleeper
    )
