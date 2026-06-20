"""
tests/conftest.py — Shared pytest fixtures for Morpheus tests.
"""

from __future__ import annotations

import time
import pytest
from morpheus.tracer import TraceEvent
from morpheus.compressor import ExecutionChapter


@pytest.fixture
def sample_events() -> list[TraceEvent]:
    """Returns a minimal list of 3 TraceEvents for use in tests."""
    t = time.time()
    return [
        TraceEvent(
            event_type="call",
            function_name="calculate",
            filename="examples/simple.py",
            line_number=17,
            local_vars={"a": 3, "b": 4},
            timestamp=t,
        ),
        TraceEvent(
            event_type="call",
            function_name="add",
            filename="examples/simple.py",
            line_number=6,
            local_vars={"x": 3, "y": 4},
            timestamp=t + 0.001,
        ),
        TraceEvent(
            event_type="return",
            function_name="add",
            filename="examples/simple.py",
            line_number=7,
            local_vars={"x": 3, "y": 4},
            timestamp=t + 0.002,
            return_value=7,
        ),
    ]


@pytest.fixture
def sample_chapters(sample_events) -> list[ExecutionChapter]:
    """Returns a minimal list of 2 ExecutionChapters for use in tests."""
    return [
        ExecutionChapter(
            chapter_id=1,
            title="Chapter 1: calculate()",
            events=[sample_events[0]],
            summary_hint="function call with 0 nested call(s), 0 return(s)",
            duration_ms=0.0,
            function_name="calculate",
            event_count=1,
        ),
        ExecutionChapter(
            chapter_id=2,
            title="Chapter 2: add()",
            events=sample_events[1:3],
            summary_hint="function call with 0 nested call(s), 1 return(s)",
            duration_ms=1.0,
            function_name="add",
            event_count=2,
        ),
    ]
