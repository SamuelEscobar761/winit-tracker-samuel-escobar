from enum import StrEnum
from pathlib import Path

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ProviderKind(StrEnum):
    MOCK = "mock"
    LIVE = "live"
    REPLICA = "replica"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", frozen=True)

    cap_provider: ProviderKind = ProviderKind.MOCK
    max_workers: int = Field(default=3, ge=1)

    cap_action_delay_seconds: float = Field(default=5.0, ge=0)
    cap_max_actions_per_minute: int = Field(default=12, ge=1)
    cap_global_max_actions_per_minute: int | None = Field(default=None, ge=1)
    cap_max_details_per_person: int | None = Field(default=None, ge=1)

    search_timeout_seconds: float = Field(default=60.0, gt=0)
    detail_timeout_seconds: float = Field(default=30.0, gt=0)
    max_retries: int = Field(default=3, ge=0)
    retry_base_delay_seconds: float = Field(default=2.0, ge=0)
    max_cases_per_person: int = Field(default=500, ge=1)

    csv_max_bytes: int = Field(default=2_000_000, ge=1)
    csv_max_rows: int = Field(default=1000, ge=1)

    cap_base_url: str = "https://cap.sb-court.org/traffic"
    live_headless: bool = True
    live_no_sandbox: bool = False
    live_response_timeout_seconds: float = Field(default=25.0, gt=0)

    mock_fixtures_dir: Path = Path("fixtures")
    mock_speed_factor: float = Field(default=10.0, gt=0)
    mock_failure_rate: float = Field(default=0.08, ge=0, le=1)
    mock_seed: int | None = None
    replica_captcha_rate: float = Field(default=0.1, ge=0, le=1)

    name_variants_file: Path = Path("config/name_variants.json")

    captcha_wait_seconds: float = Field(default=300.0, gt=0)
    cap_down_recheck_seconds: float = Field(default=30.0, gt=0)
    default_parallelism: int = Field(default=1, ge=1)
    sse_heartbeat_seconds: float = Field(default=15.0, gt=0)

    session_ttl_seconds: float = Field(default=28800.0, gt=0)
    cookie_secure: bool = True
    login_max_failures_per_minute: int = Field(default=5, ge=1)

    screencast_quality: int = Field(default=60, ge=1, le=100)
    screencast_every_nth_frame: int = Field(default=2, ge=1)
    screencast_max_width: int = Field(default=1024, ge=200)

    cors_origins: list[str] = ["http://localhost:5173"]

    admin_token: SecretStr | None = None

    ai_enabled: bool = False
    anthropic_api_key: SecretStr | None = None
    ai_model: str = "claude-opus-5-5"
    ai_offline_mock: bool = False
    ai_max_output_tokens: int = Field(default=4000, ge=256)
    ai_request_timeout_seconds: float = Field(default=60.0, gt=0)
    ai_rules_auto_apply: bool = True
    ai_rules_max_repairs_per_hour: int = Field(default=3, ge=1)
    portal_rules_dir: Path = Path("config")

    @property
    def is_live(self) -> bool:
        return self.cap_provider is ProviderKind.LIVE

    @model_validator(mode="after")
    def require_admin_token_in_live_mode(self) -> "Settings":
        if self.is_live and not self.has_admin_token:
            raise ValueError("ADMIN_TOKEN is required when CAP_PROVIDER=live")
        return self

    @property
    def has_admin_token(self) -> bool:
        return self.admin_token is not None and bool(self.admin_token.get_secret_value())
