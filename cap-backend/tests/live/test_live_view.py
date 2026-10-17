import base64

from app.live.cdp_screencast import CdpScreencast
from app.live.input import InputEvent, InputKind
from app.live.lanes import LaneChannel
from app.providers.live.health import PortalHealthChecker
from app.providers.live.page_source import PlaywrightPageSource
from app.providers.live.provider import LiveCapProvider
from app.providers.throttle.action_throttle import ActionThrottle
from tests.support.fake_portal import FakePortal
from tests.support.fake_time import FakeTime


async def test_the_real_browser_streams_jpeg_frames_and_accepts_a_persons_input(
    portal: FakePortal, fake_time: FakeTime
) -> None:
    channel = LaneChannel(lane=0)
    screencast = CdpScreencast(channel.frames, quality=50, every_nth_frame=1, max_width=800)
    source = PlaywrightPageSource(True, channel, screencast)
    provider = LiveCapProvider(
        source,
        ActionThrottle(0.0, [], fake_time),
        PortalHealthChecker(source, portal.base_url, 5.0),
        portal.base_url,
        5.0,
    )
    try:
        await provider.search("smith, john")
        frame = channel.frames.latest
        assert frame is not None
        assert base64.b64decode(frame.data_base64).startswith(b"\xff\xd8")
        assert frame.width > 0 and frame.height > 0

        page = await source.get_page()
        box = await page.locator("#party").bounding_box()
        assert box is not None and channel.input_handler is not None
        click = InputEvent(
            type=InputKind.CLICK, x=box["x"] + box["width"] / 2, y=box["y"] + box["height"] / 2
        )
        await channel.input_handler.handle(click)
        selected = await page.locator("#party").get_attribute("class")
        assert "btn-primary" in (selected or "")
    finally:
        await provider.aclose()


async def test_typed_text_reaches_the_page_and_a_cleared_captcha_is_detected(
    portal: FakePortal, fake_time: FakeTime
) -> None:
    channel = LaneChannel(lane=0)
    source = PlaywrightPageSource(True, channel, None)
    provider = LiveCapProvider(
        source,
        ActionThrottle(0.0, [], fake_time),
        PortalHealthChecker(source, portal.base_url, 5.0),
        portal.base_url,
        5.0,
    )
    try:
        await provider.search("smith, john")
        page = await source.get_page()
        assert channel.input_handler is not None

        await page.locator("#number").click()
        await channel.input_handler.handle(InputEvent(type=InputKind.TEXT, text="abc"))
        await channel.input_handler.handle(InputEvent(type=InputKind.KEY, key="Tab"))

        assert await page.locator("#number").input_value() == "abc"
        assert await channel.input_handler.captcha_cleared()
    finally:
        await provider.aclose()
