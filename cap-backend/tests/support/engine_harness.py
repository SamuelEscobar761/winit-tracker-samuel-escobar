import asyncio
import random
import shutil
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from app.config.settings import Settings
from app.csv_import.factory import create_csv_importer
from app.csv_import.importer import CsvImporter
from app.jobs.activity import JobWaitObserver
from app.jobs.container import JobSystem, build_job_system
from app.jobs.events import EventType
from app.jobs.models import Job
from app.people.variants.config import load_name_variant_config
from app.providers.base import CapProvider
from app.providers.mock.catalog import load_mock_catalog
from app.providers.mock.failures import FailureSchedule, NoFailures
from app.providers.mock.provider import MockCapProvider, MockLatency
from app.providers.throttle.action_throttle import ActionThrottle
from tests.support.fake_time import FakeTime

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = PROJECT_ROOT / "fixtures"
CSV_HEADER = "first_name,last_name,date_of_birth,external_ref\n"


@dataclass
class Engine:
    system: JobSystem
    importer: CsvImporter
    variants_path: Path
    fake_time: FakeTime

    async def submit(self, rows: str, parallelism: int | None = None) -> Job:
        report = self.importer.import_bytes((CSV_HEADER + rows).encode("utf-8"))
        return await self.system.service.create_job(report, parallelism)

    async def finish(self, job: Job, timeout: float = 15.0) -> None:
        await asyncio.wait_for(self._wait_until_closed(job), timeout)

    async def wait_for_event(self, job: Job, event_type: EventType, timeout: float = 5.0) -> None:
        await asyncio.wait_for(self._wait_for_event(job, event_type), timeout)

    async def _wait_until_closed(self, job: Job) -> None:
        while not job.event_log.is_closed:
            seen = len(job.event_log.events_after(0))
            await job.event_log.wait_for_more(seen, 1.0)

    async def _wait_for_event(self, job: Job, event_type: EventType) -> None:
        while not any(event.type is event_type for event in job.event_log.events_after(0)):
            seen = len(job.event_log.events_after(0))
            await job.event_log.wait_for_more(seen, 1.0)


def event_types(job: Job) -> list[EventType]:
    return [event.type for event in job.event_log.events_after(0)]


def build_settings(variants_path: Path, fixtures_dir: Path, **overrides: object) -> Settings:
    values: dict[str, object] = {
        "mock_fixtures_dir": fixtures_dir,
        "name_variants_file": variants_path,
        "max_workers": 1,
        "mock_failure_rate": 0,
        "retry_base_delay_seconds": 0.001,
        "max_retries": 2,
        "cap_down_recheck_seconds": 0.01,
        "captcha_wait_seconds": 0.3,
    }
    values.update(overrides)
    return Settings.model_validate(values)


@asynccontextmanager
async def running_engine(
    tmp_path: Path,
    failures: FailureSchedule | None = None,
    fixtures_dir: Path = FIXTURES,
    **setting_overrides: object,
) -> AsyncIterator[Engine]:
    variants_path = tmp_path / "name_variants.json"
    shutil.copy(PROJECT_ROOT / "config" / "name_variants.json", variants_path)
    settings = build_settings(variants_path, fixtures_dir, **setting_overrides)
    variants = load_name_variant_config(variants_path)
    fake_time = FakeTime()
    shared_failures = failures or NoFailures()
    catalog = load_mock_catalog(fixtures_dir)

    def provider_factory(lane: int) -> CapProvider:
        throttle = ActionThrottle(5.0, [], fake_time, JobWaitObserver())
        return MockCapProvider(catalog, throttle, fake_time, shared_failures, MockLatency(0.5, 5.0))

    system = build_job_system(
        settings, variants, provider_factory, fake_time, random.Random(0), date(2026, 10, 16)
    )
    importer = create_csv_importer(settings, variants, date(2026, 10, 16))
    system.pool.start()
    try:
        yield Engine(system, importer, variants_path, fake_time)
    finally:
        await system.pool.stop()
