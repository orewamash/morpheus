"""
tests/test_compressor.py — Compressor tests for Morpheus.
"""

from __future__ import annotations

from morpheus.compressor import compress_trace, chapter_to_prompt


def test_compress_creates_chapters(sample_events):
    """compress_trace() must return at least 1 chapter when given a non-empty event list."""
    chapters = compress_trace(sample_events)
    assert len(chapters) >= 1
    assert chapters[0].function_name == "calculate"


def test_chapter_to_prompt_returns_string(sample_chapters):
    """chapter_to_prompt() must return a non-empty string."""
    prompt = chapter_to_prompt(sample_chapters[0])
    assert isinstance(prompt, str)
    assert len(prompt.strip()) > 0
    assert "Chapter 1: calculate()" in prompt
