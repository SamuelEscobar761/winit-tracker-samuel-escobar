from pydantic import BaseModel

from app.ai.errors import AiUnavailable
from app.ai.model import SchemaT
from app.rules.healing.proposals import CanaryResult
from app.rules.models import PortalRules


class ScriptedModel:
    name = "scripted"

    def __init__(self, answer: BaseModel | Exception) -> None:
        self._answer = answer
        self.prompts: list[str] = []

    async def ask(self, system: str, prompt: str, schema: type[SchemaT]) -> SchemaT:
        self.prompts.append(prompt)
        if isinstance(self._answer, Exception):
            raise self._answer
        assert isinstance(self._answer, schema)
        return self._answer


class BrokenModel(ScriptedModel):
    def __init__(self) -> None:
        super().__init__(AiUnavailable("down"))


class FixedCanary:
    def __init__(self, passed: bool) -> None:
        self._passed = passed
        self.verified: list[PortalRules] = []

    async def verify(self, candidate: PortalRules) -> CanaryResult:
        self.verified.append(candidate)
        return CanaryResult(passed=self._passed, detail="fixed")
