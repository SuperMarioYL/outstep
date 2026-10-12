"""``outstep compare`` over saved JSON report files (m11)."""

from __future__ import annotations

import json

from typer.testing import CliRunner

from outstep.cli import app
from outstep.compare import load_report

runner = CliRunner()


def _write_reports(tmp_path, *models):
    paths = []
    for model in models:
        out_file = tmp_path / f"report_{model}.json"
        result = runner.invoke(
            app, ["report", "--model", model, "--out", "json", "--file", str(out_file)]
        )
        assert result.exit_code == 0
        paths.append(out_file)
    return paths


def test_compare_two_reports_renders_scorecard(tmp_path):
    a, b = _write_reports(tmp_path, "deepseek-v4", "qwen3.8")
    result = runner.invoke(app, ["compare", str(a), str(b)])
    assert result.exit_code == 0
    assert "deepseek-v4" in result.output
    assert "qwen3.8" in result.output
    assert "0/12" in result.output
    assert "ranking (fewest unauthorized)" in result.output
    assert "per-scenario verdicts" in result.output


def test_compare_rejects_a_single_report(tmp_path):
    (a,) = _write_reports(tmp_path, "solo")
    result = runner.invoke(app, ["compare", str(a)])
    assert result.exit_code == 2
    assert "compare error" in result.output


def test_compare_rejects_missing_file(tmp_path):
    result = runner.invoke(app, ["compare", str(tmp_path / "a.json"), str(tmp_path / "b.json")])
    assert result.exit_code == 2
    assert "compare error" in result.output


def test_compare_rejects_malformed_report(tmp_path):
    good, _ = _write_reports(tmp_path, "m1", "m2")
    bad = tmp_path / "bad.json"
    payload = json.loads(good.read_text(encoding="utf-8"))
    del payload["model"]
    bad.write_text(json.dumps(payload), encoding="utf-8")
    result = runner.invoke(app, ["compare", str(bad), str(good)])
    assert result.exit_code == 2
    assert "compare error" in result.output
    assert "model" in result.output


def test_compare_warns_on_battery_version_mismatch(tmp_path):
    a, b = _write_reports(tmp_path, "m1", "m2")
    other = tmp_path / "other.json"
    payload = json.loads(a.read_text(encoding="utf-8"))
    payload["battery_version"] = "custom_v9"
    payload["model"] = "m3"
    other.write_text(json.dumps(payload), encoding="utf-8")
    result = runner.invoke(app, ["compare", str(other), str(b)])
    assert result.exit_code == 0
    assert "different batteries" in result.output


def test_load_report_round_trips_to_json_payload(tmp_path):
    (a,) = _write_reports(tmp_path, "roundtrip")
    report = load_report(str(a))
    assert report.model == "roundtrip"
    assert report.battery_version == "canary_v1"
    assert report.escape_score == (0, 12)
    assert len(report.actions) == 12
