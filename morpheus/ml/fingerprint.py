"""
morpheus/ml/fingerprint.py — Behavioral fingerprinting (Codebase DNA).

Generates and compares behavioral fingerprints for project execution.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from morpheus.ml.anomaly import build_feature_vector

if TYPE_CHECKING:
    from morpheus.compressor import ExecutionChapter


def generate_fingerprint(chapters: list[ExecutionChapter]) -> list[float]:
    """
    Generate a behavioral fingerprint vector for a set of execution chapters.

    The fingerprint encodes:
    - Function call frequency distribution
    - Execution timing patterns
    - Depth of call nesting
    - Variable type patterns

    Always returns a vector of length 32.

    Args:
        chapters: List of ExecutionChapter objects from one or more runs.

    Returns:
        List of floats representing this codebase's behavioral fingerprint.
        Always returns a vector of length 32.
    """
    if not chapters:
        return [0.0] * 32

    # Get the 8 features from build_feature_vector
    base_features = build_feature_vector(chapters)
    vector = list(base_features)

    # Deterministically derive additional values to fill 32 dimensions
    # For a real implementation in later sprints, this will encode function hashes,
    # but for Sprint 1 this deterministic expansion ensures the shape contract is met.
    while len(vector) < 32:
        idx = len(vector)
        # Create unique mathematical transformations of base features
        val = sum(math.sin(f * (idx + 1)) for f in base_features)
        vector.append(val)

    return vector


def _expand_vector(vector: list[float], target_dim: int) -> list[float]:
    """Deterministically expand a vector to target_dim using sinusoidal features."""
    if len(vector) >= target_dim:
        return vector[:target_dim]
    result = list(vector)
    while len(result) < target_dim:
        idx = len(result)
        val = sum(math.sin(f * (idx + 1)) for f in vector)
        result.append(val)
    return result


def compare_fingerprints(
    fingerprint_a: list[float], fingerprint_b: list[float]
) -> dict[str, float | str]:
    """
    Compare two behavioral fingerprints using cosine similarity.

    Args:
        fingerprint_a: Fingerprint from generate_fingerprint().
        fingerprint_b: Another fingerprint from generate_fingerprint().

    Returns:
        Dict with keys:
            "similarity": float — 0.0 (completely different) to 1.0 (identical)
            "verdict": str — "MATCHES", "SIMILAR", "DIFFERENT", "FOREIGN"
            "message": str — Human-readable explanation
    """
    if len(fingerprint_a) != 32 or len(fingerprint_b) != 32:
        return {
            "similarity": 0.0,
            "verdict": "FOREIGN",
            "message": "Invalid fingerprint length. Fingerprints must be length 32.",
        }

    dot_product = sum(a * b for a, b in zip(fingerprint_a, fingerprint_b))
    norm_a = math.sqrt(sum(a * a for a in fingerprint_a))
    norm_b = math.sqrt(sum(b * b for b in fingerprint_b))

    if norm_a == 0.0 or norm_b == 0.0:
        similarity = 0.0
    else:
        similarity = dot_product / (norm_a * norm_b)

    # Clamp similarity to [0.0, 1.0] range
    similarity = max(0.0, min(1.0, similarity))

    # Determine verdict based on thresholds
    if similarity >= 0.9:
        verdict = "MATCHES"
    elif similarity >= 0.7:
        verdict = "SIMILAR"
    elif similarity >= 0.4:
        verdict = "DIFFERENT"
    else:
        verdict = "FOREIGN"

    msg = f"Behavioral similarity is {similarity * 100:.1f}%. Verdict: {verdict}."

    return {
        "similarity": similarity,
        "verdict": verdict,
        "message": msg,
    }
