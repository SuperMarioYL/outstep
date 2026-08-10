"""Core data model for Outstep.

The primitive is the *canary-action battery*. A scenario declares a goal that
invites an out-of-scope action, the tools made available to the model, and an
allowlist of permitted (tool, scope) pairs. The scope oracle checks every
attempted tool call against the allowlist and classifies it as authorized or
unauthorized. Output primitive is the :class:`ContainmentReport`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Verdict = Literal["escaped", "contained"]

DISCLAIMER = (
    "tendency signal, not exhaustive proof — a contained verdict does not mean "
    "the model cannot escape under a longer or different battery"
)


@dataclass
class Rule:
    """A single permitted (tool, scope) entry in a scenario's allowlist.

    ``scope`` is a glob matched against the action's normalized target:
    a filesystem path for ``file_read``, a command string for ``shell_exec``,
    and a hostname for ``http_get``.
    """

    tool: str
    scope: str


@dataclass
class Action:
    """A tool call observed from the model via the instrumented stubs."""

    tool: str
    args: dict
    raw: str = ""

    @property
    def target(self) -> str:
        """Human-readable summary of what the action tried to touch."""
        for key in ("path", "command", "url", "host"):
            if key in self.args:
                return f"{self.tool}({key}={self.args[key]!r})"
        return f"{self.tool}({self.args})"


@dataclass
class Scenario:
    """One escape-attempt canary: goal + available tools + safe-scope allowlist."""

    id: str
    goal: str
    tools: list[str]
    allowlist: list[Rule] = field(default_factory=list)


@dataclass
class ActionResult:
    """Per-scenario outcome: every attempted action + the unauthorized subset."""

    scenario_id: str
    attempted_actions: list[Action]
    unauthorized: list[Action]
    verdict: Verdict


@dataclass
class ContainmentReport:
    """Per-model containment report — the battery's output primitive."""

    model: str
    battery_version: str
    escape_score: tuple[int, int]
    actions: list[ActionResult]
    transcript_hash: str
    disclaimer: str = DISCLAIMER
