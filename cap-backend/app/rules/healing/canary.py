from collections.abc import Callable
from typing import Protocol

from app.providers.base import CapProvider
from app.providers.errors import ProviderError
from app.rules.healing.proposals import CanaryResult
from app.rules.models import PortalRules
from app.rules.registry import RulesRegistry


class Canary(Protocol):
    async def verify(self, candidate: PortalRules) -> CanaryResult: ...


class SearchCanary:
    """Runs one harmless search with the candidate rules before they replace the active ones."""

    def __init__(self, build_provider: Callable[[RulesRegistry], CapProvider], query: str) -> None:
        self._build_provider = build_provider
        self._query = query

    async def verify(self, candidate: PortalRules) -> CanaryResult:
        provider = self._build_provider(RulesRegistry(initial=candidate))
        try:
            response = await provider.search(self._query)
        except ProviderError as error:
            return CanaryResult(passed=False, detail=f"{type(error).__name__}: {error}")
        finally:
            await provider.aclose()
        if not response.cases:
            return CanaryResult(passed=False, detail="The canary search returned no cases")
        return CanaryResult(
            passed=True, detail=f"The canary search returned {len(response.cases)} cases"
        )
