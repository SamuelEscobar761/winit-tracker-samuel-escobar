from typing import Protocol


class Screen(Protocol):
    def show_form(self) -> None: ...

    def show_searching(self, query: str) -> None: ...

    def show_results(self, total: int) -> None: ...

    def show_no_results(self) -> None: ...

    def show_detail(self, case_number: str, amount: str) -> None: ...

    def show_error(self, message: str) -> None: ...

    def show_captcha(self) -> None: ...


class NullScreen:
    def show_form(self) -> None:
        return None

    def show_searching(self, query: str) -> None:
        return None

    def show_results(self, total: int) -> None:
        return None

    def show_no_results(self) -> None:
        return None

    def show_detail(self, case_number: str, amount: str) -> None:
        return None

    def show_error(self, message: str) -> None:
        return None

    def show_captcha(self) -> None:
        return None
