"""
morpheus/ml/anomaly.py — Anomaly detection for execution runs.

Extracts feature vectors from execution chapters and compares against run history.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from morpheus.compressor import ExecutionChapter


def build_feature_vector(chapters: list[ExecutionChapter]) -> list[float]:
    """
    Convert a list of ExecutionChapters into a numerical feature vector for ML.

    Features to extract (in this exact order):
    1. Total event count
    2. Number of chapters
    3. Average chapter duration_ms
    4. Max chapter duration_ms
    5. Min chapter duration_ms
    6. Number of unique function names
    7. Max recursion depth (same function appearing in nested calls)
    8. Total duration_ms

    Args:
        chapters: List of ExecutionChapter objects.

    Returns:
        List of 8 float values representing this run.
    """
    if not chapters:
        return [0.0] * 8

    # 1. Total event count
    total_events = float(sum(ch.event_count for ch in chapters))

    # 2. Number of chapters
    num_chapters = float(len(chapters))

    # 3. Average chapter duration_ms
    avg_duration = sum(ch.duration_ms for ch in chapters) / num_chapters

    # 4. Max chapter duration_ms
    max_duration = float(max(ch.duration_ms for ch in chapters))

    # 5. Min chapter duration_ms
    min_duration = float(min(ch.duration_ms for ch in chapters))

    # 6. Number of unique function names
    unique_funcs = float(len(set(ch.function_name for ch in chapters)))

    # 7. Max recursion depth
    # We estimate max recursion depth by traversing all events in all chapters
    max_rec_depth = 0
    stack: list[str] = []
    for ch in chapters:
        for ev in ch.events:
            if ev.event_type == "call":
                stack.append(ev.function_name)
                # Count current occurrences of the same function in the stack
                func_count = stack.count(ev.function_name)
                if func_count > max_rec_depth:
                    max_rec_depth = func_count
            elif ev.event_type == "return" and stack:
                if ev.function_name in stack:
                    # Remove from stack from the end
                    for idx in range(len(stack) - 1, -1, -1):
                        if stack[idx] == ev.function_name:
                            stack.pop(idx)
                            break

    # 8. Total duration_ms
    total_duration = sum(ch.duration_ms for ch in chapters)

    return [
        total_events,
        num_chapters,
        avg_duration,
        max_duration,
        min_duration,
        unique_funcs,
        float(max_rec_depth),
        total_duration,
    ]


def detect_anomaly(
    current_vector: list[float], history_vectors: list[list[float]]
) -> dict[str, float | bool | str]:
    """
    Use Isolation Forest to determine if the current run is anomalous.

    Requires at least 10 historical vectors to produce meaningful results.

    Args:
        current_vector: Feature vector of the current run.
        history_vectors: Feature vectors of all previous runs.

    Returns:
        Dict with keys "is_anomaly", "anomaly_score", "confidence", "message".
    """
    if len(history_vectors) < 10:
        return {
            "is_anomaly": False,
            "message": "Not enough history yet (need 10+ runs)",
        }

    try:
        import numpy as np
        from sklearn.ensemble import IsolationForest

        X = np.array(history_vectors)
        clf = IsolationForest(random_state=42)
        clf.fit(X)

        x_curr = np.array([current_vector])
        pred = clf.predict(x_curr)[0]
        # Isolation Forest decision_function returns negative values for anomalies, positive for inliers
        score = float(clf.decision_function(x_curr)[0])

        is_anomaly = bool(pred == -1)

        # Scale score to a normalized confidence or distance
        # Decision function outputs are generally in range [-0.5, 0.5]
        confidence = float(min(1.0, max(0.0, abs(score) * 2.0)))

        msg = (
            "Execution pattern is normal."
            if not is_anomaly
            else "Execution pattern is anomalous compared to history."
        )

        return {
            "is_anomaly": is_anomaly,
            "anomaly_score": score,
            "confidence": confidence,
            "message": msg,
        }
    except ImportError:
        # Graceful fallback if scikit-learn is not installed
        return {
            "is_anomaly": False,
            "message": "scikit-learn is not installed. Anomaly detection skipped.",
        }
