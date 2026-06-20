from __future__ import annotations

import time
import networkx as nx

from morpheus.tracer import TraceEvent
from morpheus.compressor import ExecutionChapter
from morpheus.ml.execution_graph import (
    build_graph_from_events,
    build_graph_from_chapters,
    extract_graph_features,
    graph_to_embedding,
)


def _make_events() -> list[TraceEvent]:
    t = time.time()
    return [
        TraceEvent("call", "main", "test.py", 1, {}, t),
        TraceEvent("call", "load_data", "test.py", 5, {}, t + 0.001),
        TraceEvent("return", "load_data", "test.py", 10, {}, t + 0.002, return_value="ok"),
        TraceEvent("call", "train", "test.py", 15, {}, t + 0.003),
        TraceEvent("return", "train", "test.py", 20, {}, t + 0.004, return_value=0),
        TraceEvent("return", "main", "test.py", 25, {}, t + 0.005, return_value=0),
    ]


def _make_chapters() -> list[ExecutionChapter]:
    t = time.time()
    ev1 = TraceEvent("call", "main", "test.py", 1, {}, t)
    ev2 = TraceEvent("call", "helper", "test.py", 5, {}, t + 0.001)
    ev3 = TraceEvent("return", "helper", "test.py", 8, {}, t + 0.002, return_value=42)
    ev4 = TraceEvent("return", "main", "test.py", 10, {}, t + 0.003, return_value=0)
    return [
        ExecutionChapter(1, "Chapter 1: main()", [ev1, ev4], "top-level", 3.0, "main", 2),
        ExecutionChapter(2, "Chapter 2: helper()", [ev2, ev3], "nested", 1.0, "helper", 2),
    ]


class TestBuildGraphFromEvents:
    def test_builds_graph_with_nodes_and_edges(self):
        events = _make_events()
        G = build_graph_from_events(events)
        assert G.number_of_nodes() == 3
        assert G.number_of_edges() == 2

    def test_node_attributes(self):
        events = _make_events()
        G = build_graph_from_events(events)
        assert "main" in G.nodes
        assert "load_data" in G.nodes
        assert G.nodes["load_data"]["call_count"] == 1
        assert G.nodes["main"]["call_count"] == 1

    def test_empty_events(self):
        G = build_graph_from_events([])
        assert G.number_of_nodes() == 0

    def test_edges_reflect_call_hierarchy(self):
        events = _make_events()
        G = build_graph_from_events(events)
        assert G.has_edge("main", "load_data")
        assert G.has_edge("main", "train")

    def test_call_count_tracking(self):
        t = time.time()
        events = [
            TraceEvent("call", "repeated", "test.py", 1, {}, t),
            TraceEvent("call", "repeated", "test.py", 2, {}, t + 0.001),
            TraceEvent("return", "repeated", "test.py", 3, {}, t + 0.002, return_value=0),
            TraceEvent("return", "repeated", "test.py", 4, {}, t + 0.003, return_value=0),
        ]
        G = build_graph_from_events(events)
        assert G.nodes["repeated"]["call_count"] == 2


class TestBuildGraphFromChapters:
    def test_builds_sequential_graph(self):
        chapters = _make_chapters()
        G = build_graph_from_chapters(chapters)
        assert G.number_of_nodes() == 2
        assert G.has_edge("main", "helper")

    def test_empty_chapters(self):
        G = build_graph_from_chapters([])
        assert G.number_of_nodes() == 0


class TestExtractGraphFeatures:
    def test_empty_graph(self):
        G = nx.DiGraph()
        f = extract_graph_features(G)
        assert f["num_nodes"] == 0.0

    def test_extracts_all_features(self):
        events = _make_events()
        G = build_graph_from_events(events)
        f = extract_graph_features(G)
        assert f["num_nodes"] == 3.0
        assert f["num_edges"] == 2.0
        assert f["num_roots"] >= 1.0
        assert f["num_leaves"] >= 1.0


class TestGraphToEmbedding:
    def test_returns_correct_dimension(self):
        events = _make_events()
        G = build_graph_from_events(events)
        emb = graph_to_embedding(G, embedding_dim=32)
        assert len(emb) == 32

    def test_deterministic(self):
        events = _make_events()
        G = build_graph_from_events(events)
        emb1 = graph_to_embedding(G)
        emb2 = graph_to_embedding(G)
        assert emb1 == emb2

    def test_empty_graph_embedding(self):
        G = nx.DiGraph()
        emb = graph_to_embedding(G, embedding_dim=32)
        assert len(emb) == 32
        assert all(v == 0.0 for v in emb)
