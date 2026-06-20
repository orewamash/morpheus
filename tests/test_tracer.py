"""
tests/test_tracer.py — Tracer tests for Morpheus.
"""

from __future__ import annotations

import os
from morpheus.tracer import trace_file


def test_tracer_captures_call_events():
    """trace_file() must return at least one TraceEvent with event_type == "call"."""
    filepath = os.path.join("examples", "simple.py")
    events = trace_file(filepath)
    calls = [e for e in events if e.event_type == "call"]
    assert len(calls) > 0
    assert any(e.function_name == "calculate" for e in calls)


def test_tracer_captures_return_events():
    """trace_file() must return at least one TraceEvent with event_type == "return"."""
    filepath = os.path.join("examples", "simple.py")
    events = trace_file(filepath)
    returns = [e for e in events if e.event_type == "return"]
    assert len(returns) > 0
    assert any(e.function_name == "add" for e in returns)


def test_tracer_ignores_stdlib():
    """trace_file() must not return any TraceEvent where filename contains 'site-packages' or 'lib/python'."""
    filepath = os.path.join("examples", "simple.py")
    events = trace_file(filepath)
    for event in events:
        filename = event.filename.replace("\\", "/").lower()
        assert "site-packages" not in filename
        assert "lib/python" not in filename
