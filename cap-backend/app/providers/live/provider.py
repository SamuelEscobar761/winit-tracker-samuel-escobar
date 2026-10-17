import json
import re
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any, TypeVar

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import Locator
from playwright.async_api import TimeoutError as PlaywrightTimeout

from app.cases.keys import build_case_key
from app.cases.models import CaseSummary
from app.cases.parsing.detail_parser import parse_select_response
from app.cases.parsing.errors import MalformedResponseError, PortalResponseError
from app.cases.parsing.search_parser import parse_search_response
from app.providers.base import CapProvider
from app.providers.errors import (
    BrowserError,
    CaptchaRequired,
    DetailNotAvailable,
    NoResults,
    ProviderError,
    ProviderTimeout,
    SessionExpired,
    UnparsedLayout,
)
from app.providers.live.health import PortalHealthChecker
from app.providers.live.page_source import PageSource
from app.providers.live.portal_page import PortalPage
from app.providers.models import DetailResponse, SearchResponse
from app.providers.throttle.action_throttle import ActionThrottle
from app.rules.healing.evidence import json_skeleton
from app.rules.healing.incidents import IncidentKind
from app.rules.healing.monitor import DriftReporter
from app.rules.models import ResponseRules
from app.rules.registry import RulesRegistry

T = TypeVar("T")
JsonPayload = dict[str, Any]


def _utc_now() -> datetime:
    return datetime.now(UTC)


class LiveCapProvider(CapProvider):
    """Drives the real page and reads the JSON the page itself receives; it only ever clicks
    Party Name, SEARCH, the Select of a result row and Search Again."""

    def __init__(
        self,
        page_source: PageSource,
        throttle: ActionThrottle,
        health: PortalHealthChecker,
        base_url: str,
        response_timeout_seconds: float,
        now: Callable[[], datetime] = _utc_now,
        rules: RulesRegistry | None = None,
        drift: DriftReporter | None = None,
    ) -> None:
        self._rules = rules or RulesRegistry()
        self._drift = drift
        self._page_source = page_source
        self._throttle = throttle
        self._health = health
        self._base_url = base_url
        self._timeout_ms = response_timeout_seconds * 1000
        self._now = now

    async def search(self, query: str) -> SearchResponse:
        portal = await self._portal()
        return await self._guard(portal, lambda: self._search(portal, query))

    async def fetch_detail(self, query: str, case_number: str) -> DetailResponse:
        portal = await self._portal()
        return await self._guard(portal, lambda: self._fetch_detail(portal, query, case_number))

    async def check_health(self) -> None:
        async with self._throttle.action():
            await self._health.check()

    async def aclose(self) -> None:
        await self._page_source.aclose()

    async def _portal(self) -> PortalPage:
        page = await self._page_source.get_page()
        page.set_default_timeout(self._timeout_ms)
        return PortalPage(page, self._rules.current.ui)

    async def _search(self, portal: PortalPage, query: str) -> SearchResponse:
        payload, url = await self._submit_query(portal, query)
        cases = self._read_cases(payload)
        await self._return_to_start(portal)
        return SearchResponse(tuple(cases), payload, url, self._now())

    async def _fetch_detail(
        self, portal: PortalPage, query: str, case_number: str
    ) -> DetailResponse:
        payload, _ = await self._submit_query(portal, query)
        case = self._require_eligible(self._read_cases(payload), case_number)
        button = portal.select_button_for(case.case_number)
        detail_payload, url = await self._click_and_capture(
            portal, button, self._rules.current.api.select_path_prefix
        )
        detail = self._read_detail(detail_payload)
        await self._return_to_start(portal)
        return DetailResponse(detail, detail_payload, url, self._now())

    async def _submit_query(self, portal: PortalPage, query: str) -> tuple[JsonPayload, str]:
        await self._go_to_party_name_form(portal)
        await portal.fill_query(query)
        return await self._click_and_capture(
            portal, portal.search_button, self._rules.current.api.search_path
        )

    async def _go_to_party_name_form(self, portal: PortalPage) -> None:
        """After any error the page may be on another step, so the position is checked first."""
        if not await portal.is_on_search_form():
            await self._recover_to_search_form(portal)
        if not await portal.party_name_selected():
            async with self._throttle.action():
                await portal.click_party_name()

    async def _recover_to_search_form(self, portal: PortalPage) -> None:
        async with self._throttle.action():
            if await portal.search_again_visible():
                await portal.click_search_again()
            else:
                await portal.open(self._base_url, self._timeout_ms)
        if not await portal.is_on_search_form():
            error = BrowserError("The search form did not appear")
            await self._report_drift("ui", error, portal)
            raise error

    async def _click_and_capture(
        self, portal: PortalPage, button: Locator, url_part: str
    ) -> tuple[JsonPayload, str]:
        async with self._throttle.action():
            async with portal.raw.expect_response(
                lambda response: url_part in response.url, timeout=self._timeout_ms
            ) as waiter:
                await button.click(timeout=self._timeout_ms)
            response = await waiter.value
            if not response.ok:
                raise BrowserError(f"The portal answered HTTP {response.status}")
            payload: JsonPayload = await response.json()
        await self._raise_if_captcha(portal)
        return payload, response.url

    async def _return_to_start(self, portal: PortalPage) -> None:
        async with self._throttle.action():
            await portal.click_search_again()

    def _read_cases(self, payload: JsonPayload) -> list[CaseSummary]:
        try:
            cases = parse_search_response(payload, self._rules.current)
        except PortalResponseError as error:
            raise _translate_portal_error(error, self._rules.current.responses) from error
        except MalformedResponseError as error:
            raise _unparsed(error, payload) from error
        if not cases:
            raise NoResults("No Case(s) Found")
        return cases

    def _read_detail(self, payload: JsonPayload) -> Any:
        try:
            return parse_select_response(payload, self._rules.current)
        except PortalResponseError as error:
            raise _translate_portal_error(error, self._rules.current.responses) from error
        except MalformedResponseError as error:
            raise _unparsed(error, payload) from error

    def _require_eligible(self, cases: list[CaseSummary], case_number: str) -> CaseSummary:
        case_key = build_case_key(case_number)
        case = next((item for item in cases if item.case_key == case_key), None)
        if case is None:
            raise DetailNotAvailable(f"Case {case_number} is not in the results")
        if not case.is_detail_eligible:
            raise DetailNotAvailable(f"Case {case_number} has no detail action")
        return case

    async def _guard(self, portal: PortalPage, operation: Callable[[], Awaitable[T]]) -> T:
        try:
            return await operation()
        except UnparsedLayout as error:
            await self._report_drift("response", error, portal)
            raise
        except ProviderError:
            raise
        except PlaywrightTimeout as error:
            raise await self._timeout_or_captcha(portal, error) from error
        except PlaywrightError as error:
            raise BrowserError(str(error)) from error

    async def _timeout_or_captcha(self, portal: PortalPage, error: Exception) -> ProviderError:
        try:
            if await portal.captcha_visible():
                return CaptchaRequired("The portal asked for a CAPTCHA")
        except PlaywrightError:
            pass
        await self._report_drift("ui", error, portal)
        return ProviderTimeout(str(error))

    async def _report_drift(self, kind: IncidentKind, error: Exception, portal: PortalPage) -> None:
        if self._drift is None:
            return
        evidence = dict(getattr(error, "evidence", {}))
        evidence.update(await _safe_controls(portal))
        message = " ".join(str(error).split())[:600] or type(error).__name__
        await self._drift.report(kind, message, evidence)

    async def _raise_if_captcha(self, portal: PortalPage) -> None:
        if await portal.captcha_visible():
            raise CaptchaRequired("The portal asked for a CAPTCHA")


async def _safe_controls(portal: PortalPage) -> dict[str, Any]:
    try:
        return await portal.describe_controls()
    except PlaywrightError:
        return {}


def _translate_portal_error(error: PortalResponseError, rules: ResponseRules) -> ProviderError:
    if _matches(rules.no_results_pattern, error.message):
        return NoResults(error.message)
    if _matches(rules.session_expired_pattern, error.message):
        return SessionExpired(error.message)
    return UnparsedLayout(f"Unexpected portal answer {error.result}: {error.message}")


def _unparsed(error: MalformedResponseError, payload: JsonPayload) -> UnparsedLayout:
    evidence = {"payload_skeleton": json_skeleton(payload)}
    return UnparsedLayout(str(error), json.dumps(payload)[:2000], evidence)


def _matches(pattern: str, message: str) -> bool:
    return re.search(pattern, message, re.IGNORECASE) is not None
