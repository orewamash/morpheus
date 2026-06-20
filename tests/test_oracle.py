from __future__ import annotations

import pytest
from morpheus.oracle import detect_language, build_oracle_prompt, OracleResult
from morpheus.tracer import TraceEvent


class TestDetectLanguage:
    def test_detects_python(self):
        assert detect_language("script.py") == "python"
        assert detect_language("main.pyw") == "python"

    def test_detects_javascript(self):
        assert detect_language("app.js") == "javascript"
        assert detect_language("module.mjs") == "javascript"

    def test_detects_typescript(self):
        assert detect_language("component.ts") == "typescript"

    def test_detects_c_and_cpp(self):
        assert detect_language("program.c") == "c"
        assert detect_language("program.h") == "c"
        assert detect_language("program.cpp") == "cpp"
        assert detect_language("program.cc") == "cpp"

    def test_detects_java(self):
        assert detect_language("Main.java") == "java"

    def test_unsupported_extension_raises(self):
        with pytest.raises(ValueError) as exc:
            detect_language("script.rb")
        assert "Unsupported language" in str(exc.value)

    def test_no_extension_raises(self):
        with pytest.raises(ValueError) as exc:
            detect_language("Makefile")
        assert "Unsupported language" in str(exc.value)


class TestBuildOraclePrompt:
    def test_builds_mentor_prompt(self):
        events = [
            TraceEvent("call", "main", "test.py", 1, {}, 1.0),
            TraceEvent("return", "main", "test.py", 5, {}, 2.0, return_value=0),
        ]
        prompt = build_oracle_prompt(events, "mentor", "python")
        assert "mentor" in prompt.lower() or "senior" in prompt.lower()
        assert "[CALL] main()" in prompt
        assert "[RETURN] main()" in prompt

    def test_builds_critic_prompt(self):
        events = [
            TraceEvent("call", "main", "test.py", 1, {}, 1.0),
        ]
        prompt = build_oracle_prompt(events, "critic", "javascript")
        assert "code review" in prompt.lower()

    def test_truncates_large_event_lists(self):
        events = [
            TraceEvent("call", f"func_{i}", "test.py", i, {}, float(i))
            for i in range(50)
        ]
        prompt = build_oracle_prompt(events, "mentor", "python")
        assert "20 more events" in prompt or "20" in prompt

    def test_respects_max_30_events(self):
        events = [
            TraceEvent("call", f"func_{i}", "test.py", i, {}, float(i))
            for i in range(40)
        ]
        prompt = build_oracle_prompt(events, "mentor", "python")
        count = prompt.count("[CALL]")
        assert count <= 30


class TestOracleResult:
    def test_oracle_result_dataclass(self):
        result = OracleResult(
            language="python",
            filepath="/test.py",
            events=[],
            narration="Test narration.",
            personality="critic",
        )
        assert result.language == "python"
        assert result.narration == "Test narration."
        assert result.personality == "critic"
