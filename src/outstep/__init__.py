"""Outstep — pre-deployment escape-behavior canary probe for open-weight CN models.

The core primitive is the *canary-action battery*: a versioned, declarative set of
escape-attempt scenarios. Each scenario pairs a goal prompt that invites an
out-of-scope action with a tool allowlist. The scope oracle checks every
attempted tool call against that allowlist and emits a machine-checkable
per-model containment report.

v0.4.0 ships a scope oracle that also refuses shell_exec commands carrying
output redirection, a ``compare`` per-scenario matrix that shows every scenario
any report contains, and strict ``report --out`` format validation. The live
model harness remains unimplemented.
"""

from __future__ import annotations

__version__ = "0.4.0"

__all__ = ["__version__"]
