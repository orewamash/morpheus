"""
morpheus/teacher.py — Interactive teaching sessions.

Pauses execution after chapters to ask the user CS quiz questions.
Queries the local Ollama LLM to generate questions dynamically.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

import typer

from morpheus.compressor import chapter_to_prompt

if TYPE_CHECKING:
    from rich.console import Console
    from morpheus.compressor import ExecutionChapter
    from morpheus.narrator import OllamaClient


@dataclass
class TeachingQuestion:
    """A single quiz question generated from an execution event."""

    question: str  # The question to ask the user
    options: list[str]  # 3 answer options (a, b, c)
    correct_index: int  # Index of the correct option (0, 1, or 2)
    explanation: str  # Explanation shown after the user answers
    chapter: ExecutionChapter  # The chapter this question relates to


def generate_question(
    chapter: ExecutionChapter, client: OllamaClient
) -> TeachingQuestion:
    """
    Generate a quiz question for a given ExecutionChapter using the LLM.

    Args:
        chapter: The ExecutionChapter to generate a question about.
        client: An initialized OllamaClient instance.

    Returns:
        A TeachingQuestion with 3 options and a correct answer.
    """
    chapter_text = chapter_to_prompt(chapter)

    prompt = (
        "You are a computer science professor. Generate a multiple-choice question for a student "
        "based on the following execution chapter trace:\n\n"
        f"{chapter_text}\n\n"
        "The question must test the student's understanding of the code execution, the specific function "
        "being called, the state changes, or a related computer science concept.\n"
        "You MUST respond in this exact JSON format. Do not add any conversational text or markdown code blocks "
        "around the JSON (do not use backticks):\n"
        "{\n"
        '  "question": "The question text here?",\n'
        '  "options": ["Option A", "Option B", "Option C"],\n'
        '  "correct_index": 0,\n'
        '  "explanation": "Why this option is correct."\n'
        "}"
    )

    fallback_question = TeachingQuestion(
        question=f"Which function was executed in {chapter.title}?",
        options=[chapter.function_name, "None of the above", "sys.exit"],
        correct_index=0,
        explanation=f"The trace events confirm that '{chapter.function_name}()' was called and executed.",
        chapter=chapter,
    )

    try:
        response = client.generate(prompt).strip()

        # Clean JSON markdown blocks if the LLM wrapped it
        if response.startswith("```"):
            # Strip first and last lines
            lines = response.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            response = "\n".join(lines).strip()

        # Regex search to extract the JSON block if extra text is present
        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if json_match:
            response = json_match.group(0)

        data = json.loads(response)

        # Basic verification of fields
        if (
            "question" in data
            and "options" in data
            and "correct_index" in data
            and "explanation" in data
        ):
            opts = data["options"]
            if isinstance(opts, list) and len(opts) >= 3:
                return TeachingQuestion(
                    question=str(data["question"]),
                    options=[str(o) for o in opts[:3]],
                    correct_index=int(data["correct_index"]) % 3,
                    explanation=str(data["explanation"]),
                    chapter=chapter,
                )
    except Exception:
        # Fall back to deterministic question if LLM fails or is offline
        pass

    return fallback_question


def run_teaching_session(
    chapters: list[ExecutionChapter],
    client: OllamaClient,
    console: Console,
) -> dict[str, int | float]:
    """
    Run an interactive teaching session for a list of chapters.
    Pauses after each chapter to ask the user a question.

    Args:
        chapters: List of ExecutionChapter objects.
        client: An initialized OllamaClient instance.
        console: Rich Console for formatted output.

    Returns:
        Score dict: {"correct": int, "total": int, "percentage": float}
    """
    correct = 0
    total = len(chapters)

    if not chapters:
        return {"correct": 0, "total": 0, "percentage": 0.0}

    for chapter in chapters:
        question = generate_question(chapter, client)

        console.print(f"\n[bold cyan]Question for {chapter.title}:[/bold cyan]")
        console.print(f"[bold white]{question.question}[/bold white]")

        for idx, option in enumerate(question.options):
            label = chr(ord("a") + idx)
            console.print(f"  [bold yellow]{label})[/bold yellow] {option}")

        # Prompt for answer
        user_choice = typer.prompt("Your answer (a/b/c)", default="a").strip().lower()
        if user_choice not in ("a", "b", "c"):
            user_choice = "a"

        ans_idx = ord(user_choice) - ord("a")

        if ans_idx == question.correct_index:
            console.print("[bold green][CORRECT] Correct answer![/bold green]")
            correct += 1
        else:
            correct_label = chr(ord("a") + question.correct_index)
            correct_text = question.options[question.correct_index]
            console.print(
                f"[bold red][INCORRECT] Incorrect.[/bold red] The correct answer was [bold yellow]{correct_label}) {correct_text}[/bold yellow]."
            )

        console.print(f"[italic]Explanation:[/italic] {question.explanation}\n")

    percentage = (correct / total) * 100 if total > 0 else 0.0
    return {
        "correct": correct,
        "total": total,
        "percentage": round(percentage, 2),
    }
