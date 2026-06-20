"""
morpheus/ml/degradation.py — Performance Degradation Detector.

Tracks execution metrics over time to detect performance regressions:
  - Duration trends (linear regression slope)
  - Event count trends
  - Anomalous slowdowns vs historical baseline

Uses scikit-learn for linear regression and z-score anomaly detection.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DegradationReport:
    """
    Report of performance degradation analysis for a run.

    Attributes:
        run_id: The ID of the analyzed run.
        duration_zscore: How many std-dev this run is from the mean duration.
        event_zscore: How many std-dev this run is from the mean event count.
        duration_trend_slope: Slope of the duration trend line (positive = getting slower).
        event_trend_slope: Slope of the event count trend line.
        degradation_detected: True if any degradation threshold is exceeded.
        severity: "NONE", "MILD", "MODERATE", or "SEVERE".
        details: Human-readable list of findings.
    """

    run_id: str
    duration_zscore: float = 0.0
    event_zscore: float = 0.0
    duration_trend_slope: float = 0.0
    event_trend_slope: float = 0.0
    degradation_detected: bool = False
    severity: str = "NONE"
    details: list[str] = field(default_factory=list)


def _safe_zscore(value: float, mean: float, std: float) -> float:
    if std == 0 or mean == 0:
        return 0.0
    return (value - mean) / std


def _safe_slope(x: list[float], y: list[float]) -> float:
    """Compute linear regression slope. Returns 0 if insufficient data."""
    n = len(x)
    if n < 3:
        return 0.0
    try:
        import numpy as np

        x_arr = np.array(x, dtype=float)
        y_arr = np.array(y, dtype=float)
        x_mean = x_arr.mean()
        y_mean = y_arr.mean()
        num = ((x_arr - x_mean) * (y_arr - y_mean)).sum()
        den = ((x_arr - x_mean) ** 2).sum()
        if den == 0:
            return 0.0
        return float(num / den)
    except ImportError:
        return _manual_slope(x, y)


def _manual_slope(x: list[float], y: list[float]) -> float:
    """Pure-Python linear regression slope fallback."""
    n = len(x)
    if n < 3:
        return 0.0
    x_mean = sum(x) / n
    y_mean = sum(y) / n
    num = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
    den = sum((x[i] - x_mean) ** 2 for i in range(n))
    if den == 0:
        return 0.0
    return num / den


def analyze_degradation(
    run_id: str,
    current_duration_ms: float,
    current_event_count: int,
    history_durations: list[float],
    history_event_counts: list[list[int]] | None = None,
) -> DegradationReport:
    """
    Analyze performance degradation for a single run against its history.

    Args:
        run_id: The ID of the current run.
        current_duration_ms: Duration of the current run in milliseconds.
        current_event_count: Number of events in the current run.
        history_durations: List of durations from previous runs (ms).
        history_event_counts: Optional list of per-run event counts from history.

    Returns:
        DegradationReport with z-scores, trends, and verdict.
    """
    report = DegradationReport(run_id=run_id)

    # --- Duration z-score vs historical baseline ---
    if history_durations:
        dur_mean = sum(history_durations) / len(history_durations)
        dur_var = (
            sum((d - dur_mean) ** 2 for d in history_durations)
            / len(history_durations)
        )
        dur_std = dur_var ** 0.5
        report.duration_zscore = _safe_zscore(
            current_duration_ms, dur_mean, dur_std
        )
    else:
        report.duration_zscore = 0.0

    # --- Event count z-score vs historical baseline ---
    if history_event_counts:
        hist_totals = [sum(ec) for ec in history_event_counts]
        ev_mean = sum(hist_totals) / len(hist_totals)
        ev_var = (
            sum((e - ev_mean) ** 2 for e in hist_totals) / len(hist_totals)
        )
        ev_std = ev_var ** 0.5
        report.event_zscore = _safe_zscore(
            current_event_count, ev_mean, ev_std
        )
    elif history_durations:
        # Fall back to using durations as a proxy for expected count
        report.event_zscore = 0.0
    else:
        report.event_zscore = 0.0

    # --- Duration trend ---
    if len(history_durations) >= 3:
        history_with_current = history_durations + [current_duration_ms]
        x = list(range(len(history_with_current)))
        report.duration_trend_slope = _safe_slope(x, history_with_current)
    else:
        report.duration_trend_slope = 0.0

    # --- Event count trend ---
    if history_event_counts and len(history_event_counts) >= 3:
        hist_totals = [sum(ec) for ec in history_event_counts]
        history_with_current = hist_totals + [current_event_count]
        x = list(range(len(history_with_current)))
        report.event_trend_slope = _safe_slope(x, history_with_current)
    else:
        report.event_trend_slope = 0.0

    # --- Severity classification ---
    abs_dur_z = abs(report.duration_zscore)
    abs_ev_z = abs(report.event_zscore)
    max_z = max(abs_dur_z, abs_ev_z)

    if report.duration_trend_slope > 5.0:
        report.degradation_detected = True
        report.details.append(
            f"Duration trend is increasing (slope={report.duration_trend_slope:.2f})"
        )

    if abs_dur_z > 3.0:
        report.degradation_detected = True
        report.details.append(
            f"Duration is {report.duration_zscore:.1f} std-dev from baseline "
            f"(z-score > 3.0)"
        )

    if abs_ev_z > 3.0:
        report.degradation_detected = True
        report.details.append(
            f"Event count is {report.event_zscore:.1f} std-dev from baseline "
            f"(z-score > 3.0)"
        )

    if max_z > 5.0:
        report.severity = "SEVERE"
    elif max_z > 3.0:
        report.severity = "MODERATE"
    elif max_z > 2.0:
        report.severity = "MILD"
    else:
        report.severity = "NONE"

    if not report.details:
        report.details.append("No significant degradation detected.")

    return report


def format_degradation_report(report: DegradationReport) -> str:
    """
    Format a DegradationReport into a human-readable string.
    """
    severity_color = {
        "NONE": "GREEN",
        "MILD": "YELLOW",
        "MODERATE": "ORANGE",
        "SEVERE": "RED",
    }
    color = severity_color.get(report.severity, "WHITE")

    lines = [
        f"Degradation Analysis [{color}]",
        f"Severity: {report.severity}",
        f"Duration z-score: {report.duration_zscore:.2f}",
        f"Event count z-score: {report.event_zscore:.2f}",
        f"Duration trend slope: {report.duration_trend_slope:.2f}",
        f"Event trend slope: {report.event_trend_slope:.2f}",
        "Details:",
    ]
    for detail in report.details:
        lines.append(f"  - {detail}")

    return "\n".join(lines)
