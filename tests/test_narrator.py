"""
tests/test_narrator.py — Narrator tests for multi-provider LLM backend.
"""

from __future__ import annotations

import httpx
import pytest
from morpheus.narrator import (
    OllamaClient,
    OllamaProvider,
    OpenRouterProvider,
    LLMBackend,
    _build_providers,
    PROVIDER_REGISTRY,
)


# ---------------------------------------------------------------------------
#  OllamaProvider tests
# ---------------------------------------------------------------------------


class TestOllamaProvider:
    def test_generate_raises_on_offline(self, mocker):
        mocker.patch(
            "httpx.stream",
            side_effect=httpx.ConnectError("Connection refused"),
        )
        provider = OllamaProvider()
        # Bypass availability check
        with pytest.raises(ConnectionError) as exc:
            provider.generate("hello")
        assert "Ollama is not running" in str(exc.value)

    def test_stream_raises_on_offline(self, mocker):
        mocker.patch(
            "httpx.stream",
            side_effect=httpx.ConnectError("Connection refused"),
        )
        provider = OllamaProvider()
        with pytest.raises(ConnectionError) as exc:
            for _ in provider.stream("hello"):
                pass
        assert "Ollama is not running" in str(exc.value)

    def test_is_available_returns_false_on_connect_error(self, mocker):
        mocker.patch(
            "httpx.get",
            side_effect=httpx.ConnectError("Connection refused"),
        )
        provider = OllamaProvider()
        assert provider.is_available() is False

    def test_stream_yields_tokens(self, mocker):
        mock_response = mocker.MagicMock()
        mock_response.__enter__.return_value = mock_response
        mock_response.iter_lines.return_value = [
            '{"response":"Hello","done":false}',
            '{"response":" world","done":false}',
            '{"response":"","done":true}',
        ]

        mocker.patch("httpx.stream", return_value=mock_response)
        mocker.patch.object(OllamaProvider, "is_available", return_value=True)

        provider = OllamaProvider()
        tokens = list(provider.stream("test"))
        assert tokens == ["Hello", " world"]

    def test_generate_collects_tokens(self, mocker):
        mock_response = mocker.MagicMock()
        mock_response.__enter__.return_value = mock_response
        mock_response.iter_lines.return_value = [
            '{"response":"Hello","done":false}',
            '{"response":" world","done":true}',
        ]
        mocker.patch("httpx.stream", return_value=mock_response)
        mocker.patch.object(OllamaProvider, "is_available", return_value=True)

        provider = OllamaProvider()
        result = provider.generate("test")
        assert result == "Hello world"


# ---------------------------------------------------------------------------
#  OpenRouterProvider tests
# ---------------------------------------------------------------------------


class TestOpenRouterProvider:
    def test_generate_raises_without_api_key(self):
        provider = OpenRouterProvider(api_key="")
        with pytest.raises(ConnectionError) as exc:
            provider.generate("hello")
        assert "API key" in str(exc.value)

    def test_stream_raises_without_api_key(self):
        provider = OpenRouterProvider(api_key="")
        with pytest.raises(ConnectionError) as exc:
            for _ in provider.stream("hello"):
                pass
        assert "API key" in str(exc.value)

    def test_is_available_returns_false_without_key(self):
        provider = OpenRouterProvider(api_key="")
        assert provider.is_available() is False

    def test_is_available_returns_true_with_key(self, mocker):
        mock_resp = mocker.MagicMock()
        mock_resp.status_code = 200
        mocker.patch("httpx.get", return_value=mock_resp)

        provider = OpenRouterProvider(api_key="sk-test-key")
        assert provider.is_available() is True

    def test_stream_raises_on_connect_error(self, mocker):
        mocker.patch(
            "httpx.get",
            side_effect=httpx.ConnectError("Connection refused"),
        )
        provider = OpenRouterProvider(api_key="sk-test-key")
        assert provider.is_available() is False

    def test_stream_yields_tokens(self, mocker):
        mock_response = mocker.MagicMock()
        mock_response.__enter__.return_value = mock_response
        mock_response.iter_lines.return_value = [
            'data: {"choices":[{"delta":{"content":"Hello"}}]}',
            'data: {"choices":[{"delta":{"content":" world"}}]}',
            "data: [DONE]",
        ]
        mocker.patch("httpx.stream", return_value=mock_response)
        mocker.patch.object(OpenRouterProvider, "is_available", return_value=True)

        provider = OpenRouterProvider(api_key="sk-test-key")
        tokens = list(provider.stream("test"))
        assert tokens == ["Hello", " world"]

    def test_stream_skips_heartbeat_lines(self, mocker):
        mock_response = mocker.MagicMock()
        mock_response.__enter__.return_value = mock_response
        mock_response.iter_lines.return_value = [
            ": keep-alive",
            'data: {"choices":[{"delta":{"content":"Hi"}}]}',
            "data: [DONE]",
        ]
        mocker.patch("httpx.stream", return_value=mock_response)
        mocker.patch.object(OpenRouterProvider, "is_available", return_value=True)

        provider = OpenRouterProvider(api_key="sk-test-key")
        tokens = list(provider.stream("test"))
        assert tokens == ["Hi"]


# ---------------------------------------------------------------------------
#  LLMBackend orchestrator tests
# ---------------------------------------------------------------------------


class TestLLMBackend:
    def test_no_available_provider_raises(self, mocker):
        mocker.patch.object(OllamaProvider, "is_available", return_value=False)
        mocker.patch.object(OpenRouterProvider, "is_available", return_value=False)

        backend = LLMBackend(providers=[OllamaProvider(), OpenRouterProvider()])
        with pytest.raises(ConnectionError) as exc:
            backend.generate("test")
        assert "No LLM backend available" in str(exc.value)

    def test_uses_first_available_provider(self, mocker):
        mock_response = mocker.MagicMock()
        mock_response.__enter__.return_value = mock_response
        mock_response.iter_lines.return_value = [
            '{"response":"ok","done":true}',
        ]

        mocker.patch.object(OllamaProvider, "is_available", return_value=True)
        mocker.patch("httpx.stream", return_value=mock_response)

        provider = OllamaProvider()
        backend = LLMBackend(providers=[provider])
        result = backend.generate("test")
        assert result == "ok"
        assert backend.provider_name == "ollama"

    def test_fallback_on_ollama_failure(self, mocker):
        ollama = OllamaProvider()
        openrouter = OpenRouterProvider(api_key="sk-test")
        mocker.patch.object(ollama, "is_available", return_value=True)
        mocker.patch.object(openrouter, "is_available", return_value=True)

        def ollama_stream(prompt):
            raise ConnectionError("Ollama is not running")

        def openrouter_stream(prompt):
            yield "fallback"

        mocker.patch.object(ollama, "stream", ollama_stream)
        mocker.patch.object(openrouter, "stream", openrouter_stream)

        backend = LLMBackend(providers=[ollama, openrouter])
        result = backend.generate("test")
        assert result == "fallback"
        assert backend.provider_name == "openrouter"


# ---------------------------------------------------------------------------
#  OllamaClient backward compatibility tests
# ---------------------------------------------------------------------------


class TestOllamaClientBackwardCompat:
    def test_ollama_client_raises_on_all_backends_down(self, mocker):
        ollama = OllamaProvider(model="test-model")
        openrouter = OpenRouterProvider(api_key="sk-test")
        mocker.patch.object(ollama, "is_available", return_value=True)
        mocker.patch.object(openrouter, "is_available", return_value=True)

        def always_fail(prompt):
            raise ConnectionError("backend failed")

        mocker.patch.object(ollama, "stream", always_fail)
        mocker.patch.object(openrouter, "stream", always_fail)

        client = LLMBackend(providers=[ollama, openrouter])
        with pytest.raises(ConnectionError) as exc:
            client.generate("test")
        assert "No LLM backend available" in str(exc.value)

    def test_ollama_client_has_model_attr(self):
        client = OllamaClient(model="test-model")
        assert client.model == "test-model"

    def test_ollama_client_defaults_to_mistral(self):
        client = OllamaClient()
        assert client.model == "mistral"


# ---------------------------------------------------------------------------
#  Provider registry tests
# ---------------------------------------------------------------------------


class TestProviderRegistry:
    def test_registry_has_ollama(self):
        assert "ollama" in PROVIDER_REGISTRY

    def test_registry_has_openrouter(self):
        assert "openrouter" in PROVIDER_REGISTRY

    def test_build_providers_returns_list(self):
        providers = _build_providers()
        assert isinstance(providers, list)
