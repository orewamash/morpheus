"""Mock-based test verifying narrator works end-to-end with simulated LLM."""
from __future__ import annotations

import json
import pytest
from unittest.mock import patch, MagicMock
from morpheus.narrator import (
    OllamaProvider,
    OpenRouterProvider,
    LLMBackend,
    OllamaClient,
    narrate_chapter,
)
from morpheus.compressor import ExecutionChapter


@pytest.fixture
def chapter():
    return ExecutionChapter(
        chapter_id=1,
        title="Chapter 1: calculate",
        events=[],
        summary_hint="function call with 0 nested calls",
        duration_ms=1.5,
        function_name="calculate",
        event_count=3,
    )


@pytest.fixture
def mock_ollama_available():
    with patch("httpx.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        yield


class TestOllamaProviderWithMock:
    """Verify Ollama provider works with a simulated LLM response."""

    def test_generate_returns_narration(self):
        mock_responses = [
            json.dumps({"response": "The ", "done": False}),
            json.dumps({"response": "function ", "done": False}),
            json.dumps({"response": "ran.", "done": True}),
        ]
        mock_stream = MagicMock()
        mock_stream.__enter__.return_value.iter_lines.return_value = mock_responses

        with patch("httpx.stream", return_value=mock_stream):
            provider = OllamaProvider(base_url="http://localhost:11434", timeout=5)
            result = provider.generate("test prompt")

        assert result == "The function ran."

    def test_stream_yields_tokens(self):
        mock_responses = [
            json.dumps({"response": "Step ", "done": False}),
            json.dumps({"response": "one.", "done": True}),
        ]
        mock_stream = MagicMock()
        mock_stream.__enter__.return_value.iter_lines.return_value = mock_responses

        with patch("httpx.stream", return_value=mock_stream):
            provider = OllamaProvider(base_url="http://localhost:11434", timeout=5)
            tokens = list(provider.stream("test"))

        assert tokens == ["Step ", "one."]


class TestOpenRouterProviderWithMock:
    """Verify OpenRouter provider works with a simulated LLM response."""

    def test_generate_with_api_key(self):
        mock_responses = [
            "data: " + json.dumps({"choices": [{"delta": {"content": "Hello"}}]}),
            "data: " + json.dumps({"choices": [{"delta": {"content": " world"}}]}),
            "data: [DONE]",
        ]
        mock_stream = MagicMock()
        mock_stream.__enter__.return_value.iter_lines.return_value = mock_responses

        with patch("httpx.stream", return_value=mock_stream):
            provider = OpenRouterProvider(
                api_key="test-key", model="test-model", timeout=5
            )
            result = provider.generate("test prompt")

        assert result == "Hello world"

    def test_stream_skips_heartbeats(self):
        mock_responses = [
            ": heartbeart comment",
            "data: " + json.dumps({"choices": [{"delta": {"content": "A"}}]}),
            ": keep-alive",
            "data: [DONE]",
        ]
        mock_stream = MagicMock()
        mock_stream.__enter__.return_value.iter_lines.return_value = mock_responses

        with patch("httpx.stream", return_value=mock_stream):
            provider = OpenRouterProvider(
                api_key="test-key", model="test-model", timeout=5
            )
            tokens = list(provider.stream("test"))

        assert tokens == ["A"]


class TestNarrateChapterWithMock:
    """Verify narrate_chapter uses LLM response when available."""

    def test_narrate_chapter_returns_llm_output(self, chapter, mock_ollama_available):
        mock_responses = [
            json.dumps({"response": "The calculate function processed data.", "done": True}),
        ]
        mock_stream = MagicMock()
        mock_stream.__enter__.return_value.iter_lines.return_value = mock_responses

        with patch("httpx.stream", return_value=mock_stream):
            client = OllamaClient()
            result = narrate_chapter(chapter, client)

        assert result == "The calculate function processed data."

    def test_narrate_chapter_fallback_on_empty(self, chapter, mock_ollama_available):
        mock_responses = [
            json.dumps({"response": "", "done": True}),
        ]
        mock_stream = MagicMock()
        mock_stream.__enter__.return_value.iter_lines.return_value = mock_responses

        with patch("httpx.stream", return_value=mock_stream):
            client = OllamaClient()
            result = narrate_chapter(chapter, client)

        assert "Chapter 1" in result
        assert "calculate" in result

    def test_narrate_chapter_fallback_on_connection_error(self, chapter):
        with patch("httpx.stream", side_effect=ConnectionError("No backend")):
            client = OllamaClient(backend="ollama")
            result = narrate_chapter(chapter, client)

        assert "Chapter 1" in result
        assert "calculate" in result


class TestLLMBackendWithMock:
    """Verify the orchestrator properly falls back between providers."""

    def test_fallback_on_first_provider_failure(self):
        failing_provider = MagicMock()
        failing_provider.name = "failing"
        failing_provider.is_available.return_value = True
        failing_provider.generate.side_effect = ConnectionError("Down")
        failing_provider.stream.side_effect = ConnectionError("Down")

        working_provider = MagicMock()
        working_provider.name = "working"
        working_provider.is_available.return_value = True
        working_provider.generate.return_value = "Fallback narration."
        working_provider.stream.return_value = ["Fallback ", "narration."]

        backend = LLMBackend(providers=[failing_provider, working_provider])
        result = backend.generate("test")

        assert result == "Fallback narration."

    def test_all_providers_fail_raises_error(self):
        failing = MagicMock()
        failing.name = "fail"
        failing.is_available.return_value = True
        failing.generate.side_effect = ConnectionError("Down")

        backend = LLMBackend(providers=[failing])
        with pytest.raises(ConnectionError):
            backend.generate("test")
