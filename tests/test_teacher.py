from __future__ import annotations

from morpheus.teacher import TeachingQuestion, generate_question
from morpheus.compressor import ExecutionChapter
from morpheus.tracer import TraceEvent
from morpheus.narrator import OllamaClient
import time


def _make_chapter() -> ExecutionChapter:
    t = time.time()
    return ExecutionChapter(
        chapter_id=1,
        title="Chapter 1: calculate()",
        events=[
            TraceEvent(
                event_type="call",
                function_name="calculate",
                filename="test.py",
                line_number=5,
                local_vars={"a": 3, "b": 4},
                timestamp=t,
            ),
            TraceEvent(
                event_type="return",
                function_name="calculate",
                filename="test.py",
                line_number=10,
                local_vars={"a": 3, "b": 4},
                timestamp=t + 0.01,
                return_value=7,
            ),
        ],
        summary_hint="function call, 1 return",
        duration_ms=10.0,
        function_name="calculate",
        event_count=2,
    )


def test_teaching_question_dataclass():
    chapter = _make_chapter()
    q = TeachingQuestion(
        question="What did calculate() return?",
        options=["3", "7", "None"],
        correct_index=1,
        explanation="calculate returned 7.",
        chapter=chapter,
    )
    assert q.question == "What did calculate() return?"
    assert q.correct_index == 1
    assert q.options[1] == "7"


def test_generate_question_fallback(mocker):
    chapter = _make_chapter()
    client = OllamaClient()

    mocker.patch.object(client, "generate", return_value="invalid response")

    question = generate_question(chapter, client)
    assert question.chapter == chapter
    assert question.correct_index == 0
    assert chapter.function_name in question.options[0]


def test_generate_question_parses_json(mocker):
    chapter = _make_chapter()
    client = OllamaClient()

    mock_json = (
        '{"question": "Test Q?", '
        '"options": ["A", "B", "C"], '
        '"correct_index": 2, '
        '"explanation": "Because."}'
    )
    mocker.patch.object(client, "generate", return_value=mock_json)

    question = generate_question(chapter, client)
    assert question.question == "Test Q?"
    assert question.correct_index == 2
    assert question.options == ["A", "B", "C"]
    assert question.explanation == "Because."


def test_generate_question_handles_markdown_json(mocker):
    chapter = _make_chapter()
    client = OllamaClient()

    mock_response = (
        "```json\n"
        '{"question": "MD Q?", '
        '"options": ["X", "Y", "Z"], '
        '"correct_index": 1, '
        '"explanation": "Markdown."}\n'
        "```"
    )
    mocker.patch.object(client, "generate", return_value=mock_response)

    question = generate_question(chapter, client)
    assert question.question == "MD Q?"
    assert question.correct_index == 1
