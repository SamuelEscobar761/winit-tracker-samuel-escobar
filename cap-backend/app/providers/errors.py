from typing import Any, ClassVar


class ProviderError(Exception):
    retryable: ClassVar[bool] = True


class NoResults(ProviderError):
    retryable: ClassVar[bool] = False


class SessionExpired(ProviderError):
    pass


class ProviderTimeout(ProviderError):
    pass


class CapDown(ProviderError):
    retryable: ClassVar[bool] = False


class CaptchaRequired(ProviderError):
    retryable: ClassVar[bool] = False


class DetailNotAvailable(ProviderError):
    retryable: ClassVar[bool] = False


class UnparsedLayout(ProviderError):
    retryable: ClassVar[bool] = False

    def __init__(
        self,
        message: str,
        raw_snapshot: str | None = None,
        evidence: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.raw_snapshot = raw_snapshot
        self.evidence = evidence or {}


class NoSearchableQuery(ProviderError):
    retryable: ClassVar[bool] = False


class BrowserError(ProviderError):
    pass
