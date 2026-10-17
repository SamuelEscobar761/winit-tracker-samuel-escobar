from datetime import date
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator


class NameVariantStrategy(StrEnum):
    AS_WRITTEN = "as_written"
    FIRST_SURNAME_ONLY = "first_surname_only"
    LAST_SURNAME_ONLY = "last_surname_only"
    JOINED_PARTICLES = "joined_particles"
    FIRST_GIVEN_NAME_ONLY = "first_given_name_only"


class StrategySetting(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: NameVariantStrategy
    enabled: bool = True


class VariantObservation(BaseModel):
    model_config = ConfigDict(frozen=True)

    csv_name: str
    query_that_worked: str
    caption_seen: str
    strategy: NameVariantStrategy | None = None
    observed_on: date | None = None


class NameVariantConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    version: int
    max_attempts_per_person: int = Field(ge=1)
    stop_after_first_with_results: bool
    name_particles: tuple[str, ...]
    strategies: tuple[StrategySetting, ...]
    observations: tuple[VariantObservation, ...] = ()

    @property
    def enabled_strategies(self) -> tuple[NameVariantStrategy, ...]:
        return tuple(setting.id for setting in self.strategies if setting.enabled)

    @model_validator(mode="after")
    def require_as_written_first(self) -> "NameVariantConfig":
        first = self.strategies[0] if self.strategies else None
        if first is None or first.id is not NameVariantStrategy.AS_WRITTEN or not first.enabled:
            raise ValueError("The first strategy must be an enabled 'as_written'")
        return self


def load_name_variant_config(path: Path) -> NameVariantConfig:
    return NameVariantConfig.model_validate_json(path.read_text(encoding="utf-8"))
