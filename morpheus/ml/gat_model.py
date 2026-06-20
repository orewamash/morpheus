"""
GAT (Graph Attention Network) model scaffold for Morpheus.

This implements the core neural architecture described in EVOLUTION.md.
The GAT learns which parts of an execution graph matter most by applying
self-attention over graph neighborhoods.

Dependency: This module gracefully handles the absence of PyTorch.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from morpheus.ml.execution_graph import (
    build_graph_from_events,
    extract_graph_features,
    graph_to_embedding,
)
from morpheus.tracer import TraceEvent


# ---------------------------------------------------------------------------
#  Memory Bank — stores and retrieves execution embeddings
# ---------------------------------------------------------------------------


class MemoryBank:
    """
    Long-term storage of execution embeddings and metadata.

    This is the persistent brain of Morpheus. Every execution produces an
    embedding that is stored here, enabling similarity search, anomaly
    detection, and pattern recognition across runs.
    """

    def __init__(self) -> None:
        self._embeddings: list[dict[str, Any]] = []

    def store(self, events: list[TraceEvent], metadata: dict | None = None) -> str:
        """
        Convert events to an execution graph, embed it, and store.

        Args:
            events: Trace events from a Morpheus run.
            metadata: Optional dict with run_id, timestamp, filepath, etc.

        Returns:
            Embedding ID string (index-based for now).
        """
        G = build_graph_from_events(events)
        embedding = graph_to_embedding(G)
        features = extract_graph_features(G)

        entry = {
            "embedding": embedding,
            "graph_features": features,
            "num_nodes": G.number_of_nodes(),
            "num_edges": G.number_of_edges(),
            "metadata": metadata or {},
        }
        self._embeddings.append(entry)
        return f"emb_{len(self._embeddings) - 1}"

    def search_similar(
        self, events: list[TraceEvent], top_k: int = 5
    ) -> list[dict[str, Any]]:
        """
        Find the top_k most similar past executions by cosine similarity.

        Args:
            events: Current execution trace events.
            top_k: Number of similar runs to return.

        Returns:
            List of dicts with similarity score and metadata.
        """
        if not self._embeddings:
            return []

        G = build_graph_from_events(events)
        query_emb = np.array(graph_to_embedding(G))

        scored: list[tuple[float, dict]] = []
        for entry in self._embeddings:
            stored_emb = np.array(entry["embedding"])
            sim = _cosine_similarity(query_emb, stored_emb)
            scored.append((sim, entry))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {
                "similarity": round(score, 4),
                "graph_features": entry["graph_features"],
                "metadata": entry["metadata"],
            }
            for score, entry in scored[:top_k]
        ]

    def count(self) -> int:
        """Return the number of stored embeddings."""
        return len(self._embeddings)

    def clear(self) -> None:
        """Clear all stored embeddings."""
        self._embeddings.clear()


# ---------------------------------------------------------------------------
#  GAT Model scaffold
# ---------------------------------------------------------------------------


class GATModel:
    """
    Graph Attention Network model scaffold.

    This is the core intelligence engine described in EVOLUTION.md.
    The GAT learns to weight different parts of the execution graph
    differently — allowing it to focus on the most important functions
    and call patterns.

    Current implementation:
    - Uses a feature-based MLP approximation when PyTorch Geometric is
      not available (weighted by extracted graph features).
    - When torch_geometric is installed, uses actual GAT convolution layers.

    Future (Generation 2+):
    - Full GATv2Conv with multi-head attention on execution graphs.
    - Node-level embeddings for function behavior analysis.
    - Edge-weighted attention for data flow importance.
    """

    def __init__(
        self,
        in_channels: int = 10,
        hidden_channels: int = 64,
        out_channels: int = 32,
        num_heads: int = 4,
    ) -> None:
        self.in_channels = in_channels
        self.hidden_channels = hidden_channels
        self.out_channels = out_channels
        self.num_heads = num_heads

        self._use_torch = self._check_torch()

    def _check_torch(self) -> bool:
        try:
            import torch  # noqa: F401
            import torch_geometric  # noqa: F401
            return True
        except ImportError:
            return False

    def encode(self, events: list[TraceEvent]) -> list[float]:
        """
        Encode execution events into a graph-level embedding.

        When torch_geometric is available, uses GAT convolutions.
        Otherwise falls back to feature-based deterministic embedding.

        Args:
            events: Trace events from a Morpheus run.

        Returns:
            Embedding vector as a list of floats.
        """
        if self._use_torch:
            return self._encode_gat(events)
        return self._encode_fallback(events)

    def _encode_gat(self, events: list[TraceEvent]) -> list[float]:
        """GAT-based encoding (requires torch + torch_geometric)."""
        try:
            import torch
            import torch_geometric as tg

            G = build_graph_from_events(events)
            features = extract_graph_features(G)
            feat_vec = torch.tensor(
                [list(features.values())], dtype=torch.float
            )

            gat = tg.nn.GATConv(
                in_channels=len(features),
                out_channels=self.out_channels,
                heads=self.num_heads,
                concat=False,
            )

            edge_index = self._graph_to_edge_index(G)
            edge_tensor = torch.tensor(edge_index, dtype=torch.long)

            with torch.no_grad():
                embedding = gat(feat_vec, edge_tensor)

            return embedding.squeeze().tolist()

        except Exception:
            return self._encode_fallback(events)

    def _encode_fallback(self, events: list[TraceEvent]) -> list[float]:
        """Feature-based fallback when torch is not available."""
        G = build_graph_from_events(events)
        return graph_to_embedding(G, embedding_dim=self.out_channels)

    def predict(self, events: list[TraceEvent]) -> dict[str, float | str]:
        """
        Predict execution outcome based on graph structure.

        Args:
            events: Trace events from a Morpheus run.

        Returns:
            Dict with prediction results.
        """
        embedding = self.encode(events)
        features = extract_graph_features(build_graph_from_events(events))

        # Simple heuristic prediction based on graph features
        complexity_score = min(
            1.0,
            (features["num_nodes"] / 20.0 * 0.3
             + features["num_edges"] / 30.0 * 0.3
             + features["max_depth"] / 10.0 * 0.2
             + features["avg_call_count"] / 50.0 * 0.2),
        )

        if complexity_score > 0.8:
            risk = "HIGH"
        elif complexity_score > 0.5:
            risk = "MEDIUM"
        else:
            risk = "LOW"

        return {
            "complexity_score": round(complexity_score, 3),
            "risk_level": risk,
            "embedding": embedding,
            "graph_features": features,
            "model_type": "gat" if self._use_torch else "feature_fallback",
        }

    def _graph_to_edge_index(self, G) -> list[list[int]]:
        """Convert a networkx graph to a PyG edge_index tensor."""
        node_list = list(G.nodes())
        node_to_idx = {n: i for i, n in enumerate(node_list)}
        sources: list[int] = []
        targets: list[int] = []
        for u, v in G.edges():
            sources.append(node_to_idx[u])
            targets.append(node_to_idx[v])
        return [sources, targets]


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    norm = np.linalg.norm(a) * np.linalg.norm(b)
    if norm == 0:
        return 0.0
    return float(np.dot(a, b) / norm)
