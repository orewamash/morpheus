"""
tests/test_concept_writer.py — Tests for ConceptWriter with embeddings.
"""

from __future__ import annotations

from morpheus.tracer import TraceEvent
from morpheus.compressor import ExecutionChapter
from morpheus.ml.concept_writer import ConceptWriter, _cosine_similarity


def _make_chapters(names: list[str]) -> list[ExecutionChapter]:
    chapters = []
    for i, name in enumerate(names):
        t = 1000.0
        events = [
            TraceEvent("call", name, "test.py", 1, {}, t),
            TraceEvent("return", name, "test.py", 5, {}, t + 0.1),
        ]
        chapters.append(
            ExecutionChapter(
                chapter_id=i + 1,
                title=f"Chapter: {name}()",
                events=events,
                summary_hint="",
                duration_ms=5.0,
                function_name=name,
                event_count=2,
            )
        )
    return chapters


class TestConceptWriter:
    def test_empty_chapters(self):
        cw = ConceptWriter()
        result = cw.infer_concept([])
        assert result["concept"] == "unknown"

    def test_ml_keyword_detected(self):
        cw = ConceptWriter()
        chapters = _make_chapters(["train_model", "predict"])
        result = cw.infer_concept(chapters)
        assert result["concept"] == "machine_learning_pipeline"

    def test_data_keyword_detected(self):
        cw = ConceptWriter()
        chapters = _make_chapters(["load_csv", "parse_data"])
        result = cw.infer_concept(chapters)
        assert result["concept"] == "data_processing_pipeline"

    def test_io_keyword_detected(self):
        cw = ConceptWriter()
        chapters = _make_chapters(["make_request", "connect_socket"])
        result = cw.infer_concept(chapters)
        assert result["concept"] == "io_bound_operation"

    def test_compute_keyword_detected(self):
        cw = ConceptWriter()
        chapters = _make_chapters(["compute_result", "solve_equation"])
        result = cw.infer_concept(chapters)
        assert result["concept"] == "computational_kernel"

    def test_simple_fallback(self):
        cw = ConceptWriter()
        chapters = _make_chapters(["run"])
        result = cw.infer_concept(chapters)
        assert result["concept"] == "simple_computational_module"

    def test_learn_and_match(self):
        cw = ConceptWriter()
        ref = _make_chapters(["train", "predict", "score"])
        cw.learn_concept("machine_learning_workflow", ref)

        test_chapters = _make_chapters(["train_model", "predict_result"])
        result = cw.infer_concept(test_chapters)
        # Either keyword-match or embedding-similarity
        assert "machine_learning" in result["concept"]

    def test_return_embedding(self):
        cw = ConceptWriter()
        chapters = _make_chapters(["foo"])
        result = cw.infer_concept(chapters)
        assert "embedding" in result
        assert len(result["embedding"]) == 16

    def test_distinct_concepts_different_embeddings(self):
        cw = ConceptWriter()
        io_chapters = _make_chapters(["read_file", "write_response"])
        ml_chapters = _make_chapters(["train", "predict"])

        io_result = cw.infer_concept(io_chapters)
        ml_result = cw.infer_concept(ml_chapters)

        # Different function names should produce different concepts
        assert io_result["concept"] != ml_result["concept"]


class TestCosineSimilarity:
    def test_identical(self):
        assert _cosine_similarity([1, 0], [1, 0]) == 1.0

    def test_orthogonal(self):
        assert _cosine_similarity([1, 0], [0, 1]) == 0.0

    def test_different_lengths(self):
        assert _cosine_similarity([1], [1, 0]) == 0.0

    def test_zero_vector(self):
        assert _cosine_similarity([0, 0], [1, 0]) == 0.0
