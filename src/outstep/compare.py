"""Cross-model comparison (m3).

The tractable, offline half of m3: compare containment reports that were
written to disk by ``outstep report --out json --file``. A comparison is a
list of containment reports keyed by model name; ``Comparison.leaders()``
ranks them best-first. The side-by-side rendering lives in the CLI.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from outstep.models import DISCLAIMER, Action, ActionResult, ContainmentReport

# Keys a saved report must carry to be diffable.
_REQUIRED_KEYS = ("model", "battery_version", "escape_score", "actions", "transcript_hash")


class CompareError(ValueError):
    """Raised when a saved report file is missing, unreadable, or malformed."""


def _actions_from_json(entries: object, field: str) -> list[Action]:
    if not isinstance(entries, list):
        raise CompareError(f"report field {field!r} must be a list of actions")
    actions: list[Action] = []
    for entry in entries:
        if not isinstance(entry, dict) or "tool" not in entry:
            raise CompareError(f"each entry in {field!r} must be a mapping with a 'tool' key")
        args = entry.get("args", {})
        if not isinstance(args, dict):
            raise CompareError(f"action 'args' in {field!r} must be a mapping")
        actions.append(
            Action(tool=str(entry["tool"]), args=dict(args), raw=str(entry.get("raw", "")))
        )
    return actions


def report_from_json(payload: object) -> ContainmentReport:
    """Rebuild a :class:`ContainmentReport` from a ``to_json`` payload.

    Raises :class:`CompareError` when the payload is not a well-formed report.
    """
    if not isinstance(payload, dict):
        raise CompareError("report must be a JSON object")
    missing = [key for key in _REQUIRED_KEYS if key not in payload]
    if missing:
        raise CompareError(f"report is missing required keys: {', '.join(missing)}")
    score = payload["escape_score"]
    if (
        not isinstance(score, list)
        or len(score) != 2
        or not all(isinstance(n, int) and not isinstance(n, bool) for n in score)
    ):
        raise CompareError(
            f"escape_score must be an [unauthorized, total] pair, got {score!r}"
        )
    if not isinstance(payload["actions"], list):
        raise CompareError("'actions' must be a list of per-scenario results")
    results: list[ActionResult] = []
    for entry in payload["actions"]:
        if not isinstance(entry, dict) or "scenario_id" not in entry or "verdict" not in entry:
            raise CompareError(
                "each entry in 'actions' must be a mapping with 'scenario_id' and 'verdict'"
            )
        if entry["verdict"] not in ("escaped", "contained"):
            raise CompareError(f"invalid verdict {entry['verdict']!r} (escaped|contained)")
        attempted = _actions_from_json(entry.get("attempted_actions", []), "attempted_actions")
        unauthorized = _actions_from_json(entry.get("unauthorized", []), "unauthorized")
        results.append(
            ActionResult(
                scenario_id=str(entry["scenario_id"]),
                attempted_actions=attempted,
                unauthorized=unauthorized,
                verdict=str(entry["verdict"]),
            )
        )
    return ContainmentReport(
        model=str(payload["model"]),
        battery_version=str(payload["battery_version"]),
        escape_score=(score[0], score[1]),
        actions=results,
        transcript_hash=str(payload["transcript_hash"]),
        disclaimer=str(payload.get("disclaimer", DISCLAIMER)),
    )


def load_report(path: str | Path) -> ContainmentReport:
    """Load a containment report written by ``outstep report --out json --file``."""
    report_path = Path(path)
    if not report_path.is_file():
        raise CompareError(f"report file not found or not a regular file: {report_path}")
    try:
        text = report_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise CompareError(f"cannot read report file {report_path}: {exc}") from exc
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise CompareError(f"report file is not valid JSON: {report_path} ({exc})") from exc
    return report_from_json(payload)


@dataclass
class Comparison:
    """A set of per-model containment reports to be diffed."""

    reports: list[ContainmentReport]

    def leaders(self) -> list[tuple[str, tuple[int, int]]]:
        """Models ranked best-first (fewest unauthorized attempts)."""
        return sorted(
            ((r.model, r.escape_score) for r in self.reports),
            key=lambda kv: kv[1][0],
        )


def compare(reports: list[ContainmentReport]) -> Comparison:
    return Comparison(reports=reports)
