class PortalResponseError(Exception):
    def __init__(self, result: int, message: str) -> None:
        super().__init__(f"Portal answered result={result}: {message}")
        self.result = result
        self.message = message

    @property
    def is_session_expired(self) -> bool:
        return "session expired" in self.message.lower()

    @property
    def is_no_results(self) -> bool:
        return self.message.lower().startswith("no case")


class MalformedResponseError(Exception):
    pass
