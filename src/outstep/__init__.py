"""Outstep — pre-deployment escape-behavior canary probe for open-weight CN models.

The core primitive is the *canary-action battery*: a versioned, declarative set of
escape-attempt scenarios. Each scenario pairs a goal prompt that invites an
out-of-scope action with a tool allowlist. The scope oracle checks every
attempted tool call against that allowlist and emits a machine-checkable
per-model containment report.

v0.1 ships m1 (battery + data model + loader + ``--dry`` validation). m2
(instrumented harness) and m3 (report/compare) follow.
"""

from __future__ import annotations

__version__ = "0.1.0"

__all__ = ["__version__"]
