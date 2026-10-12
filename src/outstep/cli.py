"""Outstep CLI — pre-deployment escape-behavior canary probe.

m1 surface:
    outstep run --dry --battery canary_v1   validate + print the battery plan
    outstep report --out stdout            preview the report format (dry-run)

m2/m3 commands (``run --model``, ``report --out md``, ``compare``) are wired
when those milestones land.
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from outstep import __version__
from outstep.battery import Battery, BatteryError
from outstep.harness import Harness, HarnessNotImplemented
from outstep.models import ContainmentReport, Rule

app = typer.Typer(
    name="outstep",
    help="Pre-deployment escape-behavior canary probe for open-weight CN models.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)
console = Console()


def _version(value: bool) -> None:
    if value:
        console.print(f"outstep {__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=False)
def main(
    version: bool = typer.Option(
        None, "--version", callback=_version, is_eager=True, help="Show version and exit."
    ),
) -> None:
    """Outstep — know whether your open-weight model escapes before you ship."""


def _print_battery(battery: Battery) -> None:
    table = Table(
        title=f"Outstep battery {battery.version} — {len(battery.scenarios)} scenarios"
    )
    table.add_column("#", style="dim", width=4)
    table.add_column("scenario", style="cyan")
    table.add_column("goal", style="white")
    table.add_column("tools", style="magenta")
    table.add_column("allowlist (tool / scope)", style="green")
    for i, s in enumerate(battery.scenarios, 1):
        allow = "\n".join(f"{r.tool}  {r.scope}" for r in s.allowlist) or "—"
        tools = ", ".join(s.tools)
        table.add_row(str(i), s.id, s.goal, tools, allow)
    console.print(table)


@app.command()
def run(
    battery: str = typer.Option(
        "canary_v1", "--battery", "-b", help="Battery name (bundled) or path to a YAML file."
    ),
    model: str = typer.Option(
        None,
        "--model",
        "-m",
        envvar="OUTSTEP_MODEL",
        help="OpenAI-compatible model endpoint URL, e.g. http://localhost:8000/v1",
    ),
    dry: bool = typer.Option(
        False, "--dry", help="Validate the battery and print the plan; do not call a model."
    ),
) -> None:
    """Run a canary-action battery against a model endpoint."""
    try:
        bat = Battery.load(battery)
    except BatteryError as exc:
        console.print(f"[red]battery error:[/red] {exc}")
        raise typer.Exit(code=2) from exc

    bat.validate()
    _print_battery(bat)

    if dry:
        console.print(
            f"\n[green]battery {bat.version} valid:[/green] "
            f"{len(bat.scenarios)} scenarios, {sum(len(s.allowlist) for s in bat.scenarios)} "
            "allowlist rules — no model calls made."
        )
        return

    if not model:
        console.print(
            "[yellow]no --model / OUTSTEP_MODEL set[/yellow] — pass --dry to validate "
            "the battery, or --model <endpoint> to run (m2)."
        )
        raise typer.Exit(code=1)

    try:
        Harness(bat).run(model)
    except HarnessNotImplemented as exc:
        console.print(f"[yellow]{exc}[/yellow]")
        raise typer.Exit(code=0) from exc


@app.command()
def report(
    battery: str = typer.Option("canary_v1", "--battery", "-b"),
    model: str = typer.Option("dry-run", "--model", "-m", envvar="OUTSTEP_MODEL"),
    out: str = typer.Option(
        "stdout", "--out", help="stdout | md | json (rendered format; also used by --file)."
    ),
    file: str = typer.Option(
        None, "--file", help="Write the report in the --out format (md or json) to this path."
    ),
) -> None:
    """Preview or write a containment report (m3 adds the real scorecard)."""
    from outstep.report import dry_run_report, render_stdout, to_json, to_markdown

    try:
        bat = Battery.load(battery)
    except BatteryError as exc:
        console.print(f"[red]battery error:[/red] {exc}")
        raise typer.Exit(code=2) from exc

    rep = dry_run_report(bat, model=model)

    if file:
        if out not in ("md", "json"):
            console.print("[red]--file requires --out md or --out json[/red]")
            raise typer.Exit(code=2)
        target = Path(file)
        if not target.parent.is_dir():
            console.print(f"[red]parent directory does not exist:[/red] {target.parent}")
            raise typer.Exit(code=2)
        if target.exists() and not target.is_file():
            console.print(f"[red]report target is not a regular file:[/red] {target}")
            raise typer.Exit(code=2)
        content = to_markdown(rep) if out == "md" else to_json(rep)
        target.write_text(content + "\n", encoding="utf-8")
        console.print(f"[green]report written:[/green] {target}")
        return

    if out == "json":
        console.print(to_json(rep))
    elif out == "md":
        console.print(to_markdown(rep))
    else:
        render_stdout(rep, console)


@app.command()
def compare(
    reports: list[str] = typer.Argument(
        None,
        help="Two or more JSON report paths written by `outstep report --out json --file`.",
    ),
) -> None:
    """Diff containment reports across 2+ models (m3)."""
    from outstep.compare import CompareError, load_report

    if not reports or len(reports) < 2:
        console.print(
            "[red]compare error:[/red] pass two or more report files, e.g. "
            "`outstep compare deepseek.json qwen.json`"
        )
        raise typer.Exit(code=2)

    loaded = []
    for path in reports:
        try:
            loaded.append(load_report(path))
        except CompareError as exc:
            console.print(f"[red]compare error:[/red] {exc}")
            raise typer.Exit(code=2) from exc

    _print_comparison(loaded)


def _print_comparison(reports: list[ContainmentReport]) -> None:
    from outstep.compare import compare as build_comparison
    from outstep.models import DISCLAIMER

    versions = sorted({r.battery_version for r in reports})
    if len(versions) > 1:
        console.print(
            "[yellow]warning:[/yellow] reports cover different batteries: "
            + ", ".join(versions)
        )
    comparison = build_comparison(reports)
    table = Table(title=f"Outstep compare — {len(reports)} models")
    table.add_column("model", style="cyan")
    table.add_column("battery", style="dim")
    table.add_column("escape score", justify="right")
    table.add_column("escaped scenarios", justify="right", style="red")
    for r in comparison.reports:
        escaped = sum(1 for a in r.actions if a.verdict == "escaped")
        table.add_row(
            r.model,
            r.battery_version,
            f"{r.escape_score[0]}/{r.escape_score[1]}",
            str(escaped),
        )
    console.print(table)
    ranking = ", ".join(f"{m} ({s[0]}/{s[1]})" for m, s in comparison.leaders())
    console.print(f"ranking (fewest unauthorized): [bold]{ranking}[/bold]")

    verdicts = {r.model: {a.scenario_id: a.verdict for a in r.actions} for r in reports}
    matrix = Table(title="per-scenario verdicts")
    matrix.add_column("scenario", style="cyan")
    for r in reports:
        matrix.add_column(r.model)
    for sid in verdicts[reports[0].model]:
        cells = []
        for r in reports:
            v = verdicts[r.model].get(sid, "—")
            cells.append(f"[red]{v}[/red]" if v == "escaped" else v)
        matrix.add_row(sid, *cells)
    console.print(matrix)
    console.print(f"[dim]{DISCLAIMER}[/dim]")


__all__ = ["Rule", "app", "console"]
