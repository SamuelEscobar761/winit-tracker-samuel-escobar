from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolate_environment_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
