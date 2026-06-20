from __future__ import annotations

from morpheus.differ import (
    DiffSegment,
    compute_diff,
    format_diff_report,
)
from morpheus.tracer import TraceEvent
import time


def _make_events(func_names: list[str]) -> list[TraceEvent]:
    t = time.time()
    events: list[TraceEvent] = []
    for i, name in enumerate(func_names):
        events.append(TraceEvent("call", name, "test.py", i * 5 + 1, {}, t + i * 0.001))
        events.append(TraceEvent("return", name, "test.py", i * 5 + 3, {}, t + i * 0.002, return_value=0))
    return events


def test_identical_runs_produce_same():
    e1 = _make_events(["main", "helper"])
    e2 = _make_events(["main", "helper"])
    segments = compute_diff(e1, e2)
    assert all(s.status == "SAME" for s in segments)


def test_different_runs_produce_changed():
    e1 = _make_events(["main", "helper"])
    e2 = _make_events(["main", "other_func"])
    segments = compute_diff(e1, e2)
    statuses = [s.status for s in segments]
    assert "CHANGED" in statuses


def test_added_chapter():
    e1 = _make_events(["main"])
    e2 = _make_events(["main", "extra"])
    segments = compute_diff(e1, e2)
    assert any(s.status == "ADDED" for s in segments)


def test_removed_chapter():
    e1 = _make_events(["main", "extra"])
    e2 = _make_events(["main"])
    segments = compute_diff(e1, e2)
    assert any(s.status == "REMOVED" for s in segments)


def test_empty_runs():
    segments = compute_diff([], [])
    assert segments == []


def test_format_diff_report():
    segments = [
        DiffSegment("SAME", "main", "main() (2 events)", "main() (2 events)"),
        DiffSegment("ADDED", "extra", "(not present)", "extra() (2 events)"),
    ]
    report = format_diff_report(segments, "run1", "run2")
    assert "[SAME]" in report
    assert "[ADDED]" in report
    assert "run1" in report
    assert "run2" in report


def test_format_diff_report_empty():
    report = format_diff_report([], "a", "b")
    assert "No chapters" in report


def test_diff_segment_dataclass():
    seg = DiffSegment("SAME", "main", "info1", "info2")
    assert seg.status == "SAME"
    assert seg.context == "main"
