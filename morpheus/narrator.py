"""
morpheus/narrator.py — Multi-provider LLM narration engine.

Supports Ollama (local) and OpenRouter (cloud) with automatic fallback.
Configure via environment variables:

  MORPHEUS_LLM_BACKEND    Comma-separated priority list:
                          "ollama,openrouter" (default)
                          "openrouter" (cloud only)
                          "ollama" (local only)

  MORPHEUS_OLLAMA_URL     Default: http://localhost:11434
  MORPHEUS_OLLAMA_MODEL   Default: mistral

  OPENROUTER_API_KEY      Required for openrouter backend
  OPENROUTER_MODEL        Default: mistralai/mistral-7b-instruct
  OPENROUTER_BASE_URL     Default: https://openrouter.ai/api/v1
"""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from typing import Any, Generator

import httpx

from morpheus.compressor import ExecutionChapter, chapter_to_prompt

_llm_warning_shown: bool = False

# ---------------------------------------------------------------------------
#  Environment configuration
# ---------------------------------------------------------------------------

BACKEND_PRIORITY = (
    os.getenv("MORPHEUS_LLM_BACKEND", "ollama,openrouter")
    .lower()
    .replace(" ", "")
    .split(",")
)

OLLAMA_URL = os.getenv("MORPHEUS_OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("MORPHEUS_OLLAMA_MODEL", "mistral")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL", "mistralai/mistral-7b-instruct"
)
OPENROUTER_BASE_URL = os.getenv(
    "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
)


# ---------------------------------------------------------------------------
#  Provider base class
# ---------------------------------------------------------------------------


class LLMProvider(ABC):
    """Abstract base for all LLM providers."""

    name: str = ""

    @abstractmethod
    def generate(self, prompt: str) -> str: ...

    @abstractmethod
    def stream(self, prompt: str) -> Generator[str, None, None]: ...

    @abstractmethod
    def is_available(self) -> bool: ...


# ---------------------------------------------------------------------------
#  Ollama provider
# ---------------------------------------------------------------------------


class OllamaProvider(LLMProvider):
    """Local Ollama LLM backend."""

    name = "ollama"

    def __init__(
        self,
        base_url: str = "",
        model: str = "",
        timeout: float = 120.0,
    ) -> None:
        self.base_url = (base_url or OLLAMA_URL).rstrip("/")
        self.model = model or OLLAMA_MODEL
        self._timeout = timeout

    def is_available(self) -> bool:
        try:
            r = httpx.get(
                f"{self.base_url}/api/tags", timeout=5.0
            )
            return r.status_code == 200
        except httpx.ConnectError:
            return False

    def generate(self, prompt: str) -> str:
        tokens: list[str] = []
        for token in self.stream(prompt):
            tokens.append(token)
        return "".join(tokens)

    def stream(self, prompt: str) -> Generator[str, None, None]:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
        }
        try:
            with httpx.stream(
                "POST",
                url,
                json=payload,
                timeout=self._timeout,
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    token = data.get("response", "")
                    if token:
                        yield token
                    if data.get("done", False):
                        return
        except httpx.ConnectError:
            raise ConnectionError(
                "Ollama is not running. Start it with: ollama serve"
            )
        except httpx.TimeoutException:
            raise httpx.TimeoutException(
                "Ollama took too long to respond. "
                "Try a smaller model or increase timeout."
            )


# ---------------------------------------------------------------------------
#  OpenRouter provider
# ---------------------------------------------------------------------------


class OpenRouterProvider(LLMProvider):
    """Cloud LLM backend via OpenRouter API."""

    name = "openrouter"

    def __init__(
        self,
        api_key: str = "",
        model: str = "",
        base_url: str = "",
        timeout: float = 120.0,
    ) -> None:
        self.api_key = api_key or OPENROUTER_API_KEY
        self.model = model or OPENROUTER_MODEL
        self.base_url = (base_url or OPENROUTER_BASE_URL).rstrip("/")
        self._timeout = timeout

    def is_available(self) -> bool:
        if not self.api_key:
            return False
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            r = httpx.get(
                f"{self.base_url}/models",
                headers=headers,
                timeout=5.0,
            )
            return r.status_code == 200
        except httpx.ConnectError:
            return False

    def generate(self, prompt: str) -> str:
        tokens: list[str] = []
        for token in self.stream(prompt):
            tokens.append(token)
        return "".join(tokens)

    def stream(self, prompt: str) -> Generator[str, None, None]:
        if not self.api_key:
            raise ConnectionError(
                "OpenRouter API key is not set. "
                "Set OPENROUTER_API_KEY environment variable."
            )
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
        }
        try:
            with httpx.stream(
                "POST",
                url,
                json=payload,
                headers=headers,
                timeout=self._timeout,
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line or line.startswith(":"):
                        continue
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        return
                    try:
                        data = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue
                    choice = data.get("choices", [{}])[0]
                    delta = choice.get("delta", {})
                    token = delta.get("content", "")
                    if token:
                        yield token
        except httpx.ConnectError:
            raise ConnectionError(
                "Cannot reach OpenRouter API. Check your internet connection."
            )
        except httpx.TimeoutException:
            raise httpx.TimeoutException(
                "OpenRouter took too long to respond. "
                "Try again later or switch to ollama backend."
            )


# ---------------------------------------------------------------------------
#  Backend orchestrator
# ---------------------------------------------------------------------------

PROVIDER_REGISTRY: dict[str, type[LLMProvider]] = {
    "ollama": OllamaProvider,
    "openrouter": OpenRouterProvider,
}


def _build_providers() -> list[LLMProvider]:
    """Build provider instances in priority order, skipping unavailable backends."""
    providers: list[LLMProvider] = []
    for name in BACKEND_PRIORITY:
        cls = PROVIDER_REGISTRY.get(name)
        if cls is None:
            continue
        providers.append(cls())
    return providers


class LLMBackend:
    """
    Orchestrator that tries providers in priority order with auto-fallback.

    Usage:
        backend = LLMBackend()
        backend.generate("...")
        backend.stream("...")
        backend.provider_name  # "ollama" or "openrouter"
    """

    def __init__(self, providers: list[LLMProvider] | None = None) -> None:
        self._providers = providers or _build_providers()
        self._active: LLMProvider | None = None
        self._failed: set[str] = set()

    @property
    def provider_name(self) -> str:
        if self._active is not None:
            return self._active.name
        return "none"

    def _resolve(self) -> LLMProvider:
        if self._active is not None:
            if (
                self._active.name not in self._failed
                and self._active.is_available()
            ):
                return self._active
            self._active = None

        for provider in self._providers:
            if provider.name in self._failed:
                continue
            if provider.is_available():
                self._active = provider
                return provider

        raise ConnectionError(
            "No LLM backend available.\n"
            "Install Ollama (ollama.com) or set OPENROUTER_API_KEY."
        )

    def generate(self, prompt: str) -> str:
        provider = self._resolve()
        while True:
            try:
                return provider.generate(prompt)
            except (ConnectionError, httpx.TimeoutException):
                self._failed.add(provider.name)
                self._active = None
                provider = self._resolve()

    def stream(self, prompt: str) -> Generator[str, None, None]:
        provider = self._resolve()
        while True:
            try:
                yield from provider.stream(prompt)
                return
            except (ConnectionError, httpx.TimeoutException):
                self._failed.add(provider.name)
                self._active = None
                provider = self._resolve()


# ---------------------------------------------------------------------------
#  Backward-compatible alias
# ---------------------------------------------------------------------------


class OllamaClient(LLMBackend):
    """
    Backward-compatible wrapper that prefers the Ollama provider.
    Falls through to OpenRouter if Ollama is unavailable.

    Use the `backend` parameter to pin a specific provider:
        OllamaClient(backend="ollama")
        OllamaClient(backend="openrouter", model="gpt-4")
    """

    def __init__(
        self,
        model: str = "",
        backend: str = "",
    ) -> None:
        backend_lower = backend.strip().lower()
        providers: list[LLMProvider] = []

        if backend_lower in ("", "auto"):
            ollama = OllamaProvider(model=model.strip() or OLLAMA_MODEL)
            providers.append(ollama)
            for name in BACKEND_PRIORITY:
                if name != "ollama":
                    cls = PROVIDER_REGISTRY.get(name)
                    if cls is not None:
                        providers.append(cls())
        elif backend_lower == "ollama":
            providers.append(
                OllamaProvider(model=model.strip() or OLLAMA_MODEL)
            )
        elif backend_lower == "openrouter":
            providers.append(
                OpenRouterProvider(model=model.strip() or OPENROUTER_MODEL)
            )
        else:
            raise ValueError(
                f"Unknown backend: {backend}. "
                f"Supported: ollama, openrouter, auto"
            )

        super().__init__(providers)
        self.model = providers[0].model if providers else ""


# ---------------------------------------------------------------------------
#  Narration prompt system
# ---------------------------------------------------------------------------

SYSTEM_PROMPTS = {
    "narrator": (
        "You are a runtime narrator. Explain what happened during this code "
        "execution in plain English. Use past tense ('the function loaded...', "
        "'it then called...'). Be concise — 2-4 sentences per chapter maximum. "
        "Never mention variable names unless they are meaningful. Never say "
        "'the code' — say 'the program'."
    ),
    "prophecy": (
        "You are a runtime analyst focused on warnings and anomalies. "
        "Explain what happened but focus on anything that looks dangerous: "
        "unbounded growth, missing error handling, repeated failures, "
        "performance bottlenecks. Flag each issue with a severity: "
        "LOW, MEDIUM, HIGH, CRITICAL."
    ),
    "teach": (
        "You are a computer science professor teaching through this execution. "
        "After each function executes, explain what happened AND connect it to "
        "a foundational CS concept. Then ask the student one question about "
        "what they just observed. Make the question multiple choice with 3 "
        "options labeled a, b, c. Never answer the question yourself."
    ),
}


def build_narration_prompt(chapter: ExecutionChapter, mode: str = "narrator") -> str:
    system_prompt = SYSTEM_PROMPTS.get(mode, SYSTEM_PROMPTS["narrator"])
    chapter_prompt = chapter_to_prompt(chapter)
    return (
        f"System: {system_prompt}\n\n"
        f"Below is a chapter from a program execution trace. "
        f"Narrate what happened:\n\n"
        f"{chapter_prompt}"
    )


def narrate_chapter(
    chapter: ExecutionChapter,
    client: LLMBackend | OllamaClient,
    mode: str = "narrator",
) -> str:
    prompt = build_narration_prompt(chapter, mode)
    try:
        narration = client.generate(prompt)
        if narration.strip():
            return narration.strip()
    except ConnectionError:
        pass
    except Exception:
        pass

    return (
        f"Chapter {chapter.chapter_id}: {chapter.function_name} "
        f"ran for {chapter.duration_ms}ms"
    )


def stream_narration(
    chapter: ExecutionChapter,
    client: LLMBackend | OllamaClient,
    console: Any,
    mode: str = "narrator",
) -> str:
    global _llm_warning_shown
    prompt = build_narration_prompt(chapter, mode)
    tokens: list[str] = []

    try:
        for token in client.stream(prompt):
            console.print(token, end="", highlight=False)
            tokens.append(token)
        console.print()
    except ConnectionError:
        if not _llm_warning_shown:
            console.print(
                "[bold yellow]LLM narration unavailable.[/bold yellow] "
                "Install Ollama (ollama.com) or set OPENROUTER_API_KEY "
                "for narrated explanations. Showing plain summary.\n"
            )
            _llm_warning_shown = True
        fallback = (
            f"Chapter {chapter.chapter_id}: {chapter.function_name} "
            f"ran for {chapter.duration_ms}ms"
        )
        console.print(fallback)
        return fallback
    except Exception:
        fallback = (
            f"Chapter {chapter.chapter_id}: {chapter.function_name} "
            f"ran for {chapter.duration_ms}ms"
        )
        console.print(fallback)
        return fallback

    result = "".join(tokens).strip()
    if not result:
        fallback = (
            f"Chapter {chapter.chapter_id}: {chapter.function_name} "
            f"ran for {chapter.duration_ms}ms"
        )
        console.print(fallback)
        return fallback

    return result
