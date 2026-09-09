"""``outstep report --file`` writes scorecards to disk (m6)."""

from __future__ import annotations

import json

from typer.testing import CliRunner

from outstep.cli import app

runner = CliRunner()


def test_report_md_writes_markdown_file(tmp_path):
    out_file = tmp_path / "report.md"
    result = runner.invoke(app, ["report", "--out", "md", "--file", str(out_file)])
    assert result.exit_code == 0
    text = out_file.read_text(encoding="utf-8")
    assert text.startswith("# Outstep containment report")
    assert "escape score" in text
    assert "canary_v1" in text


def test_report_json_writes_parseable_json(tmp_path):
    out_file = tmp_path / "report.json"
    result = runner.invoke(app, ["report", "--out", "json", "--file", str(out_file)])
    assert result.exit_code == 0
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["model"] == "dry-run"
    assert data["battery_version"] == "canary_v1"
    assert data["escape_score"] == [0, 12]
    assert len(data["actions"]) == 12


def test_report_file_requires_md_or_json_format(tmp_path):
    result = runner.invoke(
        app, ["report", "--out", "stdout", "--file", str(tmp_path / "r.md")]
    )
    assert result.exit_code == 2
    assert "--file requires" in result.output


def test_report_file_rejects_missing_parent_directory(tmp_path):
    result = runner.invoke(
        app, ["report", "--out", "md", "--file", str(tmp_path / "nope" / "r.md")]
    )
    assert result.exit_code == 2
    assert "parent directory" in result.output


def test_report_without_file_prints_to_stdout_only(tmp_path):
    result = runner.invoke(app, ["report", "--out", "json"])
    assert result.exit_code == 0
    assert "escape_score" in result.output
    assert not any(tmp_path.iterdir())
