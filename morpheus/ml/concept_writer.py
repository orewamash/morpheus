"""
morpheus/ml/concept_writer.py — Behavioral concept inference using execution embeddings.

Classifies execution traces into high-level conceptual categories by combining:
  - Execution graph embedding features (from execution_graph.py)
  - Feature vector statistics (from anomaly.py)
  - Function name keyword analysis (fallback)

Supports concept learning: stores seen embeddings and classifies new runs
by similarity to previously seen concepts.
"""

from __future__ import annotations

import math
from typing import Any

from morpheus.compressor import ExecutionChapter
from morpheus.ml.anomaly import build_feature_vector
from morpheus.ml.execution_graph import (
    build_graph_from_chapters,
    extract_graph_features,
    graph_to_embedding,
)

# ---------------------------------------------------------------------------
#  Concept taxonomy
# ---------------------------------------------------------------------------

CONCEPT_DESCRIPTIONS: dict[str, str] = {
    "machine_learning_pipeline": (
        "Trains or evaluates a machine learning model with data loading, "
        "transformation, and prediction steps."
    ),
    "data_processing_pipeline": (
        "Loads, transforms, and processes structured or unstructured data."
    ),
    "utility_module": (
        "General-purpose helper functions performing conversions, formatting, "
        "or validation logic."
    ),
    "high_volume_processor": (
        "Handles a large number of iterations or events, potentially a loop "
        "or batch processing operation."
    ),
    "complex_orchestrator": (
        "Coordinates multiple subsystems or functions with branching logic "
        "and nested call patterns."
    ),
    "io_bound_operation": (
        "Performs file I/O, network requests, or database queries with "
        "significant wait time."
    ),
    "computational_kernel": (
        "CPU-intensive computation with mathematical operations and tight loops."
    ),
    "simple_computational_module": (
        "Straightforward function composition with linear execution flow."
    ),
    "interactive_session": (
        "User-interactive sequence with input/output operations and state changes."
    ),
}


class ConceptWriter:
    """
    Infers behavioral concepts from execution traces.

    Uses execution graph embeddings for similarity-based classification,
    with keyword analysis as a fallback. Can learn new concepts by storing
    reference embeddings.
    """

    def __init__(self) -> None:
        self._concept_memory: dict[str, list[float]] = {}

    def learn_concept(
        self, concept: str, chapters: list[ExecutionChapter]
    ) -> None:
        """
        Store an execution embedding associated with a concept label.

        Future calls to infer_concept will use this for similarity matching.
        """
        if not chapters:
            return
        embedding = self._compute_embedding(chapters)
        self._concept_memory[concept] = embedding

    def infer_concept(
        self, chapters: list[ExecutionChapter]
    ) -> dict[str, Any]:
        if not chapters:
            return {
                "concept": "unknown",
                "description": "No execution data available.",
            }

        vec = build_feature_vector(chapters)
        func_names = [ch.function_name for ch in chapters]

        # Try embedding-based classification first (if we have learned concepts)
        embedding = self._compute_embedding(chapters)
        concept = self._match_by_embedding(embedding)

        # Keyword-based classification (most specific — exact function names)
        keyword_concept = self._classify_by_keywords(func_names, vec)

        # Graph-based classification (structural patterns like depth, density)
        graph_concept = self._classify_by_graph_features(chapters)

        concept = graph_concept or keyword_concept or concept

        description = CONCEPT_DESCRIPTIONS.get(
            concept,
            f"Execution of {', '.join(func_names[:3])} "
            f"with {vec[1]:.0f} chapter(s) and {vec[0]:.0f} events.",
        )

        return {
            "concept": concept,
            "functions": func_names,
            "description": description,
            "feature_vector": vec,
            "embedding": embedding,
        }

    # -------------------------------------------------------------------
    #  Internal: embedding computation
    # -------------------------------------------------------------------

    def _compute_embedding(
        self, chapters: list[ExecutionChapter]
    ) -> list[float]:
        G = build_graph_from_chapters(chapters)
        return graph_to_embedding(G, embedding_dim=16)

    # -------------------------------------------------------------------
    #  Internal: embedding-based similarity matching
    # -------------------------------------------------------------------

    def _match_by_embedding(
        self, embedding: list[float]
    ) -> str | None:
        if not self._concept_memory:
            return None

        best_concept = None
        best_sim = 0.4  # minimum similarity threshold

        for concept, ref_emb in self._concept_memory.items():
            sim = _cosine_similarity(embedding, ref_emb)
            if sim > best_sim:
                best_sim = sim
                best_concept = concept

        return best_concept

    # -------------------------------------------------------------------
    #  Internal: keyword-based classification (fallback)
    # -------------------------------------------------------------------

    def _classify_by_keywords(
        self, func_names: list[str], vec: list[float]
    ) -> str:
        data_keywords = {
            "load", "read", "parse", "fetch", "query", "data",
            "csv", "file", "write", "save", "export", "import",
        }
        ml_keywords = {
            "train", "predict", "fit", "transform", "model",
            "classify", "cluster", "score", "evaluate",
        }
        util_keywords = {
            "helper", "util", "convert", "format", "validate",
            "clean", "normalize", "sanitize",
        }
        io_keywords = {
            "request", "response", "socket", "connect",
            "download", "upload", "open", "readline",
        }
        compute_keywords = {
            "compute", "calculate", "solve", "optimize",
            "simulate", "iterate", "reduce",
        }

        name_set = set(n.lower() for n in func_names)

        if any(any(kw in name for kw in ml_keywords) for name in name_set):
            return "machine_learning_pipeline"
        if any(any(kw in name for kw in io_keywords) for name in name_set):
            return "io_bound_operation"
        if any(any(kw in name for kw in compute_keywords) for name in name_set):
            return "computational_kernel"
        if any(any(kw in name for kw in data_keywords) for name in name_set):
            return "data_processing_pipeline"
        if any(any(kw in name for kw in util_keywords) for name in name_set):
            return "utility_module"
        if vec[0] > 100:
            return "high_volume_processor"
        if len(func_names) > 5:
            return "complex_orchestrator"

        return "simple_computational_module"

    # -------------------------------------------------------------------
    #  Internal: graph-based feature refinement
    # -------------------------------------------------------------------

    def _classify_by_graph_features(
        self, chapters: list[ExecutionChapter]
    ) -> str | None:
        G = build_graph_from_chapters(chapters)
        features = extract_graph_features(G)

        # High depth and many nodes -> orchestrator
        if features["max_depth"] > 5 and features["num_nodes"] > 10:
            return "complex_orchestrator"

        # Many leaves but low connectivity -> io bound
        if features["num_leaves"] > 5 and features["density"] < 0.3:
            return "io_bound_operation"

        # High call count per node -> computational kernel
        if features["avg_call_count"] > 20:
            return "computational_kernel"

        return None


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)
