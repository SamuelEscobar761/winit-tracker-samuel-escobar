from collections.abc import Awaitable, Callable
from typing import Any

from pydantic import BaseModel

from app.ai.errors import AiUnavailable
from app.ai.model import SchemaT

OfflineHandler = Callable[[str], Awaitable[BaseModel]]


class OfflineModel:
    """Deterministic stand-in used for demos and tests; each agent registers its own handler."""

    name = "offline-mock"

    def __init__(self, handlers: dict[type[Any], OfflineHandler] | None = None) -> None:
        self._handlers = dict(handlers or {})

    def register(self, schema: type[BaseModel], handler: OfflineHandler) -> None:
        self._handlers[schema] = handler

    async def ask(self, system: str, prompt: str, schema: type[SchemaT]) -> SchemaT:
        handler = self._handlers.get(schema)
        if handler is None:
            raise AiUnavailable(f"The offline model cannot answer {schema.__name__}")
        answer = await handler(prompt)
        if not isinstance(answer, schema):
            raise AiUnavailable(f"The offline handler returned {type(answer).__name__}")
        return answer
