from collections.abc import Callable
from dataclasses import dataclass

import anthropic

from app.ai.anthropic_model import AnthropicModel
from app.ai.explain import MatchExplainer
from app.ai.gate import AiGate
from app.ai.insight import InsightAgent
from app.ai.model import StructuredModel
from app.ai.offline import register_offline_handlers
from app.ai.offline_model import OfflineModel
from app.ai.structuring import NoticeStructurer
from app.config.settings import Settings
from app.providers.base import CapProvider
from app.rules.healing.canary import SearchCanary
from app.rules.healing.healer import RulesHealer
from app.rules.healing.incidents import IncidentLog
from app.rules.healing.monitor import DriftMonitor
from app.rules.healing.offline import register_healing_handler
from app.rules.healing.proposals import ProposalBoard
from app.rules.registry import RulesRegistry

CANARY_QUERY = "smith, john"


@dataclass(frozen=True)
class AiServices:
    gate: AiGate
    rules: RulesRegistry
    incidents: IncidentLog
    proposals: ProposalBoard
    monitor: DriftMonitor
    healer: RulesHealer | None
    explainer: MatchExplainer | None
    insight: InsightAgent | None
    structurer: NoticeStructurer | None


def create_model(settings: Settings) -> StructuredModel | None:
    if not AiGate(settings).is_available:
        return None
    if settings.ai_offline_mock:
        return _create_offline_model()
    return AnthropicModel(
        _create_client(settings),
        settings.ai_model,
        settings.ai_max_output_tokens,
        settings.ai_request_timeout_seconds,
    )


def build_ai_services(
    settings: Settings,
    rules: RulesRegistry,
    incidents: IncidentLog,
    build_canary_provider: Callable[[RulesRegistry], CapProvider],
    model: StructuredModel | None = None,
) -> AiServices:
    used_model = model or create_model(settings)
    proposals = ProposalBoard()
    healer = _create_healer(
        settings, used_model, rules, incidents, proposals, build_canary_provider
    )
    return AiServices(
        gate=AiGate(settings),
        rules=rules,
        incidents=incidents,
        proposals=proposals,
        monitor=DriftMonitor(incidents, rules, healer),
        healer=healer,
        explainer=MatchExplainer(used_model) if used_model else None,
        insight=InsightAgent(used_model) if used_model else None,
        structurer=NoticeStructurer(used_model) if used_model else None,
    )


def _create_healer(
    settings: Settings,
    model: StructuredModel | None,
    rules: RulesRegistry,
    incidents: IncidentLog,
    proposals: ProposalBoard,
    build_canary_provider: Callable[[RulesRegistry], CapProvider],
) -> RulesHealer | None:
    if model is None:
        return None
    return RulesHealer(
        model,
        rules,
        incidents,
        proposals,
        SearchCanary(build_canary_provider, CANARY_QUERY),
        settings.ai_rules_auto_apply,
        settings.ai_rules_max_repairs_per_hour,
    )


def _create_offline_model() -> OfflineModel:
    model = OfflineModel()
    register_offline_handlers(model)
    register_healing_handler(model)
    return model


def _create_client(settings: Settings) -> anthropic.AsyncAnthropic:
    key = settings.anthropic_api_key
    return anthropic.AsyncAnthropic(api_key=key.get_secret_value() if key else None)
