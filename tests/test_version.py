"""Version lockstep: package, pyproject, and CLI agree (m7)."""

from __future__ import annotations

import re
from pathlib import Path

from typer.testing import CliRunner

import outstep
from outstep.cli import app

runner = CliRunner()


def test_dunder_version_is_020():
    assert outstep.__version__ == "0.2.0"


def test_pyproject_version_matches_package():
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    match = re.search(
        r'^version\s*=\s*"([^"]+)"', pyproject.read_text(encoding="utf-8"), re.MULTILINE
    )
    assert match, "pyproject.toml [project] version not found"
    assert match.group(1) == outstep.__version__


def test_cli_version_flag_matches_package():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.output.strip() == f"outstep {outstep.__version__}"
