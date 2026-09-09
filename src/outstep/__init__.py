"""Outstep — pre-deployment escape-behavior canary probe for open-weight CN models.

The core primitive is the *canary-action battery*: a versioned, declarative set of
escape-attempt scenarios. Each scenario pairs a goal prompt that invites an
out-of-scope action with a tool allowlist. The scope oracle checks every
attempted tool call against that allowlist and emits a machine-checkable
per-model containment report.

v0.2.0 ships battery validation (``--dry`` plus custom YAML files via
``--battery <path>``), a traversal-safe scope oracle, and dry-run report
previews with optional file output (``outstep report --out md --file <path>``).
The live model harness remains unimplemented.
"""

from __future__ import annotations

__version__ = "0.2.0"

__all__ = ["__version__"]
