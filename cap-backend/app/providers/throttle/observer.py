from typing import Protocol


class WaitObserver(Protocol):
    def waiting(self, seconds: float) -> None: ...
