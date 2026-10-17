from decimal import Decimal

import pytest

from app.cases.parsing.search_parser import parse_search_response
from app.cases.status import CaseStatus
from app.providers.errors import (
    CapDown,
    CaptchaRequired,
    DetailNotAvailable,
    NoResults,
    ProviderTimeout,
    SessionExpired,
)
from app.providers.live.provider import LiveCapProvider
from tests.live.conftest import ACTION_DELAY
from tests.support.fake_portal import FakePortal
from tests.support.fake_time import FakeTime
from tests.support.fixtures import load_fixture


def case_number_with_status(status: CaseStatus) -> str:
    cases = parse_search_response(load_fixture("search_pedro_rodriguez.json"))
    return next(case.case_number for case in cases if case.status is status)


async def test_search_reads_the_json_the_page_receives(
    live_provider: LiveCapProvider, portal: FakePortal
) -> None:
    response = await live_provider.search("rodriguez, pedro")

    assert len(response.cases) == 193
    assert response.raw_payload["message"] == "Found 193 Case(s)"
    assert response.source_url.endswith("/api/traffic/search")
    assert "POST /api/traffic/search" in portal.state.calls


async def test_first_search_also_opens_the_portal(
    live_provider: LiveCapProvider, fake_time: FakeTime
) -> None:
    await live_provider.search("smith, john")

    assert fake_time.now == pytest.approx(4 * ACTION_DELAY)


async def test_first_last_form_reaches_the_same_results(live_provider: LiveCapProvider) -> None:
    response = await live_provider.search("Pedro Rodriguez")

    assert len(response.cases) == 193


@pytest.mark.parametrize("empty_as_error", [True, False])
async def test_empty_results_are_reported_in_both_possible_shapes(
    live_provider: LiveCapProvider, portal: FakePortal, empty_as_error: bool
) -> None:
    portal.state.empty_result_as_error = empty_as_error

    with pytest.raises(NoResults):
        await live_provider.search("nobody, nemo")


async def test_party_name_is_selected_again_before_every_search(
    live_provider: LiveCapProvider, fake_time: FakeTime
) -> None:
    await live_provider.search("smith, john")
    before = fake_time.now

    await live_provider.search("rodriguez, pedro")

    assert fake_time.now - before == pytest.approx(3 * ACTION_DELAY)


async def test_first_detail_opens_the_portal_and_reads_the_select_response(
    live_provider: LiveCapProvider, fake_time: FakeTime
) -> None:
    response = await live_provider.fetch_detail("rodriguez, pedro", "26IN-055186")

    assert response.detail.amount_due == Decimal("1665.00")
    assert response.detail.proof_of_correction_required
    assert response.source_url.endswith("/api/traffic/select/26IN-055186")
    assert fake_time.now == pytest.approx(5 * ACTION_DELAY)


async def test_payment_controls_are_never_clicked(
    live_provider: LiveCapProvider, portal: FakePortal
) -> None:
    await live_provider.fetch_detail("rodriguez, pedro", "26IN-055186")

    assert not any("pay" in call for call in portal.state.calls)


async def test_cases_without_a_detail_action_are_refused_before_clicking_anything(
    live_provider: LiveCapProvider, portal: FakePortal
) -> None:
    for status in (CaseStatus.CLOSED, CaseStatus.WARRANT):
        with pytest.raises(DetailNotAvailable):
            await live_provider.fetch_detail("rodriguez, pedro", case_number_with_status(status))

    assert not any("/api/traffic/select/" in call for call in portal.state.calls)


async def test_expired_session_is_reported_and_the_next_call_recovers(
    live_provider: LiveCapProvider, portal: FakePortal
) -> None:
    portal.state.session_expired = True

    with pytest.raises(SessionExpired):
        await live_provider.search("rodriguez, pedro")

    portal.state.session_expired = False
    response = await live_provider.search("rodriguez, pedro")
    assert len(response.cases) == 193


async def test_error_while_opening_a_case_leaves_the_provider_usable(
    live_provider: LiveCapProvider, portal: FakePortal
) -> None:
    original_is_valid = portal.state.is_valid
    calls_seen = {"select": 0}

    def expire_on_select(token: str | None) -> bool:
        if any("/api/traffic/select/" in call for call in portal.state.calls):
            calls_seen["select"] += 1
            return False
        return original_is_valid(token)

    portal.state.is_valid = expire_on_select  # type: ignore[method-assign]
    with pytest.raises(SessionExpired):
        await live_provider.fetch_detail("rodriguez, pedro", "26IN-055186")

    portal.state.is_valid = original_is_valid  # type: ignore[method-assign]
    response = await live_provider.search("smith, john")
    assert len(response.cases) == 286


async def test_a_captcha_on_the_page_is_reported_for_a_human(
    live_provider: LiveCapProvider, portal: FakePortal
) -> None:
    portal.state.show_captcha = True

    with pytest.raises(CaptchaRequired):
        await live_provider.search("rodriguez, pedro")

    portal.state.show_captcha = False
    assert len((await live_provider.search("rodriguez, pedro")).cases) == 193


async def test_a_portal_that_does_not_answer_in_time_is_a_timeout(
    live_provider: LiveCapProvider, portal: FakePortal
) -> None:
    portal.state.search_delay_seconds = 7.0

    with pytest.raises(ProviderTimeout):
        await live_provider.search("rodriguez, pedro")


async def test_health_passes_in_normal_mode(live_provider: LiveCapProvider) -> None:
    await live_provider.check_health()


@pytest.mark.parametrize(
    ("maintenance", "mode"), [(True, "NORMAL"), (False, "MAINTENANCE"), (False, "READONLY")]
)
async def test_maintenance_or_other_modes_mean_the_portal_is_down(
    live_provider: LiveCapProvider, portal: FakePortal, maintenance: bool, mode: str
) -> None:
    portal.state.maintenance = maintenance
    portal.state.application_mode = mode

    with pytest.raises(CapDown):
        await live_provider.check_health()


async def test_an_unreachable_portal_means_the_portal_is_down(
    live_provider: LiveCapProvider, portal: FakePortal
) -> None:
    portal.stop()

    with pytest.raises(CapDown):
        await live_provider.check_health()
