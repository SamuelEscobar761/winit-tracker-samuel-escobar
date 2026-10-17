from enum import StrEnum
from typing import Protocol

from pydantic import BaseModel, Field, model_validator

ALLOWED_KEYS = frozenset(
    {"Enter", "Tab", "Backspace", "Escape", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", " "}
)
MAX_TEXT_LENGTH = 200


class InputKind(StrEnum):
    CLICK = "click"
    TEXT = "text"
    KEY = "key"
    SCROLL = "scroll"


class InputEvent(BaseModel):
    type: InputKind
    x: float | None = Field(default=None, ge=0, le=10_000)
    y: float | None = Field(default=None, ge=0, le=10_000)
    text: str | None = Field(default=None, max_length=MAX_TEXT_LENGTH)
    key: str | None = None
    delta_y: float | None = Field(default=None, ge=-5_000, le=5_000)

    @model_validator(mode="after")
    def require_the_fields_of_its_kind(self) -> "InputEvent":
        needs = {
            InputKind.CLICK: self.x is not None and self.y is not None,
            InputKind.TEXT: bool(self.text),
            InputKind.KEY: self.key in ALLOWED_KEYS,
            InputKind.SCROLL: self.delta_y is not None,
        }
        if not needs[self.type]:
            raise ValueError(f"The {self.type.value} event is incomplete or not allowed")
        return self


class InputHandler(Protocol):
    async def handle(self, event: InputEvent) -> None: ...

    async def captcha_cleared(self) -> bool: ...
