import random
from dataclasses import dataclass
from datetime import date

from app.config.settings import ProviderKind, Settings
from app.jobs.activity import JobWaitObserver
from app.jobs.cap_gate import CapGate
from app.jobs.lifecycle import JobLifecycle
from app.jobs.observations import ObservationRecorder
from app.jobs.person_processor import PersonProcessor
from app.jobs.retry import RetryPolicy
from app.jobs.scheduler import FairScheduler
from app.jobs.service import JobService
from app.jobs.worker_pool import ProviderFactory, WorkerPool
from app.live.input_router import InputRouter
from app.live.lanes import LaneRegistry
from app.people.variants.config import NameVariantConfig
from app.providers.base import CapProvider
from app.providers.factory import create_provider
from app.providers.throttle.clock import AsyncioSleeper, Sleeper, SystemClock
from app.providers.throttle.factory import create_global_limiter
from app.replica.server import ReplicaPortal
from app.rules.healing.monitor import DriftReporter
from app.rules.registry import RulesRegistry


@dataclass(frozen=True)
class JobSystem:
    service: JobService
    pool: WorkerPool
    cap_gate: CapGate
    registry: LaneRegistry
    input_router: InputRouter


def create_default_provider_factory(
    settings: Settings,
    registry: LaneRegistry | None = None,
    rules: RulesRegistry | None = None,
    drift: DriftReporter | None = None,
    replica: ReplicaPortal | None = None,
) -> ProviderFactory:
    clock = SystemClock()
    sleeper = AsyncioSleeper()
    speed_factor = settings.mock_speed_factor if settings.cap_provider is ProviderKind.MOCK else 1.0
    global_limiter = create_global_limiter(settings, clock, sleeper, speed_factor)
    observer = JobWaitObserver()

    def build(lane: int) -> CapProvider:
        channel = registry.channel_for(lane) if registry is not None and lane >= 0 else None
        return create_provider(
            settings,
            global_limiter,
            clock,
            sleeper,
            observer,
            channel,
            rules=rules,
            drift=drift,
            replica=replica,
        )

    return build


def build_job_system(
    settings: Settings,
    variants: NameVariantConfig,
    provider_factory: ProviderFactory,
    sleeper: Sleeper | None = None,
    generator: random.Random | None = None,
    today: date | None = None,
    registry: LaneRegistry | None = None,
) -> JobSystem:
    used_sleeper = sleeper or AsyncioSleeper()
    scheduler = FairScheduler()
    lifecycle = JobLifecycle()
    service = JobService(settings, scheduler, lifecycle)
    recorder = ObservationRecorder(settings.name_variants_file, today or date.today())
    retry = RetryPolicy(
        settings.max_retries,
        settings.retry_base_delay_seconds,
        used_sleeper,
        generator or random.Random(),
    )
    processor = PersonProcessor(settings, variants, retry, recorder)
    health_provider = provider_factory(-1)
    gate = CapGate(
        health_provider.check_health, settings.cap_down_recheck_seconds, used_sleeper, service
    )
    lanes = registry or LaneRegistry()
    pool = WorkerPool(
        settings.max_workers, scheduler, processor, lifecycle, gate, provider_factory, lanes
    )
    return JobSystem(service, pool, gate, lanes, InputRouter(lanes, service))
