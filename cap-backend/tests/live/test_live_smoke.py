from pathlib import Path

import pytest

from app.tools.live_smoke import build_settings, parse_arguments, run
from tests.support.fake_portal import FakePortal


async def test_smoke_tool_runs_one_person_and_records_the_raw_json(
    portal: FakePortal,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("CAP_BASE_URL", portal.base_url)
    monkeypatch.setenv("CAP_ACTION_DELAY_SECONDS", "0")
    arguments = parse_arguments(
        ["Pedro", "Rodriguez", "--details", "1", "--record", str(tmp_path), "--yes"]
    )

    exit_code = await run(arguments, build_settings(arguments))

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Kept 188 cases" in output
    assert (tmp_path / "search_rodriguez_pedro.json").exists()
    assert list(tmp_path.glob("select_*.json"))


async def test_smoke_tool_reports_people_without_cases(
    portal: FakePortal, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("CAP_BASE_URL", portal.base_url)
    monkeypatch.setenv("CAP_ACTION_DELAY_SECONDS", "0")
    arguments = parse_arguments(["Nemo", "Nobody", "--yes"])

    exit_code = await run(arguments, build_settings(arguments))

    assert exit_code == 0
    assert "found no cases" in capsys.readouterr().out
