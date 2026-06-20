"""
tests/test_prophecy.py — Prophecy mode warning detection tests.
"""

from __future__ import annotations

import time

from morpheus.prophecy import ProphecyWarning, analyze_for_prophecy, format_prophecy_report
from morpheus.tracer import TraceEvent


def _make_call(func_name: str, line: int, local_vars: dict | None = None) -> TraceEvent:
    """Helper to create a call TraceEvent."""
    return TraceEvent(
        event_type="call",
        function_name=func_name,
        filename="test.py",
        line_number=line,
        local_vars=local_vars or {},
        timestamp=time.time(),
    )


def _make_return(
    func_name: str, line: int, return_value=42, local_vars: dict | None = None
) -> TraceEvent:
    """Helper to create a return TraceEvent."""
    return TraceEvent(
        event_type="return",
        function_name=func_name,
        filename="test.py",
        line_number=line,
        local_vars=local_vars or {},
        timestamp=time.time(),
        return_value=return_value,
    )


def test_detects_rapid_repeated_calls():
    """A function called > 100 times should produce a MEDIUM warning."""
    events = []
    for i in range(120):
        events.append(_make_call("process_item", 10))
        events.append(_make_return("process_item", 12))

    warnings = analyze_for_prophecy(events)

    rapid_warnings = [w for w in warnings if "Rapid repeated calls" in w.message]
    assert len(rapid_warnings) >= 1
    assert rapid_warnings[0].severity == "MEDIUM"
    assert "120" in rapid_warnings[0].message


def test_detects_missing_return_value():
    """A function named 'get_*' returning None should produce a MEDIUM warning."""
    events = [
        _make_call("get_user", 5),
        _make_return("get_user", 10, return_value=None),
    ]

    warnings = analyze_for_prophecy(events)

    missing_warnings = [w for w in warnings if "returned None" in w.message]
    assert len(missing_warnings) >= 1
    assert missing_warnings[0].severity == "MEDIUM"


def test_no_warnings_on_clean_trace():
    """A clean short execution should produce zero warnings."""
    events = [
        _make_call("main", 1),
        _make_call("helper", 5),
        _make_return("helper", 8, return_value=42),
        _make_return("main", 10, return_value=0),
    ]

    warnings = analyze_for_prophecy(events)
    assert len(warnings) == 0


def test_format_prophecy_report_empty():
    """Empty warnings list should return 'No warnings detected.'."""
    result = format_prophecy_report([])
    assert "No warnings detected" in result


def test_format_prophecy_report_non_empty():
    """Non-empty warnings list should render a table with content."""
    warnings = [
        ProphecyWarning(
            severity="HIGH",
            function_name="run_loop",
            line_number=15,
            message="Test warning message.",
            suggestion="Test suggestion.",
        )
    ]
    result = format_prophecy_report(warnings)
    assert "Test warning" in result
    assert "run_loop" in result
