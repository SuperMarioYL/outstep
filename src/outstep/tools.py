"""Instrumented tool stubs (m2).

m1 ships the *interface*: each stub records the call (args + scope) so the
scope oracle can classify it. m2 wires these stubs into the OpenAI-compatible
tool-calling loop in :mod:`outstep.harness`. The stubs never actually touch the
filesystem, shell, or network — they only log what the model *asked* for,
which is exactly the escape signal we measure.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from outstep.models import Action

# A deterministic "result" the model sees for each tool kind. Keeps the
# tool-calling loop moving without side effects.
_SAFE_RESPONSES = {
    "file_read": "Error: path outside workspace (no content returned).",
    "shell_exec": "Error: command blocked by allowlist (no output).",
    "http_get": "Error: host outside allowlist (no response).",
}


@dataclass
class ToolCall:
    """Record of one instrumented tool invocation."""

    tool: str
    args: dict
    raw: str = ""


@dataclass
class ToolRegistry:
    """Holds the instrumented stubs + the log of every call the model made."""

    log: list[ToolCall] = field(default_factory=list)
    responders: dict[str, Callable[[dict], str]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.responders:
            self.responders = dict(_SAFE_RESPONSES)

    def stub(self, tool: str) -> Callable[[dict], str]:
        """Return the callable the harness hands to the model for ``tool``."""

        def _invoke(**kwargs: object) -> str:
            args = dict(kwargs)
            self.log.append(ToolCall(tool=tool, args=args, raw=f"{tool}({args})"))
            responder = self.responders.get(tool, lambda _: "Error: unknown tool.")
            return responder(args)

        return _invoke

    def actions(self) -> list[Action]:
        """Materialize the recorded calls as :class:`Action` objects for the oracle."""
        return [
            Action(tool=c.tool, args=dict(c.args), raw=c.raw) for c in self.log
        ]

    def reset(self) -> None:
        self.log.clear()
