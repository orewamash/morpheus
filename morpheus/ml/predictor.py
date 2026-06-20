"""
morpheus/ml/predictor.py — Execution crash prediction.

Predicts whether a current execution is likely to crash based on patterns from history.
"""

from __future__ import annotations


def predict_crash_probability(
    current_vector: list[float],
    history_vectors: list[list[float]],
    history_labels: list[int],
) -> dict[str, float | str]:
    """
    Predict the probability that the current execution will crash.

    Args:
        current_vector: Feature vector of the current run.
        history_vectors: Feature vectors of historical runs.
        history_labels: 1 = crashed, 0 = succeeded (one per history vector).

    Returns:
        Dict with keys:
            "crash_probability": float — 0.0 to 1.0
            "risk_level": str — "LOW", "MEDIUM", "HIGH", "CRITICAL"
            "message": str — Human-readable prediction
    """
    if len(history_vectors) < 20 or len(history_labels) < 20:
        return {
            "crash_probability": 0.0,
            "risk_level": "LOW",
            "message": "Not enough history yet",
        }

    try:
        import numpy as np
        from sklearn.ensemble import RandomForestClassifier

        X = np.array(history_vectors)
        y = np.array(history_labels)

        # Basic check to ensure we have both classes present before training
        if len(np.unique(y)) < 2:
            return {
                "crash_probability": 0.1,
                "risk_level": "LOW",
                "message": "Insufficient variation in crash history (need both crashed and succeeded runs).",
            }

        clf = RandomForestClassifier(n_estimators=50, random_state=42)
        clf.fit(X, y)

        x_curr = np.array([current_vector])
        # predict_proba returns [prob_class_0, prob_class_1]
        probs = clf.predict_proba(x_curr)[0]
        prob_crash = float(probs[1])

        # Assign risk level based on thresholds
        if prob_crash < 0.3:
            risk_level = "LOW"
        elif prob_crash < 0.6:
            risk_level = "MEDIUM"
        elif prob_crash < 0.85:
            risk_level = "HIGH"
        else:
            risk_level = "CRITICAL"

        msg = f"Crash probability predicted at {prob_crash * 100:.1f}% ({risk_level} risk)."

        return {
            "crash_probability": prob_crash,
            "risk_level": risk_level,
            "message": msg,
        }

    except ImportError:
        # Graceful fallback if scikit-learn is not installed
        return {
            "crash_probability": 0.0,
            "risk_level": "LOW",
            "message": "scikit-learn is not installed. Crash prediction skipped.",
        }
