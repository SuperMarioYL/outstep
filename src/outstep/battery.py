"""Battery loader — turns a versioned YAML file into validated scenarios.

m1 deliverable: ``outstep run --dry --battery canary_v1`` validates and prints
all 12 scenarios with their allowlists.
"""

from __future__ import annotations

import os
from importlib import resources
from pathlib import Path
from typing import Any

import yaml

from outstep.models import Rule, Scenario

_BUILTIN = {"canary_v1"}


def _looks_like_path(name: str) -> bool:
    """True when a --battery value refers to a file rather than a bundled name."""
    return name.endswith((".yaml", ".yml")) or "/" in name or os.sep in name or "\\" in name


class BatteryError(ValueError):
    """Raised when a battery file is malformed or semantically invalid."""


class Battery:
    """A versioned canary-action battery."""

    def __init__(self, version: str, scenarios: list[Scenario], source: str = "") -> None:
        self.version = version
        self.scenarios = scenarios
        self.source = source

    @classmethod
    def load(cls, name: str, path: str | None = None) -> Battery:
        """Load a battery by short name (``canary_v1``) or path to a YAML file."""
        if path is not None:
            return cls._from_file(Path(path), source=str(path))
        if _looks_like_path(name):
            # --battery may point at a file, e.g. ``--battery ./my_battery.yaml``
            return cls._from_file(Path(name), source=name)
        # bundled battery: src/outstep/scenarios/<name>.yaml
        try:
            res = resources.files("outstep.scenarios").joinpath(f"{name}.yaml")
        except ModuleNotFoundError as exc:  # pragma: no cover - packaging guard
            raise BatteryError(f"cannot locate bundled scenario package: {exc}") from exc
        try:
            with res.open("r", encoding="utf-8") as fh:
                return cls._from_dict(yaml.safe_load(fh), source=f"bundled:{name}")
        except FileNotFoundError as exc:
            raise BatteryError(
                f"battery not found: {name!r} is neither a bundled battery "
                f"(no scenarios/{name}.yaml) nor an existing YAML file"
            ) from exc

    @classmethod
    def _from_file(cls, path: Path, source: str) -> Battery:
        if not path.exists():
            raise BatteryError(f"battery file not found: {path}")
        return cls._from_dict(yaml.safe_load(path.read_text(encoding="utf-8")), source=source)

    @classmethod
    def _from_dict(cls, data: Any, source: str) -> Battery:
        if not isinstance(data, dict):
            raise BatteryError("battery root must be a mapping")
        version = data.get("version") or data.get("battery_version")
        if not version:
            raise BatteryError("battery is missing a 'version' field")
        raw_scenarios = data.get("scenarios")
        if not isinstance(raw_scenarios, list) or not raw_scenarios:
            raise BatteryError("battery must declare a non-empty 'scenarios' list")
        scenarios: list[Scenario] = []
        for item in raw_scenarios:
            scenarios.append(_scenario_from_dict(item))
        bat = cls(version=version, scenarios=scenarios, source=source)
        bat.validate()
        return bat

    def validate(self) -> bool:
        """Enforce invariants: unique ids, non-empty goal/tools, sane allowlist."""
        ids = [s.id for s in self.scenarios]
        dupes = {i for i in ids if ids.count(i) > 1}
        if dupes:
            raise BatteryError(f"duplicate scenario ids: {sorted(dupes)}")
        for s in self.scenarios:
            if not s.id or not s.goal or not s.tools:
                raise BatteryError(f"scenario {s.id!r} is missing id/goal/tools")
            for r in s.allowlist:
                if r.tool not in s.tools:
                    raise BatteryError(
                        f"scenario {s.id!r}: allowlist references tool {r.tool!r} "
                        f"not declared in tools {s.tools}"
                    )
        return True

    @property
    def scenario_ids(self) -> list[str]:
        return [s.id for s in self.scenarios]


def _scenario_from_dict(data: Any) -> Scenario:
    if not isinstance(data, dict):
        raise BatteryError("each scenario must be a mapping")
    try:
        sid = data["id"]
        goal = data["goal"]
        tools = data["tools"]
    except KeyError as exc:
        raise BatteryError(f"scenario missing required field: {exc}") from exc
    if sid is None or goal is None:
        raise BatteryError(f"scenario {sid!r}: 'id' and 'goal' must be non-null")
    if (
        not isinstance(tools, list)
        or not tools
        or not all(isinstance(t, str) and t for t in tools)
    ):
        raise BatteryError(
            f"scenario {sid!r}: 'tools' must be a non-empty list of tool names"
        )
    raw_allowlist = data.get("allowlist", [])
    if not isinstance(raw_allowlist, list):
        raise BatteryError(f"scenario {sid!r}: 'allowlist' must be a list")
    allowlist: list[Rule] = []
    for entry in raw_allowlist:
        if not isinstance(entry, dict) or "tool" not in entry or "scope" not in entry:
            raise BatteryError(
                f"scenario {sid!r}: allowlist entries must be mappings with "
                "'tool' and 'scope' fields"
            )
        allowlist.append(Rule(tool=str(entry["tool"]), scope=str(entry["scope"])))
    return Scenario(id=str(sid), goal=str(goal), tools=list(tools), allowlist=allowlist)
