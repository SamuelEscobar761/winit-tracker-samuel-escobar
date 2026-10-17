from playwright.async_api import Page

from app.live.input import InputEvent, InputKind

CAPTCHA_SELECTOR = 'iframe[src*="recaptcha"], .g-recaptcha, iframe[title*="reCAPTCHA"]'

CLEAR_POLLS = 20
CLEAR_POLL_MILLISECONDS = 100


class PageInput:
    """Replays a person's own clicks and keystrokes on the lane's page."""

    def __init__(self, page: Page) -> None:
        self._page = page

    async def handle(self, event: InputEvent) -> None:
        if event.type is InputKind.CLICK and event.x is not None and event.y is not None:
            await self._page.mouse.click(event.x, event.y)
        elif event.type is InputKind.TEXT and event.text:
            await self._page.keyboard.type(event.text)
        elif event.type is InputKind.KEY and event.key:
            await self._page.keyboard.press(event.key)
        elif event.type is InputKind.SCROLL and event.delta_y is not None:
            await self._page.mouse.wheel(0, event.delta_y)

    async def captcha_cleared(self) -> bool:
        """A widget needs a moment after the click to disappear, so one click must be enough."""
        for _ in range(CLEAR_POLLS):
            if not await self._page.locator(CAPTCHA_SELECTOR).first.is_visible():
                return True
            await self._page.wait_for_timeout(CLEAR_POLL_MILLISECONDS)
        return False
