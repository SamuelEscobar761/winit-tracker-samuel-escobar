from pydantic import BaseModel

from app.config.settings import Settings


class AiStatus(BaseModel):
    enabled: bool
    available: bool
    mode: str
    model: str | None
    rules_auto_apply: bool
    reason: str | None


class AiGate:
    """The single off switch: without AI or a key the app runs on deterministic code only."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @property
    def is_available(self) -> bool:
        return self._settings.ai_enabled and (self._has_key or self._settings.ai_offline_mock)

    @property
    def _has_key(self) -> bool:
        key = self._settings.anthropic_api_key
        return key is not None and bool(key.get_secret_value())

    def status(self) -> AiStatus:
        settings = self._settings
        return AiStatus(
            enabled=settings.ai_enabled,
            available=self.is_available,
            mode=self._mode(),
            model=settings.ai_model if self.is_available else None,
            rules_auto_apply=settings.ai_rules_auto_apply,
            reason=self._unavailable_reason(),
        )

    def _mode(self) -> str:
        if not self.is_available:
            return "off"
        return "offline-mock" if self._settings.ai_offline_mock else "anthropic"

    def _unavailable_reason(self) -> str | None:
        if self.is_available:
            return None
        if not self._settings.ai_enabled:
            return "AI_ENABLED is false"
        return "ANTHROPIC_API_KEY is not set"
