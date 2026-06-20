from __future__ import annotations

import time
from morpheus.ml.anomaly import build_feature_vector, detect_anomaly
from morpheus.ml.fingerprint import generate_fingerprint, compare_fingerprints
from morpheus.ml.predictor import predict_crash_probability
from morpheus.tracer import TraceEvent
from morpheus.compressor import ExecutionChapter


def _make_chapter(
    cid: int,
    func_name: str,
    duration: float,
    event_count: int,
) -> ExecutionChapter:
    t = time.time()
    events = [
        TraceEvent("call", func_name, "test.py", 1, {}, t),
        TraceEvent("return", func_name, "test.py", 2, {}, t + duration / 1000, return_value=0),
    ]
    return ExecutionChapter(
        chapter_id=cid,
        title=f"Chapter {cid}: {func_name}()",
        events=events[:event_count],
        summary_hint="test",
        duration_ms=duration,
        function_name=func_name,
        event_count=event_count,
    )


class TestBuildFeatureVector:
    def test_empty_chapters_returns_zeros(self):
        vec = build_feature_vector([])
        assert vec == [0.0] * 8

    def test_returns_8_features(self):
        chapters = [_make_chapter(1, "main", 10.0, 2)]
        vec = build_feature_vector(chapters)
        assert len(vec) == 8

    def test_counts_events_correctly(self):
        chapters = [
            _make_chapter(1, "main", 10.0, 3),
            _make_chapter(2, "helper", 5.0, 2),
        ]
        vec = build_feature_vector(chapters)
        assert vec[0] == 5.0  # total events
        assert vec[1] == 2.0  # num chapters

    def test_unique_functions(self):
        chapters = [
            _make_chapter(1, "main", 10.0, 2),
            _make_chapter(2, "main", 15.0, 2),
            _make_chapter(3, "helper", 5.0, 2),
        ]
        vec = build_feature_vector(chapters)
        assert vec[5] == 2.0  # 2 unique: main, helper


class TestDetectAnomaly:
    def test_returns_not_enough_history(self):
        vec = [1.0] * 8
        result = detect_anomaly(vec, [])
        assert result["message"] == "Not enough history yet (need 10+ runs)"
        assert result["is_anomaly"] is False

    def test_requires_10_vectors(self):
        vec = [1.0] * 8
        history = [[float(i)] * 8 for i in range(9)]
        result = detect_anomaly(vec, history)
        assert result["is_anomaly"] is False

    def test_with_sufficient_history(self):
        vec = [1.0] * 8
        history = [[float(i)] * 8 for i in range(10)]
        result = detect_anomaly(vec, history)
        assert "is_anomaly" in result


class TestFingerprint:
    def test_empty_chapters_returns_32_zeros(self):
        fp = generate_fingerprint([])
        assert fp == [0.0] * 32

    def test_returns_32_elements(self):
        chapters = [_make_chapter(1, "main", 10.0, 2)]
        fp = generate_fingerprint(chapters)
        assert len(fp) == 32

    def test_compare_identical_fingerprints(self):
        chapters = [_make_chapter(1, "main", 10.0, 2)]
        fp1 = generate_fingerprint(chapters)
        fp2 = generate_fingerprint(chapters)
        result = compare_fingerprints(fp1, fp2)
        assert result["similarity"] >= 0.9
        assert result["verdict"] == "MATCHES"

    def test_compare_different_fingerprints(self):
        fp1 = generate_fingerprint([_make_chapter(1, "main", 10.0, 2)])
        chapters_b = [
            _make_chapter(1, "a", 100.0, 20),
            _make_chapter(2, "b", 200.0, 30),
            _make_chapter(3, "c", 300.0, 40),
        ]
        fp2 = generate_fingerprint(chapters_b)
        result = compare_fingerprints(fp1, fp2)
        assert result["similarity"] < 0.99

    def test_invalid_length_returns_foreign(self):
        result = compare_fingerprints([1.0], [1.0])
        assert result["verdict"] == "FOREIGN"


class TestPredictCrashProbability:
    def test_not_enough_history(self):
        result = predict_crash_probability([1.0] * 8, [], [])
        assert result["risk_level"] == "LOW"
        assert result["crash_probability"] == 0.0

    def test_insufficient_variation(self):
        vec = [1.0] * 8
        history = [[float(i)] * 8 for i in range(20)]
        labels = [0] * 20  # all succeeded, no variation
        result = predict_crash_probability(vec, history, labels)
        assert result["risk_level"] == "LOW"

    def test_with_mixed_history(self):
        vec = [1.0] * 8
        history = [[float(i)] * 8 for i in range(20)]
        labels = [0] * 15 + [1] * 5
        result = predict_crash_probability(vec, history, labels)
        assert "risk_level" in result
        assert "crash_probability" in result
