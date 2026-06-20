"""
tests/test_degradation.py — Tests for Performance Degradation Detector.
"""

from __future__ import annotations

from morpheus.ml.degradation import (
    DegradationReport,
    analyze_degradation,
    format_degradation_report,
)


class TestAnalyzeDegradation:
    def test_no_history_returns_none(self):
        report = analyze_degradation(
            run_id="test-1",
            current_duration_ms=100.0,
            current_event_count=50,
            history_durations=[],
        )
        assert report.severity == "NONE"
        assert report.duration_zscore == 0.0

    def test_normal_variation_returns_none(self):
        report = analyze_degradation(
            run_id="test-1",
            current_duration_ms=100.0,
            current_event_count=50,
            history_durations=[95.0, 105.0, 98.0, 102.0],
        )
        assert report.severity == "NONE"

    def test_duration_anomaly_detected(self):
        report = analyze_degradation(
            run_id="test-1",
            current_duration_ms=500.0,
            current_event_count=50,
            history_durations=[95.0, 105.0, 98.0, 102.0],
        )
        assert report.degradation_detected is True
        assert report.severity in ("MODERATE", "SEVERE")
        assert any("z-score" in d or "trend" in d for d in report.details)

    def test_event_count_anomaly_detected(self):
        report = analyze_degradation(
            run_id="test-1",
            current_duration_ms=100.0,
            current_event_count=999,
            history_durations=[95.0, 105.0, 98.0, 102.0],
            history_event_counts=[[50], [52], [48], [51]],
        )
        assert report.degradation_detected is True
        assert report.event_zscore > 2.0

    def test_trend_slope_detected(self):
        history_durations = [10.0, 20.0, 30.0, 40.0, 50.0]
        report = analyze_degradation(
            run_id="test-1",
            current_duration_ms=60.0,
            current_event_count=50,
            history_durations=history_durations,
        )
        assert report.duration_trend_slope > 0
        assert report.degradation_detected is True

    def test_severity_scaling(self):
        report = analyze_degradation(
            run_id="test-1",
            current_duration_ms=1000.0,
            current_event_count=50,
            history_durations=[100.0, 110.0, 90.0],
        )
        # 1000 vs mean=100, std~8.16 -> zscore ~110 -> SEVERE
        assert report.severity == "SEVERE"

    def test_edge_case_identical_values(self):
        report = analyze_degradation(
            run_id="test-1",
            current_duration_ms=100.0,
            current_event_count=50,
            history_durations=[100.0, 100.0, 100.0],
        )
        assert report.severity == "NONE"
        assert not report.degradation_detected

    def test_insufficient_data_for_trend(self):
        report = analyze_degradation(
            run_id="test-1",
            current_duration_ms=200.0,
            current_event_count=50,
            history_durations=[100.0],
        )
        assert report.duration_trend_slope == 0.0

    def test_mixed_history_event_counts(self):
        report = analyze_degradation(
            run_id="test-1",
            current_duration_ms=100.0,
            current_event_count=100,
            history_durations=[95.0, 105.0],
            history_event_counts=[[10, 20], [12, 18]],
        )
        assert isinstance(report.event_zscore, float)


class TestFormatDegradationReport:
    def test_includes_severity(self):
        report = DegradationReport(run_id="test", severity="SEVERE")
        formatted = format_degradation_report(report)
        assert "SEVERE" in formatted

    def test_includes_details(self):
        report = DegradationReport(
            run_id="test",
            degradation_detected=True,
            details=["Something went wrong"],
        )
        formatted = format_degradation_report(report)
        assert "Something went wrong" in formatted

    def test_empty_details(self):
        report = DegradationReport(run_id="test")
        formatted = format_degradation_report(report)
        assert formatted is not None
