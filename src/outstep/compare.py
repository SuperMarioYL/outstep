"""Cross-model comparison (m3).

m1 ships the *contract*: a comparison is a list of containment reports keyed by
model name. m3 will render the side-by-side scorecard — escape-score per model,
per-scenario pass/fail matrix — and ``outstep compare <a> <b> --battery v1``
will produce the launch artifact (the "I ran the same escape battery on Kimi-K3
/ DeepSeek-V4 / Qwen3.8" scorecard).
"""

from __future__ import annotations

from dataclasses import dataclass

from outstep.models import ContainmentReport


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
