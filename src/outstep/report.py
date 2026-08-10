"""Per-model containment report generator (m3).

m1 ships the report *shape* (:class:`outstep.models.ContainmentReport`) and a
dry-run preview. m3 will render a real scorecard — Markdown + JSON, with the
"tendency, not proof" disclaimer and a reproducible transcript hash — from a
harness run, and ``outstep report --out md`` will write it to disk.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from typing import Literal

from rich.console import Console
from rich.table import Table

from outstep.battery import Battery
from outstep.models import ContainmentReport

ReportFormat = Literal["md", "json", "stdout"]


def transcript_hash(battery: Battery, model: str) -> str:
    """Stable hash over (battery_version, model, scenario ids+goals).

    m3 will hash the actual transcript (every model message + tool call). For
    m1 we hash the battery plan so a dry-run report is still reproducible.
    """
    payload = json.dumps(
        {
            "battery_version": battery.version,
            "model": model,
            "scenarios": [
                {"id": s.id, "goal": s.goal, "tools": s.tools}
                for s in battery.scenarios
            ],
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def dry_run_report(battery: Battery, model: str = "dry-run") -> ContainmentReport:
    """A containment report for the plan itself (no model calls yet).

    Every scenario is ``contained`` by construction — nothing was attempted.
    This is the artifact ``outstep run --dry`` previews so the report format is
    visible before m2/m3 land.
    """
    from outstep.models import ActionResult

    actions = [
        ActionResult(
            scenario_id=s.id,
            attempted_actions=[],
            unauthorized=[],
            verdict="contained",
        )
        for s in battery.scenarios
    ]
    return ContainmentReport(
        model=model,
        battery_version=battery.version,
        escape_score=(0, len(battery.scenarios)),
        actions=actions,
        transcript_hash=transcript_hash(battery, model),
    )


def to_json(report: ContainmentReport) -> str:
    return json.dumps(asdict(report), ensure_ascii=False, indent=2)


def to_markdown(report: ContainmentReport) -> str:
    lines = [
        f"# Outstep containment report — {report.model}",
        "",
        f"- **battery**: `{report.battery_version}`",
        f"- **escape score**: {report.escape_score[0]}/{report.escape_score[1]} unauthorized actions attempted",
        f"- **transcript**: `{report.transcript_hash}`",
        "",
        f"> {report.disclaimer}",
        "",
        "| scenario | verdict | unauthorized |",
        "|---|---|---|",
    ]
    for a in report.actions:
        unauth = ", ".join(u.target for u in a.unauthorized) or "—"
        lines.append(f"| {a.scenario_id} | {a.verdict} | {unauth} |")
    return "\n".join(lines)


def render_stdout(report: ContainmentReport, console: Console) -> None:
    table = Table(title=f"Outstep containment report — {report.model}")
    table.add_column("scenario", style="cyan")
    table.add_column("verdict", style="green")
    table.add_column("unauthorized", style="red")
    for a in report.actions:
        unauth = ", ".join(u.target for u in a.unauthorized) or "—"
        table.add_row(a.scenario_id, a.verdict, unauth)
    console.print(table)
    console.print(
        f"escape score: [bold]{report.escape_score[0]}/{report.escape_score[1]}[/bold] "
        f"unauthorized · battery `{report.battery_version}` · "
        f"transcript `{report.transcript_hash}`"
    )
    console.print(f"[dim]{report.disclaimer}[/dim]")
