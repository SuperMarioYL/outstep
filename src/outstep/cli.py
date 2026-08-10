"""Outstep CLI — pre-deployment escape-behavior canary probe.

m1 surface:
    outstep run --dry --battery canary_v1   validate + print the battery plan
    outstep report --out stdout            preview the report format (dry-run)

m2/m3 commands (``run --model``, ``report --out md``, ``compare``) are wired
when those milestones land.
"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from outstep import __version__
from outstep.battery import Battery, BatteryError
from outstep.harness import Harness, HarnessNotImplemented
from outstep.models import Rule

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
        "stdout", "--out", help="stdout | md | json (m3 adds file output)."
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
    if out == "json":
        console.print(to_json(rep))
    elif out == "md":
        console.print(to_markdown(rep))
    else:
        render_stdout(rep, console)


@app.command()
def compare(
    models: list[str] = typer.Argument(None, help="Two or more model names to diff (m3)."),
    battery: str = typer.Option("canary_v1", "--battery", "-b"),
) -> None:
    """Diff containment reports across 2+ models (m3)."""
    console.print(
        "[yellow]outstep compare ships in m3[/yellow] — v0.1 emits per-model "
        "reports only. The side-by-side scorecard lands with m3."
    )
    console.print(
        f"configured for battery [cyan]{battery}[/cyan] "
        f"against models: {', '.join(models) or '(none)'}"
    )


__all__ = ["Rule", "app", "console"]
