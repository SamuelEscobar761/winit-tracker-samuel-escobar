from dataclasses import dataclass

from app.csv_import.models import FileIssue, FileIssueCode, Severity


class CsvFileError(Exception):
    def __init__(self, issue: FileIssue) -> None:
        super().__init__(issue.message)
        self.issue = issue


@dataclass(frozen=True)
class DecodedText:
    text: str
    encoding: str
    used_fallback: bool


def decode_csv_bytes(data: bytes) -> DecodedText:
    if b"\x00" in data:
        raise CsvFileError(_error(FileIssueCode.BINARY_FILE, "The file is binary, not CSV text"))
    try:
        return DecodedText(data.decode("utf-8-sig"), "utf-8", used_fallback=False)
    except UnicodeDecodeError:
        return DecodedText(data.decode("latin-1"), "latin-1", used_fallback=True)


def _error(code: FileIssueCode, message: str) -> FileIssue:
    return FileIssue(code=code, severity=Severity.ERROR, message=message)
