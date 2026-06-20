"""
tests/test_profiler.py — Tests for ExecutionProfiler with clustering.
"""

from __future__ import annotations

from morpheus.tracer import TraceEvent
from morpheus.compressor import ExecutionChapter
from morpheus.ml.profiler import ExecutionProfiler


def _make_chapter(
    name: str,
    duration: float = 10.0,
    events_count: int = 5,
) -> ExecutionChapter:
    t = 1000.0
    events = [
        TraceEvent("call", name, "test.py", 1, {}, t + i * 0.1)
        for i in range(events_count // 2)
    ] + [
        TraceEvent("return", name, "test.py", 10, {}, t + i * 0.2)
        for i in range(events_count // 2)
    ]
    return ExecutionChapter(
        chapter_id=1,
        title=f"Chapter: {name}()",
        events=events,
        summary_hint="",
        duration_ms=duration,
        function_name=name,
        event_count=events_count,
    )


class TestExecutionProfiler:
    def test_add_and_get_profile(self):
        profiler = ExecutionProfiler()
        ch = _make_chapter("foo", 10.0, 4)
        profiler.add_run([ch])
        profile = profiler.get_profile("foo")
        assert profile["runs"] == 1
        assert profile["avg_duration_ms"] == 10.0

    def test_add_multiple_runs(self):
        profiler = ExecutionProfiler()
        for i in range(3):
            profiler.add_run([_make_chapter("foo", float(i + 1) * 10)])
        profile = profiler.get_profile("foo")
        assert profile["runs"] == 3
        assert profile["avg_duration_ms"] == 20.0

    def test_all_profiles(self):
        profiler = ExecutionProfiler()
        profiler.add_run([_make_chapter("a"), _make_chapter("b")])
        all_profiles = profiler.get_profile()
        assert all_profiles["total_functions"] == 2

    def test_missing_function_returns_empty(self):
        profiler = ExecutionProfiler()
        profile = profiler.get_profile("nonexistent")
        assert profile["runs"] == 0

    def test_cluster_insufficient_data(self):
        profiler = ExecutionProfiler()
        profiler.add_run([_make_chapter("foo")])
        result = profiler.cluster_runs("foo")
        assert result["clusters"] == 0
        assert "Insufficient data" in result["note"]

    def test_outlier_detection_insufficient_data(self):
        profiler = ExecutionProfiler()
        profiler.add_run([_make_chapter("foo")])
        outliers = profiler.detect_outliers("foo")
        assert outliers == []

    def test_outlier_detection_identical(self):
        profiler = ExecutionProfiler()
        for _ in range(3):
            profiler.add_run([_make_chapter("foo", 10.0)])
        outliers = profiler.detect_outliers("foo")
        assert outliers == []

    def test_detect_outlier(self):
        profiler = ExecutionProfiler()
        for _ in range(5):
            profiler.add_run([_make_chapter("foo", 10.0)])
        profiler.add_run([_make_chapter("foo", 999.0)])
        outliers = profiler.detect_outliers("foo", threshold=2.0)
        assert len(outliers) > 0

    def test_estimate_depth(self):
        from morpheus.ml.profiler import _estimate_depth
        ch = _make_chapter("foo")
        depth = _estimate_depth(ch)
        assert isinstance(depth, int)
