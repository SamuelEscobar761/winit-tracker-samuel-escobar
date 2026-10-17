import pytest
from pydantic import ValidationError

from app.config.settings import ProviderKind, Settings


def build_settings(**overrides: object) -> Settings:
    return Settings.model_validate(overrides)


def test_defaults_use_mock_provider_and_agreed_pacing() -> None:
    settings = build_settings()

    assert settings.cap_provider is ProviderKind.MOCK
    assert settings.cap_action_delay_seconds == 5
    assert settings.cap_max_actions_per_minute == 12
    assert settings.cap_max_details_per_person is None
    assert settings.ai_enabled is False


def test_values_are_read_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CAP_ACTION_DELAY_SECONDS", "10")
    monkeypatch.setenv("CAP_MAX_ACTIONS_PER_MINUTE", "6")
    monkeypatch.setenv("MAX_WORKERS", "2")

    settings = build_settings()

    assert settings.cap_action_delay_seconds == 10
    assert settings.cap_max_actions_per_minute == 6
    assert settings.max_workers == 2


def test_live_provider_without_admin_token_is_rejected() -> None:
    with pytest.raises(ValidationError, match="ADMIN_TOKEN"):
        build_settings(cap_provider="live")


def test_live_provider_with_empty_admin_token_is_rejected() -> None:
    with pytest.raises(ValidationError, match="ADMIN_TOKEN"):
        build_settings(cap_provider="live", admin_token="")


def test_live_provider_with_admin_token_is_accepted() -> None:
    settings = build_settings(cap_provider="live", admin_token="secret")

    assert settings.is_live
    assert settings.has_admin_token


@pytest.mark.parametrize(
    "field,value",
    [
        ("cap_action_delay_seconds", -1),
        ("cap_max_actions_per_minute", 0),
        ("max_workers", 0),
        ("search_timeout_seconds", 0),
    ],
)
def test_invalid_numeric_values_are_rejected(field: str, value: float) -> None:
    with pytest.raises(ValidationError):
        build_settings(**{field: value})


def test_admin_token_is_not_exposed_in_representation() -> None:
    settings = build_settings(cap_provider="live", admin_token="secret")

    assert "secret" not in repr(settings)
