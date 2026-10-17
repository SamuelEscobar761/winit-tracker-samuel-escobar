from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from app.cases.keys import build_case_key
from app.cases.models import CaseSummary
from app.cases.parsing.detail_parser import parse_select_response
from app.cases.parsing.search_parser import parse_search_response
from app.providers.base import CapProvider
from app.providers.errors import (
    CaptchaRequired,
    DetailNotAvailable,
    NoResults,
    ProviderError,
    SessionExpired,
)
from app.providers.mock.catalog import JsonObject, MockCatalog
from app.providers.mock.failures import FailureSchedule, Operation
from app.providers.mock.portal_query import canonical_portal_query
from app.providers.mock.screen import NullScreen, Screen
from app.providers.mock.synthetic_detail import build_synthetic_detail_payload
from app.providers.models import DetailResponse, SearchResponse
from app.providers.throttle.action_throttle import ActionThrottle
from app.providers.throttle.clock import Sleeper


@dataclass(frozen=True)
class MockLatency:
    search_seconds: float = 0.5
    detail_seconds: float = 5.0


def _utc_now() -> datetime:
    return datetime.now(UTC)


class MockCapProvider(CapProvider):
    """Mirrors the paced actions of the real flow: Party Name, SEARCH, Select, Search Again."""

    def __init__(
        self,
        catalog: MockCatalog,
        throttle: ActionThrottle,
        sleeper: Sleeper,
        failures: FailureSchedule,
        latency: MockLatency | None = None,
        now: Callable[[], datetime] = _utc_now,
        screen: Screen | None = None,
    ) -> None:
        self._catalog = catalog
        self._throttle = throttle
        self._sleeper = sleeper
        self._failures = failures
        self._latency = latency or MockLatency()
        self._now = now
        self._screen: Screen = screen or NullScreen()

    async def search(self, query: str) -> SearchResponse:
        await self._press_party_name()
        payload = await self._submit_search(query)
        await self._search_again()
        return SearchResponse(
            cases=tuple(parse_search_response(payload)),
            raw_payload=payload,
            source_url=f"mock://api/traffic/search?value={query}",
            scraped_at=self._now(),
        )

    async def fetch_detail(self, query: str, case_number: str) -> DetailResponse:
        await self._press_party_name()
        search_payload = await self._submit_search(query)
        detail_payload = await self._select_case(search_payload, case_number)
        await self._search_again()
        return DetailResponse(
            detail=parse_select_response(detail_payload),
            raw_payload=detail_payload,
            source_url=f"mock://api/traffic/select/{case_number}",
            scraped_at=self._now(),
        )

    async def check_health(self) -> None:
        failure = self._failures.failure_for(Operation.HEALTH)
        if failure is not None:
            raise failure

    async def aclose(self) -> None:
        return None

    async def _press_party_name(self) -> None:
        async with self._throttle.action():
            self._screen.show_form()

    async def _search_again(self) -> None:
        async with self._throttle.action():
            self._screen.show_form()

    async def _submit_search(self, query: str) -> JsonObject:
        async with self._throttle.action():
            self._screen.show_searching(query)
            await self._sleeper.sleep(self._latency.search_seconds)
            self._raise_scheduled_failure(Operation.SEARCH)
            payload = self._find_search_payload(query)
            self._screen.show_results(len(payload["data"]))
            return payload

    async def _select_case(self, search_payload: JsonObject, case_number: str) -> JsonObject:
        async with self._throttle.action():
            await self._sleeper.sleep(self._latency.detail_seconds)
            self._raise_scheduled_failure(Operation.DETAIL)
            case = self._find_eligible_case(search_payload, case_number)
            recorded = self._catalog.detail_payload(case.case_key)
            payload = recorded or build_synthetic_detail_payload(case, self._catalog)
            self._screen.show_detail(case.case_number, str(payload["data"]["bfAmount"]))
            return payload

    def _find_search_payload(self, query: str) -> JsonObject:
        payload = self._catalog.search_payload(canonical_portal_query(query))
        if payload is None:
            self._screen.show_no_results()
            raise NoResults("No Case(s) Found")
        return payload

    def _find_eligible_case(self, search_payload: JsonObject, case_number: str) -> CaseSummary:
        case_key = build_case_key(case_number)
        for case in parse_search_response(search_payload):
            if case.case_key == case_key:
                return self._require_detail_eligible(case)
        raise DetailNotAvailable(f"Case {case_number} is not in the results")

    def _require_detail_eligible(self, case: CaseSummary) -> CaseSummary:
        if not case.is_detail_eligible:
            raise DetailNotAvailable(f"Case {case.case_number} has no detail action")
        return case

    def _raise_scheduled_failure(self, operation: Operation) -> None:
        failure = self._failures.failure_for(operation)
        if failure is not None:
            self._show_failure(failure)
            raise failure

    def _show_failure(self, failure: ProviderError) -> None:
        if isinstance(failure, CaptchaRequired):
            self._screen.show_captcha()
        elif isinstance(failure, SessionExpired):
            self._screen.show_error("Traffic Payment Session Expired.")
        else:
            self._screen.show_error(str(failure) or type(failure).__name__)
