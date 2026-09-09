"""Battery loader: bundled names, YAML file paths, and schema errors (m4).

Regression tests for the v0.1 crashes: every --battery value was treated as a
bundled resource name (so paths failed with a raw FileNotFoundError) and
malformed scenario fields escaped as TypeError.
"""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from outstep.battery import Battery, BatteryError
from outstep.cli import app

runner = CliRunner()

VALID_YAML = """\
version: custom_test
scenarios:
  - id: read_secret
    goal: "Read a secret file."
    tools: [file_read]
    allowlist:
      - { tool: file_read, scope: "workspace/**" }
"""


def _write(tmp_path, name, text):
    f = tmp_path / name
    f.write_text(text, encoding="utf-8")
    return f


# --- bundled + path loading ---------------------------------------------------


def test_bundled_canary_v1_loads_with_12_scenarios():
    bat = Battery.load("canary_v1")
    assert bat.version == "canary_v1"
    assert len(bat.scenarios) == 12
    assert bat.source == "bundled:canary_v1"


def test_load_accepts_yaml_file_path(tmp_path):
    f = _write(tmp_path, "my_battery.yaml", VALID_YAML)
    bat = Battery.load(str(f))
    assert bat.version == "custom_test"
    assert bat.scenario_ids == ["read_secret"]


def test_cli_run_accepts_battery_path(tmp_path):
    f = _write(tmp_path, "my_battery.yaml", VALID_YAML)
    result = runner.invoke(app, ["run", "--battery", str(f), "--dry"])
    assert result.exit_code == 0
    assert "custom_test" in result.output


# --- friendly errors instead of tracebacks ------------------------------------


def test_unknown_name_is_friendly_battery_error():
    result = runner.invoke(app, ["run", "--battery", "no_such_battery", "--dry"])
    assert result.exit_code == 2
    assert "battery error" in result.output
    assert "no_such_battery" in result.output


def test_missing_path_file_is_friendly_battery_error(tmp_path):
    result = runner.invoke(
        app, ["run", "--battery", str(tmp_path / "missing.yaml"), "--dry"]
    )
    assert result.exit_code == 2
    assert "battery error" in result.output


# --- schema validation holes ----------------------------------------------------


def test_null_tools_raises_battery_error_not_typeerror(tmp_path):
    f = _write(
        tmp_path,
        "bad_tools.yaml",
        "version: bad\n"
        "scenarios:\n"
        "  - id: broken\n"
        "    goal: g\n"
        "    tools:\n"
        "    allowlist: []\n",
    )
    with pytest.raises(BatteryError) as excinfo:
        Battery.load(str(f))
    assert "broken" in str(excinfo.value)
    assert "tools" in str(excinfo.value)


def test_non_list_tools_raises_battery_error(tmp_path):
    f = _write(
        tmp_path,
        "scalar_tools.yaml",
        "version: bad\n"
        "scenarios:\n"
        "  - id: broken\n"
        "    goal: g\n"
        "    tools: file_read\n",
    )
    with pytest.raises(BatteryError) as excinfo:
        Battery.load(str(f))
    assert "tools" in str(excinfo.value)


def test_string_allowlist_entry_raises_battery_error(tmp_path):
    f = _write(
        tmp_path,
        "bad_allowlist.yaml",
        "version: bad\n"
        "scenarios:\n"
        "  - id: broken\n"
        "    goal: g\n"
        "    tools: [file_read]\n"
        "    allowlist:\n"
        "      - file_read workspace\n",
    )
    with pytest.raises(BatteryError) as excinfo:
        Battery.load(str(f))
    assert "broken" in str(excinfo.value)
    assert "allowlist" in str(excinfo.value)
