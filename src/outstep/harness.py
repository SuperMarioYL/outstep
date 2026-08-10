"""Tool-calling driver loop (m2).

m1 leaves this as a stub: ``outstep run --dry`` validates the battery and
prints the plan without driving a model. m2 will wire the OpenAI-compatible
tool-calling loop here — one round-trip per scenario, dispatching each model
tool call through the :mod:`outstep.tools` stubs and collecting the call log
for the :mod:`outstep.observer` oracle.
"""

from __future__ import annotations

from dataclasses import dataclass

from outstep.battery import Battery


class HarnessNotImplemented(NotImplementedError):
    """m2 milestone — instrumented harness not yet wired."""


@dataclass
class Harness:
    """Drives a battery against a single OpenAI-compatible model endpoint."""

    battery: Battery

    def run(self, model: str) -> None:  # pragma: no cover - m2 territory
        raise HarnessNotImplemented(
            "m2: instrumented harness not implemented. v0.1 ships `--dry` "
            "battery validation only; the tool-calling driver lands in m2."
        )
