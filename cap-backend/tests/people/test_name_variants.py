from pathlib import Path

import pytest
from pydantic import ValidationError

from app.people.models import Person
from app.people.variants.config import (
    NameVariantConfig,
    NameVariantStrategy,
    load_name_variant_config,
)
from app.people.variants.queries import generate_search_attempts
from app.people.variants.surnames import split_surname_groups

SHIPPED_CONFIG = Path(__file__).resolve().parents[2] / "config" / "name_variants.json"
PARTICLES = ("DE", "DEL", "LA", "LAS", "LOS")


def build_config(**overrides: object) -> NameVariantConfig:
    values: dict[str, object] = {
        "version": 1,
        "max_attempts_per_person": 5,
        "stop_after_first_with_results": True,
        "name_particles": PARTICLES,
        "strategies": [{"id": strategy.value} for strategy in NameVariantStrategy],
    }
    values.update(overrides)
    return NameVariantConfig.model_validate(values)


def queries_for(person: Person, config: NameVariantConfig) -> list[str]:
    return [attempt.query for attempt in generate_search_attempts(person, config)]


def test_shipped_configuration_is_valid_and_starts_with_the_written_name() -> None:
    config = load_name_variant_config(SHIPPED_CONFIG)

    assert config.enabled_strategies[0] is NameVariantStrategy.AS_WRITTEN
    assert config.max_attempts_per_person >= 1
    assert config.observations == ()


def test_unknown_strategy_is_rejected() -> None:
    with pytest.raises(ValidationError):
        build_config(strategies=[{"id": "as_written"}, {"id": "invented"}])


def test_as_written_must_be_the_first_enabled_strategy() -> None:
    with pytest.raises(ValidationError, match="as_written"):
        build_config(strategies=[{"id": "first_surname_only"}, {"id": "as_written"}])
    with pytest.raises(ValidationError, match="as_written"):
        build_config(strategies=[{"id": "as_written", "enabled": False}])


@pytest.mark.parametrize(
    ("last_name", "expected"),
    [
        ("Garcia Lopez", ("GARCIA", "LOPEZ")),
        ("De la Cruz Perez", ("DE LA CRUZ", "PEREZ")),
        ("Del Rio", ("DEL RIO",)),
        ("Lopez-Garcia", ("LOPEZ", "GARCIA")),
        ("Smith", ("SMITH",)),
        ("Perez de", ("PEREZ DE",)),
    ],
)
def test_surnames_are_split_keeping_particles_with_the_next_word(
    last_name: str, expected: tuple[str, ...]
) -> None:
    assert split_surname_groups(last_name, PARTICLES) == expected


def test_simple_name_gives_a_single_attempt() -> None:
    person = Person(first_name="John", last_name="Smith")

    assert queries_for(person, build_config()) == ["smith, john"]


def test_compound_surname_tries_written_then_each_surname() -> None:
    person = Person(first_name="Maria", last_name="Garcia Lopez")

    assert queries_for(person, build_config()) == [
        "garcia lopez, maria",
        "garcia, maria",
        "lopez, maria",
    ]


def test_particles_surname_also_tries_the_joined_form() -> None:
    person = Person(first_name="Juan", last_name="De la Cruz")

    assert queries_for(person, build_config()) == ["de la cruz, juan", "delacruz, juan"]


def test_multi_word_first_name_also_tries_the_first_given_name() -> None:
    person = Person(first_name="Maria Jose", last_name="Garcia")

    assert queries_for(person, build_config()) == ["garcia, maria jose", "garcia, maria"]


def test_accents_are_removed_from_every_attempt() -> None:
    person = Person(first_name="José", last_name="Muñoz Núñez")

    assert queries_for(person, build_config()) == [
        "munoz nunez, jose",
        "munoz, jose",
        "nunez, jose",
    ]


def test_attempts_are_limited_by_the_configuration() -> None:
    person = Person(first_name="Maria", last_name="Garcia Lopez")

    assert len(queries_for(person, build_config(max_attempts_per_person=2))) == 2


def test_queries_outside_the_portal_length_are_dropped() -> None:
    person = Person(first_name="Maria", last_name="Rodriguez Hernandez")

    assert queries_for(person, build_config()) == ["rodriguez, maria", "hernandez, maria"]


def test_disabled_strategies_are_skipped() -> None:
    person = Person(first_name="Maria", last_name="Garcia Lopez")
    config = build_config(
        strategies=[
            {"id": "as_written"},
            {"id": "first_surname_only", "enabled": False},
            {"id": "last_surname_only"},
        ]
    )

    assert queries_for(person, config) == ["garcia lopez, maria", "lopez, maria"]
