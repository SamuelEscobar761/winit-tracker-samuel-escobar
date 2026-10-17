from typing import Protocol

from playwright.async_api import (
    APIRequestContext,
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)

from app.live.cdp_screencast import CdpScreencast
from app.live.lanes import LaneChannel
from app.live.page_input import PageInput


class PageSource(Protocol):
    async def get_page(self) -> Page: ...

    async def get_request_context(self) -> APIRequestContext: ...

    async def aclose(self) -> None: ...


class PlaywrightPageSource:
    """One isolated browser session (own cookies) that starts on first use."""

    def __init__(
        self,
        headless: bool,
        channel: LaneChannel | None = None,
        screencast: CdpScreencast | None = None,
        launch_args: tuple[str, ...] = (),
    ) -> None:
        self._headless = headless
        self._launch_args = list(launch_args)
        self._channel = channel
        self._screencast = screencast
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    async def get_page(self) -> Page:
        if self._page is None or self._page.is_closed():
            context = await self._ensure_context()
            self._page = await context.new_page()
            await self._connect_viewers(self._page)
        return self._page

    async def get_request_context(self) -> APIRequestContext:
        context = await self._ensure_context()
        return context.request

    async def aclose(self) -> None:
        if self._screencast is not None:
            await self._screencast.detach()
        if self._context is not None:
            await self._context.close()
        if self._browser is not None:
            await self._browser.close()
        if self._playwright is not None:
            await self._playwright.stop()
        self._playwright = self._browser = self._context = self._page = None

    async def _connect_viewers(self, page: Page) -> None:
        if self._screencast is not None:
            await self._screencast.attach(page)
        if self._channel is not None:
            self._channel.input_handler = PageInput(page)

    async def _ensure_context(self) -> BrowserContext:
        if self._context is None:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=self._headless, args=self._launch_args
            )
            self._context = await self._browser.new_context()
        return self._context
