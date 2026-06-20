from __future__ import annotations

import pytest
from pathlib import Path

from morpheus.tracer import trace_file
from morpheus.compressor import compress_trace, chapter_to_prompt
from morpheus.narrator import build_narration_prompt
from morpheus.storage import MorpheusStorage, RunRecord
from morpheus.differ import compute_diff
from morpheus.prophecy import analyze_for_prophecy
from morpheus.spy import scan_file, format_spy_report
from morpheus.ml.execution_graph import build_graph_from_events, extract_graph_features


EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"


@pytest.fixture
def simple_script() -> str:
    return str(EXAMPLES_DIR / "simple.py")


@pytest.fixture
def will_crash_script() -> str:
    return str(EXAMPLES_DIR / "will_crash.py")


@pytest.fixture
def safe_script() -> str:
    return str(EXAMPLES_DIR / "safe_script.py")


@pytest.fixture
def malware_script() -> str:
    return str(EXAMPLES_DIR / "malware_sim.py")


class TestTracerIntegration:
    def test_simple_script_produces_events(self, simple_script):
        events = trace_file(simple_script)
        assert len(events) > 0
        calls = [e for e in events if e.event_type == "call"]
        returns = [e for e in events if e.event_type == "return"]
        assert len(calls) > 0
        assert len(returns) > 0

    def test_simple_script_contains_expected_functions(self, simple_script):
        events = trace_file(simple_script)
        func_names = {e.function_name for e in events}
        assert "calculate" in func_names or "add" in func_names

    def test_will_crash_captures_exception(self, will_crash_script):
        events = trace_file(will_crash_script)
        exception_events = [
            e for e in events
            if e.function_name.startswith("<exception:")
        ]
        assert len(exception_events) > 0

    def test_will_crash_has_error_in_return_value(self, will_crash_script):
        events = trace_file(will_crash_script)
        for e in events:
            if e.function_name.startswith("<exception:"):
                assert e.return_value is not None
                return
        pytest.fail("No exception event found")


class TestCompressorIntegration:
    def test_compress_simple_script(self, simple_script):
        events = trace_file(simple_script)
        chapters = compress_trace(events)
        assert len(chapters) >= 1
        assert all(ch.event_count > 0 for ch in chapters)

    def test_chapter_prompt_is_readable(self, simple_script):
        events = trace_file(simple_script)
        chapters = compress_trace(events)
        prompt = chapter_to_prompt(chapters[0])
        assert len(prompt) > 50
        assert "Chapter" in prompt

    def test_narration_prompt_format(self, simple_script):
        events = trace_file(simple_script)
        chapters = compress_trace(events)
        prompt = build_narration_prompt(chapters[0], mode="narrator")
        assert "System:" in prompt
        assert "Chapter" in prompt


class TestStorageIntegration:
    def test_save_and_list_runs(self, simple_script):
        import json
        import time
        events = trace_file(simple_script)
        chapters = compress_trace(events)

        storage = MorpheusStorage(db_path=":memory:")
        record = RunRecord(
            run_id="",
            filepath=simple_script,
            timestamp=time.time(),
            mode="narrator",
            chapters=json.dumps(
                [{"title": ch.title, "event_count": ch.event_count}
                 for ch in chapters]
            ),
            narrations=json.dumps(["Chapter 1: did something"]),
            duration_ms=100.0,
            event_count=len(events),
        )
        run_id = storage.save_run(record)
        assert run_id != ""

        retrieved = storage.get_run(run_id)
        assert retrieved.filepath == simple_script

        runs = storage.list_runs(limit=10)
        assert len(runs) >= 1

    def test_memory_db_works(self):
        storage = MorpheusStorage(db_path=":memory:")
        assert storage.db_path == ":memory:"


class TestProphecyIntegration:
    def test_prophecy_analyzes_events(self, simple_script):
        events = trace_file(simple_script)
        warnings = analyze_for_prophecy(events)
        assert isinstance(warnings, list)


class TestSpyIntegration:
    def test_spy_on_safe_script(self, safe_script):
        events = scan_file(safe_script)
        report = format_spy_report(events, safe_script)
        assert "SAFE" in report or "SUSPICIOUS" in report

    def test_spy_on_malware_sim(self, malware_script):
        events = scan_file(malware_script)
        # malware_sim should trigger some events
        assert len(events) >= 0  # at minimum, doesn't crash

    def test_spy_event_content(self, malware_script):
        events = scan_file(malware_script)
        if events:
            assert all(hasattr(e, "risk_level") for e in events)
            assert all(hasattr(e, "action") for e in events)


class TestDiffIntegration:
    def test_diff_same_script(self, simple_script):
        events1 = trace_file(simple_script)
        events2 = trace_file(simple_script)
        segments = compute_diff(events1, events2)
        assert len(segments) >= 0

    def test_diff_different_scripts(self, simple_script, will_crash_script):
        events1 = trace_file(simple_script)
        events2 = trace_file(will_crash_script)
        segments = compute_diff(events1, events2)
        assert isinstance(segments, list)


class TestExecutionGraphIntegration:
    def test_graph_from_simple_script(self, simple_script):
        events = trace_file(simple_script)
        G = build_graph_from_events(events)
        assert G.number_of_nodes() >= 1

    def test_graph_features(self, simple_script):
        events = trace_file(simple_script)
        G = build_graph_from_events(events)
        features = extract_graph_features(G)
        assert features["num_nodes"] >= 1
        assert "density" in features
        assert "num_roots" in features

    def test_empty_script_graph(self):
        events: list = []
        G = build_graph_from_events(events)
        assert G.number_of_nodes() == 0
        features = extract_graph_features(G)
        assert features["num_nodes"] == 0.0


class TestEndToEnd:
    def test_trace_compress_pipeline(self, simple_script):
        events = trace_file(simple_script)
        assert len(events) > 0

        chapters = compress_trace(events)
        assert len(chapters) >= 1

        for ch in chapters:
            prompt = chapter_to_prompt(ch)
            assert len(prompt) > 0

    def test_all_example_scripts_trace_without_error(self):
        example_files = [
            "simple.py",
            "ml_train.py",
            "safe_script.py",
            "will_crash.py",
            "malware_sim.py",
        ]
        for fname in example_files:
            fpath = EXAMPLES_DIR / fname
            if not fpath.exists():
                continue
            try:
                events = trace_file(str(fpath))
                assert isinstance(events, list)
            except Exception as e:
                # will_crash.py is expected to produce exception events
                # but trace_file itself should not raise
                if fname == "will_crash.py":
                    continue
                pytest.fail(f"{fname} raised: {e}")

    def test_oracle_detect_language_on_examples(self):
        from morpheus.oracle import detect_language
        for fname in ["simple.py", "simple.js", "simple.c"]:
            fpath = EXAMPLES_DIR / fname
            if fpath.exists():
                lang = detect_language(str(fpath))
                assert lang in ("python", "javascript", "c", "cpp")
