import random
from decimal import Decimal
from pathlib import Path

import pytest

from app.cases.parsing.search_parser import parse_search_response
from app.cases.status import CaseStatus
from app.config.settings import Settings
from app.providers.errors import (
    CapDown,
    DetailNotAvailable,
    NoResults,
    ProviderError,
    ProviderTimeout,
    SessionExpired,
)
from app.providers.mock.catalog import load_mock_catalog
from app.providers.mock.failures import (
    FailureRates,
    FailureSchedule,
    NoFailures,
    Operation,
    RandomFailures,
    ScriptedFailures,
)
from app.providers.mock.provider import MockCapProvider, MockLatency
from app.providers.throttle.action_throttle import ActionThrottle
from tests.support.fake_time import FakeTime
from tests.support.fixtures import load_fixture

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"
DELAY = 5.0
LATENCY = MockLatency(search_seconds=0.5, detail_seconds=5.0)


def build_provider(
    fake_time: FakeTime | None = None, failures: FailureSchedule | None = None
) -> MockCapProvider:
    time_source = fake_time or FakeTime()
    return MockCapProvider(
        catalog=load_mock_catalog(FIXTURES),
        throttle=ActionThrottle(DELAY, [], time_source),
        sleeper=time_source,
        failures=failures or NoFailures(),
        latency=LATENCY,
    )


def case_number_with_status(
    status: CaseStatus, fixture: str = "search_pedro_rodriguez.json"
) -> str:
    cases = parse_search_response(load_fixture(fixture))
    return next(case.case_number for case in cases if case.status is status)


async def test_search_returns_the_recorded_pedro_rodriguez_results() -> None:
    response = await build_provider().search("rodriguez, pedro")

    assert len(response.cases) == 193
    assert response.raw_payload == load_fixture("search_pedro_rodriguez.json")


async def test_search_returns_the_recorded_john_smith_results() -> None:
    response = await build_provider().search("smith, john")

    assert len(response.cases) == 286


async def test_first_last_form_is_read_like_the_portal() -> None:
    response = await build_provider().search("Pedro Rodriguez")

    assert len(response.cases) == 193


@pytest.mark.parametrize("query", ["rodriguez pedro", "rodríguez, pedro", "pedro, rodriguez"])
async def test_wrong_order_or_accents_find_nothing_like_the_portal(query: str) -> None:
    with pytest.raises(NoResults):
        await build_provider().search(query)


async def test_unknown_person_finds_nothing() -> None:
    with pytest.raises(NoResults):
        await build_provider().search("nobody, nemo")


async def test_search_costs_three_paced_actions_plus_latency() -> None:
    fake_time = FakeTime()

    await build_provider(fake_time).search("smith, john")

    assert fake_time.now == pytest.approx(3 * DELAY + LATENCY.search_seconds)


async def test_detail_costs_four_paced_actions_plus_latencies() -> None:
    fake_time = FakeTime()
    case_number = case_number_with_status(CaseStatus.ACTIVE)

    await build_provider(fake_time).fetch_detail("rodriguez, pedro", case_number)

    expected = 4 * DELAY + LATENCY.search_seconds + LATENCY.detail_seconds
    assert fake_time.now == pytest.approx(expected)


async def test_recorded_detail_is_returned_for_known_cases() -> None:
    response = await build_provider().fetch_detail("rodriguez, pedro", "26IN-055186")

    assert response.detail.amount_due == Decimal("1665.00")
    assert response.detail.proof_of_correction_required


async def test_case_number_without_hyphen_is_accepted() -> None:
    response = await build_provider().fetch_detail("rodriguez, pedro", "25IN169374")

    assert response.detail.has_payment_plan


async def test_cases_without_a_recording_get_a_deterministic_synthetic_detail() -> None:
    case_number = case_number_with_status(CaseStatus.ACTIVE, "search_john_smith.json")

    first = await build_provider().fetch_detail("smith, john", case_number)
    second = await build_provider().fetch_detail("smith, john", case_number)

    assert first.detail == second.detail
    assert first.detail.amount_due is not None
    assert first.detail.case_key == case_number.replace("-", "").upper()


async def test_ar_fine_cases_use_the_payment_plan_layout() -> None:
    case_number = case_number_with_status(CaseStatus.AR_FINE, "search_john_smith.json")

    response = await build_provider().fetch_detail("smith, john", case_number)

    assert response.detail.has_payment_plan


@pytest.mark.parametrize("status", [CaseStatus.CLOSED, CaseStatus.WARRANT])
async def test_cases_without_a_detail_action_are_refused(status: CaseStatus) -> None:
    case_number = case_number_with_status(status)

    with pytest.raises(DetailNotAvailable):
        await build_provider().fetch_detail("rodriguez, pedro", case_number)


async def test_case_outside_the_results_is_refused() -> None:
    with pytest.raises(DetailNotAvailable):
        await build_provider().fetch_detail("rodriguez, pedro", "99XX-000000")


async def test_scripted_failure_is_raised_once_and_the_next_call_succeeds() -> None:
    provider = build_provider(failures=ScriptedFailures([SessionExpired("expired"), None]))

    with pytest.raises(SessionExpired):
        await provider.search("smith, john")

    assert len((await provider.search("smith, john")).cases) == 286


async def test_failed_action_still_pays_the_delay() -> None:
    fake_time = FakeTime()
    provider = build_provider(fake_time, ScriptedFailures([ProviderTimeout("slow")]))

    with pytest.raises(ProviderTimeout):
        await provider.search("smith, john")

    assert fake_time.now == pytest.approx(2 * DELAY + LATENCY.search_seconds)


async def test_health_check_raises_when_the_portal_is_down() -> None:
    provider = build_provider(failures=ScriptedFailures([CapDown("maintenance")]))

    with pytest.raises(CapDown):
        await provider.check_health()


async def test_health_check_passes_when_nothing_fails() -> None:
    await build_provider().check_health()


def collect_failures(seed: int, calls: int) -> list[type[ProviderError] | None]:
    schedule = RandomFailures(FailureRates.from_total(0.5), random.Random(seed))
    outcomes = (schedule.failure_for(Operation.SEARCH) for _ in range(calls))
    return [type(error) if error else None for error in outcomes]


def test_random_failures_are_reproducible_with_the_same_seed() -> None:
    assert collect_failures(7, 50) == collect_failures(7, 50)
    assert collect_failures(7, 50) != collect_failures(8, 50)


def test_random_failures_cover_every_error_type_at_a_high_rate() -> None:
    kinds = {kind for kind in collect_failures(1, 2000) if kind is not None}

    assert len(kinds) == 4


def test_failure_rates_add_up_to_the_requested_total() -> None:
    rates = FailureRates.from_total(0.2)

    total = rates.session_expired + rates.timeout + rates.captcha + rates.cap_down
    assert total == pytest.approx(0.2)


def test_settings_defaults_provide_a_fast_demo_with_some_failures() -> None:
    settings = Settings()

    assert settings.mock_speed_factor == 10
    assert 0 < settings.mock_failure_rate < 0.5
