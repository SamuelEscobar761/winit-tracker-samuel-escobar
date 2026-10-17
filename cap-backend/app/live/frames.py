import asyncio
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass


@dataclass(frozen=True)
class Frame:
    lane: int
    sequence: int
    data_base64: str
    width: int
    height: int
    mime_type: str = "image/jpeg"


class FrameBroadcaster:
    """Keeps only the newest frame for each viewer, so a slow viewer never slows the scraper."""

    def __init__(self, lane: int) -> None:
        self._lane = lane
        self._sequence = 0
        self._latest: Frame | None = None
        self._queues: set[asyncio.Queue[Frame]] = set()

    @property
    def latest(self) -> Frame | None:
        return self._latest

    def publish(self, data_base64: str, width: int, height: int) -> Frame:
        self._sequence += 1
        frame = Frame(self._lane, self._sequence, data_base64, width, height)
        self._latest = frame
        for queue in self._queues:
            self._replace_pending(queue, frame)
        return frame

    @contextmanager
    def subscribe(self) -> Iterator[asyncio.Queue[Frame]]:
        queue: asyncio.Queue[Frame] = asyncio.Queue(maxsize=1)
        if self._latest is not None:
            queue.put_nowait(self._latest)
        self._queues.add(queue)
        try:
            yield queue
        finally:
            self._queues.discard(queue)

    def _replace_pending(self, queue: asyncio.Queue[Frame], frame: Frame) -> None:
        if queue.full():
            queue.get_nowait()
        queue.put_nowait(frame)
