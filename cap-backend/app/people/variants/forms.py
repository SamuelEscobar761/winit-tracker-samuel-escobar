from dataclasses import dataclass

from app.people.models import Person
from app.people.names import normalize_name
from app.people.variants.config import NameVariantConfig, NameVariantStrategy
from app.people.variants.surnames import split_surname_groups


@dataclass(frozen=True)
class NameForms:
    last_names: frozenset[str]
    first_name_prefixes: tuple[tuple[str, ...], ...]

    @classmethod
    def exact(cls, person: Person) -> "NameForms":
        return cls(
            last_names=frozenset({normalize_name(person.last_name)}),
            first_name_prefixes=(tuple(normalize_name(person.first_name).split()),),
        )


def build_name_forms(person: Person, config: NameVariantConfig) -> NameForms:
    enabled = set(config.enabled_strategies)
    groups = split_surname_groups(person.last_name, config.name_particles)
    last_names = {normalize_name(person.last_name)}
    last_names |= _alternative_last_names(enabled, groups)
    return NameForms(
        last_names=frozenset(last_names),
        first_name_prefixes=_first_name_prefixes(person, enabled),
    )


def _alternative_last_names(enabled: set[NameVariantStrategy], groups: tuple[str, ...]) -> set[str]:
    alternatives: set[str] = set()
    if NameVariantStrategy.FIRST_SURNAME_ONLY in enabled and len(groups) > 1:
        alternatives.add(groups[0])
    if NameVariantStrategy.LAST_SURNAME_ONLY in enabled and len(groups) > 1:
        alternatives.add(groups[-1])
    if NameVariantStrategy.JOINED_PARTICLES in enabled:
        alternatives.add(" ".join(group.replace(" ", "") for group in groups))
    return alternatives


def _first_name_prefixes(
    person: Person, enabled: set[NameVariantStrategy]
) -> tuple[tuple[str, ...], ...]:
    written = tuple(normalize_name(person.first_name).split())
    if NameVariantStrategy.FIRST_GIVEN_NAME_ONLY in enabled and len(written) > 1:
        return (written, written[:1])
    return (written,)
