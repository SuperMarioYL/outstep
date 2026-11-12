"""Version lockstep: package, pyproject, CLI, site and CHANGELOG agree (m7, m12, m16)."""

from __future__ import annotations

import json
import re
from pathlib import Path

from typer.testing import CliRunner

import outstep
from outstep.cli import app

runner = CliRunner()
ROOT = Path(__file__).resolve().parents[1]


def test_dunder_version_is_current():
    assert outstep.__version__ == "0.4.0"


def test_pyproject_version_matches_package():
    match = re.search(
        r'^version\s*=\s*"([^"]+)"',
        (ROOT / "pyproject.toml").read_text(encoding="utf-8"),
        re.MULTILINE,
    )
    assert match, "pyproject.toml [project] version not found"
    assert match.group(1) == outstep.__version__


def test_cli_version_flag_matches_package():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.output.strip() == f"outstep {outstep.__version__}"


def test_site_meta_versions_match_package():
    # web/site.json is a hand-bumped surface; guard both of its version keys so a
    # release that forgets one fails here instead of on the deployed site.
    meta = json.loads((ROOT / "web" / "site.json").read_text(encoding="utf-8"))["meta"]
    assert meta["implementation_version"] == outstep.__version__
    assert meta["content_version"] == f"v{outstep.__version__}"


def test_changelog_head_matches_package():
    # The newest released heading must *equal* the package version, not merely
    # exist: asserting containment is how a stale head survives a version bump.
    headings = re.findall(
        r"^## \[(\d+\.\d+\.\d+)\]", (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"), re.MULTILINE
    )
    assert headings, "CHANGELOG.md has no released version heading"
    assert headings[0] == outstep.__version__
