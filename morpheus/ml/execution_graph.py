from __future__ import annotations

from typing import Any

import networkx as nx

from morpheus.compressor import ExecutionChapter
from morpheus.tracer import TraceEvent


def build_graph_from_events(events: list[TraceEvent]) -> nx.DiGraph:
    """
    Build a directed execution graph from trace events.

    Each function becomes a node. Each call relationship becomes an edge.
    Node attributes include call count, total time, and line info.

    Args:
        events: List of TraceEvent objects in execution order.

    Returns:
        networkx.DiGraph representing the execution flow.
    """
    G: nx.DiGraph = nx.DiGraph()
    stack: list[str] = []
    func_stats: dict[str, dict[str, Any]] = {}
    call_stack: list[tuple[str, float]] = []

    for ev in events:
        func_name = ev.function_name
        if func_name not in func_stats:
            func_stats[func_name] = {
                "call_count": 0,
                "return_count": 0,
                "total_time_ms": 0.0,
                "lines": set(),
                "filenames": set(),
            }

        stats = func_stats[func_name]
        stats["lines"].add(ev.line_number)
        stats["filenames"].add(ev.filename)

        if ev.event_type == "call":
            stats["call_count"] += 1
            if stack:
                caller = stack[-1]
                G.add_edge(caller, func_name)
            else:
                G.add_node(func_name)
            stack.append(func_name)
            call_stack.append((func_name, ev.timestamp))

        elif ev.event_type == "return":
            stats["return_count"] += 1
            if call_stack and call_stack[-1][0] == func_name:
                _, start_time = call_stack.pop()
                duration = (ev.timestamp - start_time) * 1000
                stats["total_time_ms"] += duration

            if stack and stack[-1] == func_name:
                stack.pop()

    # Set node attributes from accumulated stats
    for func, stats in func_stats.items():
        G.nodes[func].update({
            "call_count": stats["call_count"],
            "return_count": stats["return_count"],
            "total_time_ms": round(stats["total_time_ms"], 2),
            "line_count": len(stats["lines"]),
            "lines": sorted(stats["lines"]),
            "filename": next(iter(stats["filenames"]), ""),
        })

    return G


def build_graph_from_chapters(chapters: list[ExecutionChapter]) -> nx.DiGraph:
    """
    Build a directed execution graph from compressed chapters.

    Each chapter's top-level function becomes a node. Sequential chapter
    calls become edges representing execution flow.

    Args:
        chapters: List of ExecutionChapter objects.

    Returns:
        networkx.DiGraph representing the high-level execution flow.
    """
    G: nx.DiGraph = nx.DiGraph()

    for i, ch in enumerate(chapters):
        func_name = ch.function_name
        G.add_node(func_name, **{
            "chapter_id": ch.chapter_id,
            "duration_ms": ch.duration_ms,
            "event_count": ch.event_count,
            "title": ch.title,
        })
        if i > 0:
            prev_func = chapters[i - 1].function_name
            G.add_edge(prev_func, func_name)

    return G


def extract_graph_features(G: nx.DiGraph) -> dict[str, float]:
    """
    Extract numerical features from an execution graph for ML consumption.

    Args:
        G: A networkx DiGraph representing execution flow.

    Returns:
        Dict of numerical features describing the graph structure.
    """
    if G.number_of_nodes() == 0:
        return {
            "num_nodes": 0.0,
            "num_edges": 0.0,
            "density": 0.0,
            "avg_degree": 0.0,
            "num_roots": 0.0,
            "num_leaves": 0.0,
            "avg_call_count": 0.0,
            "total_time_ms": 0.0,
            "max_depth": 0.0,
            "num_connected_components": 0.0,
        }

    roots = sum(1 for _, d in G.in_degree() if d == 0)
    leaves = sum(1 for _, d in G.out_degree() if d == 0)

    call_counts = [
        data.get("call_count", 1) for _, data in G.nodes(data=True)
    ]
    total_time = sum(
        data.get("total_time_ms", data.get("duration_ms", 0))
        for _, data in G.nodes(data=True)
    )

    max_depth = 0
    for node in G.nodes:
        try:
            length = nx.shortest_path_length(G, node)
            if length:
                max_depth = max(max_depth, max(length.values()))
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            pass

    return {
        "num_nodes": float(G.number_of_nodes()),
        "num_edges": float(G.number_of_edges()),
        "density": round(nx.density(G), 4),
        "avg_degree": round(sum(d for _, d in G.degree()) / max(G.number_of_nodes(), 1), 2),
        "num_roots": float(roots),
        "num_leaves": float(leaves),
        "avg_call_count": round(sum(call_counts) / max(len(call_counts), 1), 2),
        "total_time_ms": round(total_time, 2),
        "max_depth": float(max_depth),
        "num_connected_components": float(nx.number_weakly_connected_components(G)),
    }


def graph_to_embedding(G: nx.DiGraph, embedding_dim: int = 32) -> list[float]:
    """
    Convert an execution graph into a fixed-size embedding vector.

    Uses graph-level features and spectral properties to create
    a deterministic embedding suitable for similarity comparison.

    Args:
        G: A networkx DiGraph.
        embedding_dim: Target dimensionality (default 32).

    Returns:
        List of floats of length embedding_dim.
    """
    features = extract_graph_features(G)
    base = list(features.values())

    if len(base) >= embedding_dim:
        return base[:embedding_dim]

    from morpheus.ml.fingerprint import _expand_vector
    return _expand_vector(base, embedding_dim)


def graphs_to_feature_matrix(
    graphs: list[nx.DiGraph],
) -> list[list[float]]:
    """
    Convert a list of execution graphs into a feature matrix.

    Each row is an embedding of one graph. Useful for clustering or
    training classical ML models (Random Forest, etc.).

    Args:
        graphs: List of networkx DiGraph objects.

    Returns:
        List of embedding vectors, one per graph.
    """
    return [extract_graph_features(G) for G in graphs]
