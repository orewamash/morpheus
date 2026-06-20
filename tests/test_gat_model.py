from __future__ import annotations

import time
import pytest

from morpheus.tracer import TraceEvent
from morpheus.ml.gat_model import GATModel, MemoryBank, _cosine_similarity
import numpy as np


def _sample_events() -> list[TraceEvent]:
    t = time.time()
    return [
        TraceEvent("call", "main", "test.py", 1, {}, t),
        TraceEvent("call", "helper", "test.py", 5, {}, t + 0.001),
        TraceEvent("return", "helper", "test.py", 10, {}, t + 0.002, return_value=42),
        TraceEvent("return", "main", "test.py", 15, {}, t + 0.003, return_value=0),
    ]


class TestCosineSimilarity:
    def test_identical_vectors(self):
        a = np.array([1.0, 2.0, 3.0])
        b = np.array([1.0, 2.0, 3.0])
        assert _cosine_similarity(a, b) == pytest.approx(1.0)

    def test_orthogonal_vectors(self):
        a = np.array([1.0, 0.0])
        b = np.array([0.0, 1.0])
        assert _cosine_similarity(a, b) == pytest.approx(0.0)

    def test_zero_vector(self):
        a = np.array([0.0, 0.0])
        b = np.array([1.0, 0.0])
        assert _cosine_similarity(a, b) == 0.0


class TestGATModel:
    def test_fallback_encoding(self):
        model = GATModel(out_channels=32)
        events = _sample_events()
        embedding = model.encode(events)
        assert len(embedding) == 32
        assert all(isinstance(v, float) for v in embedding)

    def test_predict_returns_all_keys(self):
        model = GATModel()
        events = _sample_events()
        result = model.predict(events)
        assert "complexity_score" in result
        assert "risk_level" in result
        assert "embedding" in result
        assert "graph_features" in result
        assert result["model_type"] == "feature_fallback"

    def test_predict_low_complexity(self):
        model = GATModel()
        t = time.time()
        events = [
            TraceEvent("call", "main", "test.py", 1, {}, t),
            TraceEvent("return", "main", "test.py", 2, {}, t + 0.001, return_value=0),
        ]
        result = model.predict(events)
        assert result["risk_level"] in ("LOW", "MEDIUM")

    def test_encoding_deterministic(self):
        model = GATModel()
        events = _sample_events()
        emb1 = model.encode(events)
        emb2 = model.encode(events)
        assert emb1 == emb2

    def test_empty_events(self):
        model = GATModel()
        embedding = model.encode([])
        assert len(embedding) == 32


class TestMemoryBank:
    def test_store_and_count(self):
        bank = MemoryBank()
        events = _sample_events()
        eid = bank.store(events, {"run_id": "test-1"})
        assert eid.startswith("emb_")
        assert bank.count() == 1

    def test_search_similar(self):
        bank = MemoryBank()
        events = _sample_events()
        bank.store(events, {"run_id": "run-1"})
        bank.store(events, {"run_id": "run-2"})
        results = bank.search_similar(events, top_k=2)
        assert len(results) == 2
        assert results[0]["similarity"] >= 0.9

    def test_search_empty_bank(self):
        bank = MemoryBank()
        events = _sample_events()
        results = bank.search_similar(events)
        assert results == []

    def test_clear(self):
        bank = MemoryBank()
        bank.store(_sample_events())
        assert bank.count() > 0
        bank.clear()
        assert bank.count() == 0
