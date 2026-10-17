from datetime import date

import pytest

from app.cases.matching.assessment import MatchLabel, assess_case
from app.cases.matching.case_filter import DiscardReason, PersonCaseFilter
from app.people.variants.config import NameVariantConfig, NameVariantStrategy
from app.people.variants.forms import NameForms, build_name_forms
from tests.support.builders import make_case, make_person

BIRTH_DATE = date(1978, 7, 24)


def build_config(enabled: set[NameVariantStrategy] | None = None) -> NameVariantConfig:
    chosen = enabled if enabled is not None else set(NameVariantStrategy)
    return NameVariantConfig.model_validate(
        {
            "version": 1,
            "max_attempts_per_person": 5,
            "stop_after_first_with_results": True,
            "name_particles": ["DE", "LA", "DEL"],
            "strategies": [
                {"id": strategy.value, "enabled": strategy in chosen}
                for strategy in NameVariantStrategy
            ],
        }
    )


def build_filter(first_name: str, last_name: str) -> PersonCaseFilter:
    person = make_person(first_name, last_name)
    return PersonCaseFilter(person, build_name_forms(person, build_config()))


@pytest.mark.parametrize(
    "caption",
    [
        "GARCIA LOPEZ, MARIA",
        "GARCIA, MARIA",
        "LOPEZ, MARIA",
        "GARCIA, MARIA JOSE",
    ],
)
def test_compound_surname_variants_are_kept(caption: str) -> None:
    case_filter = build_filter("Maria", "Garcia Lopez")

    assert case_filter.discard_reason(make_case(caption=caption)) is None


@pytest.mark.parametrize("caption", ["GARCIAS, MARIA", "LOPEZ GARCIA, MARIA", "PEREZ, MARIA"])
def test_unrelated_surnames_are_still_discarded(caption: str) -> None:
    case_filter = build_filter("Maria", "Garcia Lopez")

    assert (
        case_filter.discard_reason(make_case(caption=caption)) is DiscardReason.LAST_NAME_MISMATCH
    )


def test_particle_surname_matches_its_glued_form() -> None:
    case_filter = build_filter("Juan", "De la Cruz")

    assert case_filter.discard_reason(make_case(caption="DELACRUZ, JUAN")) is None
    assert case_filter.discard_reason(make_case(caption="DE LA CRUZ, JUAN")) is None


def test_first_given_name_only_variant_is_accepted_for_two_given_names() -> None:
    case_filter = build_filter("Maria Jose", "Garcia")

    assert case_filter.discard_reason(make_case(caption="GARCIA, MARIA")) is None
    assert (
        case_filter.discard_reason(make_case(caption="GARCIA, JOSE"))
        is DiscardReason.FIRST_NAME_MISMATCH
    )


def test_without_variants_only_the_written_name_matches() -> None:
    person = make_person("Maria", "Garcia Lopez")
    case_filter = PersonCaseFilter(person, NameForms.exact(person))

    assert (
        case_filter.discard_reason(make_case(caption="GARCIA, MARIA"))
        is DiscardReason.LAST_NAME_MISMATCH
    )


def test_disabled_strategies_do_not_widen_the_match() -> None:
    person = make_person("Maria", "Garcia Lopez")
    forms = build_name_forms(person, build_config({NameVariantStrategy.AS_WRITTEN}))

    assert PersonCaseFilter(person, forms).discard_reason(make_case(caption="LOPEZ, MARIA")) is (
        DiscardReason.LAST_NAME_MISMATCH
    )


def test_variant_match_is_never_confirmed_even_with_the_same_birth_date() -> None:
    person = make_person("Maria", "Garcia Lopez", BIRTH_DATE)

    assessment = assess_case(person, make_case(caption="GARCIA, MARIA", date_of_birth=BIRTH_DATE))

    assert assessment.label is MatchLabel.PROBABLE
    assert "Matched through a name variant" in assessment.reasons


def test_exact_name_with_same_birth_date_is_still_confirmed() -> None:
    person = make_person("Maria", "Garcia Lopez", BIRTH_DATE)

    assessment = assess_case(
        person, make_case(caption="GARCIA LOPEZ, MARIA", date_of_birth=BIRTH_DATE)
    )

    assert assessment.label is MatchLabel.CONFIRMED
