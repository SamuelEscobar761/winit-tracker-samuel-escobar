from typing import Any
from urllib.parse import urlsplit

from playwright.async_api import APIRequestContext
from playwright.async_api import Error as PlaywrightError

from app.providers.errors import CapDown
from app.providers.live.page_source import PageSource
from app.rules.registry import RulesRegistry


class PortalHealthChecker:
    def __init__(
        self,
        page_source: PageSource,
        base_url: str,
        timeout_seconds: float,
        rules: RulesRegistry | None = None,
    ) -> None:
        parts = urlsplit(base_url)
        self._rules = rules or RulesRegistry()
        self._origin = f"{parts.scheme}://{parts.netloc}"
        self._page_source = page_source
        self._timeout_ms = timeout_seconds * 1000

    async def check(self) -> None:
        context = await self._page_source.get_request_context()
        rules = self._rules.current
        try:
            in_maintenance = await self._read(context, rules.api.maintenance_path)
            mode = await self._read(context, rules.api.application_mode_path)
        except PlaywrightError as error:
            raise CapDown(f"The portal cannot be reached: {error}") from error
        if (
            _is_maintenance(in_maintenance, rules.responses.data_key)
            or mode != rules.api.normal_mode
        ):
            raise CapDown("The portal is in maintenance or not in normal mode")

    async def _read(self, context: APIRequestContext, path: str) -> Any:
        response = await context.get(self._origin + path, timeout=self._timeout_ms)
        if not response.ok:
            raise CapDown(f"The portal answered HTTP {response.status} for {path}")
        return await response.json()


def _is_maintenance(payload: Any, data_key: str) -> bool:
    return isinstance(payload, dict) and payload.get(data_key) is True
