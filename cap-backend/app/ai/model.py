from typing import Protocol, TypeVar

from pydantic import BaseModel

SchemaT = TypeVar("SchemaT", bound=BaseModel)


class StructuredModel(Protocol):
    """Anything that can answer a prompt with an object of the requested schema."""

    @property
    def name(self) -> str: ...

    async def ask(self, system: str, prompt: str, schema: type[SchemaT]) -> SchemaT: ...
