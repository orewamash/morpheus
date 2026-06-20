"""
morpheus/ml/profiler.py — Execution profiling with HDBSCAN clustering.

Tracks per-function execution metrics over time and can cluster runs by
behavioral profile to identify outliers and execution patterns.

Uses HDBSCAN when available (install with: pip install morpheus-cli[ml]).
Falls back to sklearn DBSCAN or basic statistics.
"""

from __future__ import annotations

from typing import Any

from morpheus.compressor import ExecutionChapter


class ExecutionProfiler:
    def __init__(self) -> None:
        self._history: dict[str, list[dict[str, Any]]] = {}

    def add_run(self, chapters: list[ExecutionChapter]) -> None:
        for ch in chapters:
            if ch.function_name not in self._history:
                self._history[ch.function_name] = []
            entry = {
                "duration_ms": ch.duration_ms,
                "event_count": ch.event_count,
                "depth": _estimate_depth(ch),
            }
            self._history[ch.function_name].append(entry)

    def get_profile(self, function_name: str | None = None) -> dict[str, Any]:
        if function_name:
            entries = self._history.get(function_name, [])
            return {
                "function": function_name,
                "runs": len(entries),
                "avg_duration_ms": _avg([e["duration_ms"] for e in entries]),
                "max_duration_ms": _max([e["duration_ms"] for e in entries]),
            }
        profiles = {}
        for func, entries in self._history.items():
            profiles[func] = {
                "runs": len(entries),
                "avg_duration_ms": _avg(
                    [e["duration_ms"] for e in entries]
                ),
                "max_duration_ms": _max(
                    [e["duration_ms"] for e in entries]
                ),
            }
        return {"functions": profiles, "total_functions": len(profiles)}

    def cluster_runs(
        self, function_name: str, min_cluster_size: int = 2
    ) -> dict[str, Any]:
        """
        Cluster historical runs of a function by their metrics.

        Uses HDBSCAN if available, falls back to sklearn DBSCAN,
        then to basic quartile-based classification.

        Returns:
            Dict with cluster labels, outliers, and per-cluster stats.
        """
        entries = self._history.get(function_name, [])
        if len(entries) < min_cluster_size + 1:
            return {
                "function": function_name,
                "clusters": 0,
                "outliers": 0,
                "note": "Insufficient data for clustering",
            }

        # Build feature matrix: [duration_ms, event_count, depth]
        X = [
            [e["duration_ms"], e["event_count"], e["depth"]]
            for e in entries
        ]

        return _cluster(X, entries, function_name, min_cluster_size)

    def detect_outliers(
        self, function_name: str, threshold: float = 2.0
    ) -> list[int]:
        """
        Find outlier runs for a function using z-score on duration.

        Args:
            function_name: Name of the function to check.
            threshold: Z-score threshold for outlier classification (default 2.0).

        Returns:
            List of outlier indices into the run history.
        """
        entries = self._history.get(function_name, [])
        if len(entries) < 3:
            return []

        durations = [e["duration_ms"] for e in entries]
        mean = sum(durations) / len(durations)
        var = sum((d - mean) ** 2 for d in durations) / len(durations)
        std = var ** 0.5
        if std == 0:
            return []

        return [
            i
            for i, d in enumerate(durations)
            if abs(d - mean) / std > threshold
        ]


# ---------------------------------------------------------------------------
#  Internal helpers
# ---------------------------------------------------------------------------


def _estimate_depth(chapter: ExecutionChapter) -> int:
    depth = 0
    call_depth = 0
    for ev in chapter.events:
        if ev.event_type == "call":
            call_depth += 1
            depth = max(depth, call_depth)
        elif ev.event_type == "return":
            call_depth = max(0, call_depth - 1)
    return depth


def _avg(vals: list[float]) -> float:
    return sum(vals) / len(vals) if vals else 0.0


def _max(vals: list[float]) -> float:
    return max(vals) if vals else 0.0


def _cluster(
    X: list[list[float]],
    entries: list[dict[str, Any]],
    function_name: str,
    min_cluster_size: int,
) -> dict[str, Any]:
    """Try HDBSCAN -> DBSCAN -> quartile fallback."""
    labels = _try_hdbscan(X, min_cluster_size)
    if labels is None:
        labels = _try_dbscan(X)
    if labels is None:
        labels = _quartile_labels(X)

    unique_labels = set(labels)
    n_clusters = len([lb for lb in unique_labels if lb >= 0])
    n_outliers = sum(1 for lb in labels if lb == -1)

    cluster_stats: dict[str, Any] = {}
    for label in unique_labels:
        indices = [i for i, lb in enumerate(labels) if lb == label]
        cluster_durations = [entries[i]["duration_ms"] for i in indices]
        cluster_stats[f"cluster_{label}"] = {
            "size": len(indices),
            "avg_duration_ms": _avg(cluster_durations),
            "indices": indices,
        }

    return {
        "function": function_name,
        "clusters": n_clusters,
        "outliers": n_outliers,
        "labels": labels,
        "cluster_stats": cluster_stats,
    }


def _try_hdbscan(
    X: list[list[float]], min_cluster_size: int
) -> list[int] | None:
    try:
        import hdbscan  # noqa: E402

        clusterer = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size)
        return clusterer.fit_predict(X).tolist()
    except ImportError:
        return None
    except Exception:
        return None


def _try_dbscan(X: list[list[float]]) -> list[int] | None:
    try:
        from sklearn.cluster import DBSCAN  # noqa: E402

        clusterer = DBSCAN(eps=0.5, min_samples=2)
        return clusterer.fit_predict(X).tolist()
    except ImportError:
        return None
    except Exception:
        return None


def _quartile_labels(X: list[list[float]]) -> list[int]:
    """Simple quartile-based classification as last-resort fallback."""
    durations = [row[0] for row in X]
    n = len(durations)
    sorted_d = sorted(durations)
    q1 = sorted_d[n // 4] if n >= 4 else sorted_d[0]
    q3 = sorted_d[3 * n // 4] if n >= 4 else sorted_d[-1]

    labels = []
    for d in durations:
        if d <= q1:
            labels.append(0)  # fast
        elif d <= q3:
            labels.append(1)  # typical
        else:
            labels.append(2)  # slow
    return labels
