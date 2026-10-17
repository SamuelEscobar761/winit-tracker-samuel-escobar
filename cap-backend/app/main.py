import random
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import date

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.ai.services import build_ai_services
from app.api.ai_router import router as ai_router
from app.api.config_router import router as config_router
from app.api.jobs_router import router as jobs_router
from app.api.lanes_router import rest_router as lanes_rest_router
from app.api.lanes_router import websocket_router as lanes_websocket_router
from app.api.rules_router import router as rules_router
from app.auth.rate_limit import LoginRateLimiter
from app.auth.router import router as auth_router
from app.auth.sessions import SessionStore
from app.config.settings import ProviderKind, Settings
from app.csv_import.factory import create_csv_importer
from app.health.router import router as health_router
from app.jobs.container import build_job_system, create_default_provider_factory
from app.jobs.worker_pool import ProviderFactory
from app.live.lanes import LaneRegistry
from app.people.variants.config import load_name_variant_config
from app.providers.factory import create_provider
from app.providers.throttle.clock import SystemClock
from app.replica.server import ReplicaPortal, ReplicaState
from app.rules.healing.incidents import IncidentLog
from app.rules.registry import RulesRegistry
from app.rules.store import RulesStore


def create_app(
    settings: Settings | None = None,
    provider_factory: ProviderFactory | None = None,
    registry: LaneRegistry | None = None,
) -> FastAPI:
    resolved_settings = settings or Settings()
    lanes = registry or LaneRegistry()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        variants = load_name_variant_config(resolved_settings.name_variants_file)
        replica = start_replica(resolved_settings)
        rules = RulesRegistry(RulesStore(resolved_settings.portal_rules_dir))
        incidents = IncidentLog(resolved_settings.portal_rules_dir / "drift_incidents.jsonl")
        ai = build_ai_services(
            resolved_settings,
            rules,
            incidents,
            lambda candidate: create_provider(resolved_settings, rules=candidate, replica=replica),
        )
        app.state.ai = ai
        factory = provider_factory or create_default_provider_factory(
            resolved_settings, lanes, rules, ai.monitor, replica
        )
        system = build_job_system(resolved_settings, variants, factory, registry=lanes)
        app.state.job_system = system
        app.state.csv_importer = create_csv_importer(resolved_settings, variants, date.today())
        system.pool.start()
        try:
            yield
        finally:
            await system.pool.stop()
            if replica is not None:
                replica.stop()

    app = FastAPI(title="California Court Case Tracker", lifespan=lifespan)
    app.state.settings = resolved_settings
    clock = SystemClock()
    app.state.session_store = SessionStore(resolved_settings.session_ttl_seconds, clock)
    app.state.login_limiter = LoginRateLimiter(
        resolved_settings.login_max_failures_per_minute, clock
    )
    register_cors(app, resolved_settings)
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(config_router)
    app.include_router(ai_router)
    app.include_router(rules_router)
    app.include_router(jobs_router)
    app.include_router(lanes_rest_router)
    app.include_router(lanes_websocket_router)
    return app


def start_replica(settings: Settings) -> ReplicaPortal | None:
    if settings.cap_provider is not ProviderKind.REPLICA:
        return None
    state = ReplicaState(
        failure_rate=settings.mock_failure_rate,
        captcha_rate=settings.replica_captcha_rate,
        generator=random.Random(settings.mock_seed),
    )
    portal = ReplicaPortal(settings.mock_fixtures_dir, state)
    portal.start()
    return portal


def register_cors(app: FastAPI, settings: Settings) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Last-Event-ID"],
    )
