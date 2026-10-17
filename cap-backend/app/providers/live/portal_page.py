from typing import Any

from playwright.async_api import Locator, Page
from playwright.async_api import TimeoutError as PlaywrightTimeout

from app.rules.models import UiRules

FORM_WAIT_MILLISECONDS = 3000


class PortalPage:
    """The only place that knows how the `/traffic` page looks; it never touches payments."""

    def __init__(self, page: Page, ui: UiRules) -> None:
        self._page = page
        self._ui = ui

    @property
    def raw(self) -> Page:
        return self._page

    @property
    def search_button(self) -> Locator:
        return self._page.locator(self._ui.search_button)

    @property
    def _party_name_button(self) -> Locator:
        return self._page.get_by_role("button", name=self._ui.party_name_button)

    @property
    def _search_again_button(self) -> Locator:
        return self._page.get_by_role("button", name=self._ui.search_again_button)

    async def open(self, url: str, timeout_ms: float) -> None:
        await self._page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")

    async def is_on_search_form(self) -> bool:
        try:
            await self._page.locator(self._ui.query_input).wait_for(
                state="visible", timeout=FORM_WAIT_MILLISECONDS
            )
        except PlaywrightTimeout:
            return False
        return True

    async def party_name_selected(self) -> bool:
        classes = await self._party_name_button.get_attribute("class") or ""
        return self._ui.selected_button_class in classes.split()

    async def click_party_name(self) -> None:
        await self._party_name_button.click()

    async def fill_query(self, query: str) -> None:
        await self._page.locator(self._ui.query_input).fill(query)

    def select_button_for(self, case_number: str) -> Locator:
        rows = self._page.locator(self._ui.results_rows)
        row = rows.filter(has=self._page.get_by_role("cell", name=case_number, exact=True))
        return row.get_by_role("button", name=self._ui.select_button)

    async def search_again_visible(self) -> bool:
        return await self._search_again_button.first.is_visible()

    async def click_search_again(self) -> None:
        await self._search_again_button.first.click()

    async def captcha_visible(self) -> bool:
        return await self._page.locator(self._ui.captcha).first.is_visible()

    async def describe_controls(self) -> dict[str, Any]:
        """Labels, ids and API paths only; never the text of cases or the values typed in."""
        description: dict[str, Any] = await self._page.evaluate(DESCRIBE_CONTROLS_SCRIPT)
        return description


DESCRIBE_CONTROLS_SCRIPT = """() => {
  const text = (element) => (element.innerText || '').trim().slice(0, 40);
  const pick = (selector, read) =>
    Array.from(document.querySelectorAll(selector)).slice(0, 25).map(read);
  const apiPaths = performance.getEntriesByType('resource')
    .map((entry) => new URL(entry.name).pathname)
    .filter((path) => path.includes('/api/'));
  return {
    buttons: pick('button, a.btn, input[type=submit]', (e) => ({
      label: text(e) || e.value || '', type: e.type || '', classes: e.className || ''
    })),
    inputs: pick('input:not([type=hidden]), select, textarea', (e) => ({
      id: e.id || '', name: e.name || '', type: e.type || '', placeholder: e.placeholder || ''
    })),
    tables: pick('table', (e) => ({
      classes: e.className || '', headers: Array.from(e.querySelectorAll('th')).map(text),
      rows: e.querySelectorAll('tbody tr').length
    })),
    api_paths_seen: Array.from(new Set(apiPaths)).slice(-20)
  };
}"""
