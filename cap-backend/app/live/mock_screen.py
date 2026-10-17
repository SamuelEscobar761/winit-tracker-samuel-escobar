import base64
import io

from PIL import Image, ImageDraw, ImageFont

from app.live.frames import FrameBroadcaster
from app.live.input import InputEvent, InputKind

WIDTH = 800
HEIGHT = 500
CAPTCHA_BOX = (270, 250, 310, 290)

_BACKGROUND = (245, 245, 245)
_BAR = (36, 40, 46)
_HEADER = (221, 232, 238)
_TEXT = (40, 52, 66)
_ACCENT = (46, 94, 148)
_ALERT = (176, 52, 52)


class MockScreen:
    """Draws what the browser of a lane would show, in the same frame format as the live view."""

    def __init__(self, frames: FrameBroadcaster, quality: int) -> None:
        self._frames = frames
        self._quality = quality
        self._captcha_cleared = False

    def show_form(self) -> None:
        self._captcha_cleared = False
        self._publish("CASE PAYMENT SEARCH", ["Step 1 - Search", "Party Name  [ Last, First ]"])

    def show_searching(self, query: str) -> None:
        self._publish("CASE PAYMENT SEARCH", ["Searching...", f"Party Name: {query}"])

    def show_results(self, total: int) -> None:
        self._publish("SEARCH RESULTS", ["Step 2 - Select Case", f"Found {total} Case(s)"])

    def show_no_results(self) -> None:
        self._publish("CASE PAYMENT SEARCH", ["No Case(s) Found"])

    def show_detail(self, case_number: str, amount: str) -> None:
        self._publish("CASE PAYMENT OPTIONS", [f"Case {case_number}", f"Amount due: {amount}"])

    def show_error(self, message: str) -> None:
        self._publish("CASE PAYMENT", [message], alert=True)

    def show_captcha(self) -> None:
        self._captcha_cleared = False
        self._publish("CASE PAYMENT", ["Please verify you are human"], captcha=True)

    async def handle(self, event: InputEvent) -> None:
        if event.type is InputKind.CLICK and self._is_inside_captcha_box(event):
            self._captcha_cleared = True
            self._publish(
                "CASE PAYMENT", ["Verified. You can continue."], captcha=True, checked=True
            )

    async def captcha_cleared(self) -> bool:
        return self._captcha_cleared

    def _is_inside_captcha_box(self, event: InputEvent) -> bool:
        left, top, right, bottom = CAPTCHA_BOX
        return (
            event.x is not None
            and event.y is not None
            and (left <= event.x <= right and top <= event.y <= bottom)
        )

    def _publish(
        self,
        title: str,
        lines: list[str],
        alert: bool = False,
        captcha: bool = False,
        checked: bool = False,
    ) -> None:
        image = Image.new("RGB", (WIDTH, HEIGHT), _BACKGROUND)
        draw = ImageDraw.Draw(image)
        self._draw_chrome(draw, title)
        self._draw_lines(draw, lines, alert)
        if captcha:
            self._draw_captcha(draw, checked)
        self._frames.publish(self._encode(image), WIDTH, HEIGHT)

    def _draw_chrome(self, draw: ImageDraw.ImageDraw, title: str) -> None:
        draw.rectangle((0, 0, WIDTH, 80), fill=_HEADER)
        draw.text((24, 22), "Court Access Portal", fill=_ACCENT, font=_font(30))
        draw.text((24, 105), title, fill=_TEXT, font=_font(22))

    def _draw_lines(self, draw: ImageDraw.ImageDraw, lines: list[str], alert: bool) -> None:
        color = _ALERT if alert else _TEXT
        for position, line in enumerate(lines):
            draw.text((24, 160 + position * 34), line, fill=color, font=_font(22))

    def _draw_captcha(self, draw: ImageDraw.ImageDraw, checked: bool) -> None:
        left, top, right, bottom = CAPTCHA_BOX
        draw.rounded_rectangle((250, 235, 560, 305), radius=6, outline=(160, 160, 160), width=2)
        draw.rectangle(CAPTCHA_BOX, outline=_TEXT, width=2, fill=(255, 255, 255))
        if checked:
            draw.line((left + 8, top + 20, left + 18, bottom - 10), fill=(20, 140, 60), width=4)
            draw.line((left + 18, bottom - 10, right - 6, top + 8), fill=(20, 140, 60), width=4)
        draw.text((330, 260), "I'm not a robot", fill=_TEXT, font=_font(18))

    def _encode(self, image: Image.Image) -> str:
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=self._quality)
        return base64.b64encode(buffer.getvalue()).decode("ascii")


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    return ImageFont.load_default(size=size)
