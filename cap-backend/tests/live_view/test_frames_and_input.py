import asyncio
import base64

import pytest
from pydantic import ValidationError

from app.live.frames import FrameBroadcaster
from app.live.input import InputEvent
from app.live.mock_screen import CAPTCHA_BOX, HEIGHT, WIDTH, MockScreen


def decode(data_base64: str) -> bytes:
    return base64.b64decode(data_base64)


def test_latest_frame_is_kept_and_sequences_increase() -> None:
    broadcaster = FrameBroadcaster(lane=2)

    first = broadcaster.publish("AAAA", 10, 10)
    second = broadcaster.publish("BBBB", 10, 10)

    assert (first.sequence, second.sequence) == (1, 2)
    assert broadcaster.latest == second
    assert second.lane == 2


async def test_a_slow_viewer_only_ever_sees_the_newest_frame() -> None:
    broadcaster = FrameBroadcaster(lane=0)
    with broadcaster.subscribe() as queue:
        for number in range(5):
            broadcaster.publish(f"frame-{number}", 1, 1)

        frame = await asyncio.wait_for(queue.get(), 1.0)

        assert frame.data_base64 == "frame-4"
        assert queue.empty()


async def test_new_viewers_start_with_the_current_frame() -> None:
    broadcaster = FrameBroadcaster(lane=0)
    broadcaster.publish("current", 1, 1)

    with broadcaster.subscribe() as queue:
        assert (await asyncio.wait_for(queue.get(), 1.0)).data_base64 == "current"


async def test_viewers_are_independent_and_removed_when_they_leave() -> None:
    broadcaster = FrameBroadcaster(lane=0)
    with broadcaster.subscribe() as first, broadcaster.subscribe() as second:
        broadcaster.publish("x", 1, 1)
        assert first.get_nowait().data_base64 == second.get_nowait().data_base64 == "x"

    broadcaster.publish("y", 1, 1)
    assert first.empty() and second.empty()


@pytest.mark.parametrize(
    "payload",
    [
        {"type": "click", "x": 10, "y": 20},
        {"type": "text", "text": "hello"},
        {"type": "key", "key": "Enter"},
        {"type": "scroll", "delta_y": -120},
    ],
)
def test_complete_input_events_are_accepted(payload: dict[str, object]) -> None:
    assert InputEvent.model_validate(payload).type.value == payload["type"]


@pytest.mark.parametrize(
    "payload",
    [
        {"type": "click"},
        {"type": "click", "x": -1, "y": 5},
        {"type": "text", "text": ""},
        {"type": "text", "text": "a" * 500},
        {"type": "key", "key": "F12"},
        {"type": "key", "key": "Control+W"},
        {"type": "scroll"},
        {"type": "drag", "x": 1, "y": 1},
    ],
)
def test_incomplete_or_unsafe_input_events_are_rejected(payload: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        InputEvent.model_validate(payload)


def build_screen() -> tuple[MockScreen, FrameBroadcaster]:
    broadcaster = FrameBroadcaster(lane=0)
    return MockScreen(broadcaster, quality=50), broadcaster


def test_mock_frames_are_jpeg_images_of_a_fixed_size() -> None:
    screen, broadcaster = build_screen()

    screen.show_results(193)

    frame = broadcaster.latest
    assert frame is not None
    assert decode(frame.data_base64).startswith(b"\xff\xd8")
    assert (frame.width, frame.height) == (WIDTH, HEIGHT)


def test_every_screen_publishes_a_new_frame() -> None:
    screen, broadcaster = build_screen()

    screen.show_form()
    screen.show_searching("smith, john")
    screen.show_results(3)
    screen.show_no_results()
    screen.show_detail("26IN-055186", "1,665.00")
    screen.show_error("Traffic Payment Session Expired.")
    screen.show_captcha()

    assert broadcaster.latest is not None and broadcaster.latest.sequence == 7


async def test_clicking_the_captcha_box_clears_it() -> None:
    screen, _ = build_screen()
    screen.show_captcha()
    left, top, right, bottom = CAPTCHA_BOX

    await screen.handle(InputEvent(type="click", x=(left + right) / 2, y=(top + bottom) / 2))

    assert await screen.captcha_cleared()


async def test_clicking_elsewhere_does_not_clear_the_captcha() -> None:
    screen, _ = build_screen()
    screen.show_captcha()

    await screen.handle(InputEvent(type="click", x=5, y=5))

    assert not await screen.captcha_cleared()


async def test_a_new_form_resets_the_captcha() -> None:
    screen, _ = build_screen()
    screen.show_captcha()
    await screen.handle(InputEvent(type="click", x=290, y=270))

    screen.show_form()

    assert not await screen.captcha_cleared()
