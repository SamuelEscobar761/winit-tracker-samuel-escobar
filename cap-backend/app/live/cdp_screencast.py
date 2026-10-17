import asyncio
from typing import Any

from playwright.async_api import CDPSession, Page
from playwright.async_api import Error as PlaywrightError

from app.live.frames import FrameBroadcaster


class CdpScreencast:
    """Streams the JPEG frames Chromium itself produces (`Page.startScreencast`)."""

    def __init__(
        self, frames: FrameBroadcaster, quality: int, every_nth_frame: int, max_width: int
    ) -> None:
        self._frames = frames
        self._quality = quality
        self._every_nth_frame = every_nth_frame
        self._max_width = max_width
        self._session: CDPSession | None = None
        self._pending: set[asyncio.Task[None]] = set()

    async def attach(self, page: Page) -> None:
        self._session = await page.context.new_cdp_session(page)
        self._session.on("Page.screencastFrame", self._on_frame)
        await self._session.send(
            "Page.startScreencast",
            {
                "format": "jpeg",
                "quality": self._quality,
                "everyNthFrame": self._every_nth_frame,
                "maxWidth": self._max_width,
            },
        )

    async def detach(self) -> None:
        if self._session is None:
            return
        for task in self._pending:
            task.cancel()
        try:
            await self._session.send("Page.stopScreencast")
        except Exception:
            return None

    def _on_frame(self, params: dict[str, Any]) -> None:
        task = asyncio.get_running_loop().create_task(self._publish_and_acknowledge(params))
        self._pending.add(task)
        task.add_done_callback(self._pending.discard)

    async def _publish_and_acknowledge(self, params: dict[str, Any]) -> None:
        metadata = params.get("metadata", {})
        width = int(metadata.get("deviceWidth", 0))
        height = int(metadata.get("deviceHeight", 0))
        self._frames.publish(params["data"], width, height)
        if self._session is None:
            return
        try:
            await self._session.send("Page.screencastFrameAck", {"sessionId": params["sessionId"]})
        except PlaywrightError:
            return
