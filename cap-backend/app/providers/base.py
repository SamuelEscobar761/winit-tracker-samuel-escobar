from abc import ABC, abstractmethod

from app.providers.models import DetailResponse, SearchResponse


class CapProvider(ABC):
    @abstractmethod
    async def search(self, query: str) -> SearchResponse:
        """Raises NoResults when the portal finds nothing for a well-formed query."""

    @abstractmethod
    async def fetch_detail(self, query: str, case_number: str) -> DetailResponse:
        """The query is needed because the portal can only open a case from its own results."""

    @abstractmethod
    async def check_health(self) -> None:
        """Raises CapDown when the portal is in maintenance or not in normal mode."""

    @abstractmethod
    async def aclose(self) -> None:
        pass
