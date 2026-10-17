from dataclasses import dataclass

from app.people.models import Person
from app.people.names import build_search_query, is_searchable_query, normalize_name
from app.people.variants.config import NameVariantConfig, NameVariantStrategy
from app.people.variants.surnames import split_surname_groups


@dataclass(frozen=True)
class SearchAttempt:
    strategy: NameVariantStrategy
    query: str


def generate_search_attempts(
    person: Person, config: NameVariantConfig
) -> tuple[SearchAttempt, ...]:
    attempts: list[SearchAttempt] = []
    seen_queries: set[str] = set()
    for strategy in config.enabled_strategies:
        for query in _queries_for(strategy, person, config):
            if _is_new_searchable(query, seen_queries):
                attempts.append(SearchAttempt(strategy, query))
                seen_queries.add(query)
    return tuple(attempts[: config.max_attempts_per_person])


def _is_new_searchable(query: str, seen_queries: set[str]) -> bool:
    return query not in seen_queries and is_searchable_query(query)


def _queries_for(
    strategy: NameVariantStrategy, person: Person, config: NameVariantConfig
) -> list[str]:
    first, last = person.first_name, person.last_name
    groups = split_surname_groups(last, config.name_particles)
    first_tokens = normalize_name(first).split()
    if strategy is NameVariantStrategy.AS_WRITTEN:
        return [build_search_query(first, last)]
    if strategy is NameVariantStrategy.FIRST_SURNAME_ONLY and len(groups) > 1:
        return [build_search_query(first, groups[0])]
    if strategy is NameVariantStrategy.LAST_SURNAME_ONLY and len(groups) > 1:
        return [build_search_query(first, groups[-1])]
    if strategy is NameVariantStrategy.JOINED_PARTICLES and any(" " in group for group in groups):
        return [build_search_query(first, " ".join(group.replace(" ", "") for group in groups))]
    if strategy is NameVariantStrategy.FIRST_GIVEN_NAME_ONLY and len(first_tokens) > 1:
        return [build_search_query(first_tokens[0], last)]
    return []
