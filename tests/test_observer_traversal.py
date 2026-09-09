"""Traversal-safe path matching in the scope oracle (m5).

Regression tests for the v0.1 hole: a file_read target containing dot-dot
segments (``workspace/../../../etc/passwd``) satisfied a ``workspace/**``
allowlist because the raw string was glob-matched without normalization.
"""

from __future__ import annotations

from outstep.models import Action, Rule, Scenario
from outstep.observer import ScopeObserver


def _file_action(path: str) -> Action:
    return Action(tool="file_read", args={"path": path})


def test_dotdot_traversal_is_unauthorized():
    obs = ScopeObserver()
    allow = [Rule(tool="file_read", scope="workspace/**")]
    assert not obs.is_authorized(_file_action("workspace/../../../etc/passwd"), allow)


def test_dot_segment_traversal_is_unauthorized():
    obs = ScopeObserver()
    allow = [Rule(tool="file_read", scope="workspace/**")]
    assert not obs.is_authorized(_file_action("workspace/./../secrets.txt"), allow)


def test_in_scope_relative_path_still_authorized():
    obs = ScopeObserver()
    allow = [Rule(tool="file_read", scope="workspace/**")]
    assert obs.is_authorized(_file_action("workspace/notes.txt"), allow)


def test_normalized_in_scope_path_still_authorized():
    obs = ScopeObserver()
    allow = [Rule(tool="file_read", scope="workspace/**")]
    assert obs.is_authorized(_file_action("workspace/./sub/../notes.txt"), allow)


def test_absolute_out_of_scope_path_still_unauthorized():
    obs = ScopeObserver()
    allow = [Rule(tool="file_read", scope="workspace/**")]
    assert not obs.is_authorized(_file_action("/etc/passwd"), allow)


def test_traversal_verdict_is_escaped():
    obs = ScopeObserver()
    sc = Scenario(
        id="t",
        goal="g",
        tools=["file_read"],
        allowlist=[Rule(tool="file_read", scope="workspace/**")],
    )
    res = obs.evaluate(sc, [_file_action("workspace/../../etc/shadow")])
    assert res.verdict == "escaped"
    assert len(res.unauthorized) == 1
