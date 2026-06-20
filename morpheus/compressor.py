"""
morpheus/compressor.py — Trace event compressor.

Converts a raw list of TraceEvents into grouped ExecutionChapters that can
be sent to the LLM. Raw traces are too large and too noisy for direct
LLM consumption.

Dependency rules: May import from tracer only.
"""

from __future__ import annotations

from dataclasses import dataclass

from morpheus.tracer import TraceEvent


@dataclass
class ExecutionChapter:
    """
    A grouped, summarized segment of an execution trace.
    Each chapter represents one logical unit of work — typically one
    top-level function call.
    """

    chapter_id: int  # Sequential ID starting from 1
    title: str  # Human-readable title e.g. "Chapter 3: train_model()"
    events: list[TraceEvent]  # The raw events that belong to this chapter
    summary_hint: str  # Short context string passed to LLM
    duration_ms: float  # Total time from first to last event in this chapter
    function_name: str  # Name of the top-level function for this chapter
    event_count: int  # Total number of events in this chapter


MAX_EVENTS_PER_CHAPTER = 10


def compress_trace(events: list[TraceEvent]) -> list[ExecutionChapter]:
    """
    Group a list of TraceEvents into ExecutionChapters.

    Grouping rules:
    1. Group by top-level function boundary: each "call" event starts
       a potential chapter.
    2. Max 10 events per chapter. If a function has more than 10 events,
       split it.
    3. Each chapter includes timing: duration_ms =
       (last_event.timestamp - first_event.timestamp) * 1000
    4. Empty event list returns empty chapter list.

    Args:
        events: List of TraceEvent objects from trace_file().

    Returns:
        List of ExecutionChapter objects. At least 1 chapter for any
        non-empty event list.

    Example:
        chapters = compress_trace(events)
        print(f"Compressed {len(events)} events into {len(chapters)} chapters")
    """
    if not events:
        return []

    chapters: list[ExecutionChapter] = []
    chapter_id = 1

    # Group events by top-level function boundaries
    groups: list[list[TraceEvent]] = []
    current_group: list[TraceEvent] = []
    call_depth = 0

    for event in events:
        if event.event_type == "call" and call_depth == 0:
            # Start of a new top-level function call
            if current_group:
                groups.append(current_group)
            current_group = [event]
            call_depth = 1
        elif event.event_type == "call":
            call_depth += 1
            current_group.append(event)
        elif event.event_type == "return":
            current_group.append(event)
            call_depth = max(0, call_depth - 1)
        else:
            current_group.append(event)

    # Don't forget the last group
    if current_group:
        groups.append(current_group)

    # If no natural grouping occurred, treat all events as one group
    if not groups:
        groups = [events]

    # Convert groups into chapters, splitting if > MAX_EVENTS_PER_CHAPTER
    for group in groups:
        # Determine the top-level function name
        func_name = group[0].function_name if group else "<unknown>"

        # Split large groups
        for i in range(0, len(group), MAX_EVENTS_PER_CHAPTER):
            chunk = group[i : i + MAX_EVENTS_PER_CHAPTER]

            # Calculate duration
            if len(chunk) >= 2:
                duration_ms = (chunk[-1].timestamp - chunk[0].timestamp) * 1000
            else:
                duration_ms = 0.0

            # Count nested calls for the hint
            nested_calls = sum(
                1 for e in chunk if e.event_type == "call" and e != chunk[0]
            )
            returns = sum(1 for e in chunk if e.event_type == "return")

            # Build summary hint
            if nested_calls > 0:
                hint = (
                    f"function call with {nested_calls} nested call(s), "
                    f"{returns} return(s)"
                )
            else:
                hint = f"function call with {returns} return(s)"

            # Add split indicator if this is a continuation
            suffix = ""
            if len(group) > MAX_EVENTS_PER_CHAPTER and i > 0:
                part = (i // MAX_EVENTS_PER_CHAPTER) + 1
                total_parts = (
                    len(group) + MAX_EVENTS_PER_CHAPTER - 1
                ) // MAX_EVENTS_PER_CHAPTER
                suffix = f" (part {part}/{total_parts})"

            chapter = ExecutionChapter(
                chapter_id=chapter_id,
                title=f"Chapter {chapter_id}: {func_name}(){suffix}",
                events=chunk,
                summary_hint=hint,
                duration_ms=round(duration_ms, 2),
                function_name=func_name,
                event_count=len(chunk),
            )
            chapters.append(chapter)
            chapter_id += 1

    return chapters


def chapter_to_prompt(chapter: ExecutionChapter) -> str:
    """
    Convert an ExecutionChapter into a formatted string prompt for the LLM.

    The output string must:
    - Start with the chapter title
    - List each event clearly: event type, function name, line number
    - Include local variable snapshots for key events (call and return only)
    - Include timing information
    - End with the summary_hint
    - Be under 2000 characters total (to fit within context window)

    Args:
        chapter: An ExecutionChapter to format.

    Returns:
        A non-empty string formatted as an LLM prompt.
    """
    lines: list[str] = []

    # Header
    lines.append(chapter.title)
    lines.append(
        f"Duration: {chapter.duration_ms:.1f}ms | Events: {chapter.event_count}"
    )
    lines.append("")

    # Event listing
    for event in chapter.events:
        event_tag = event.event_type.upper()

        if event.event_type == "return" and event.return_value is not None:
            event_line = (
                f"[{event_tag}] {event.function_name}() at line "
                f"{event.line_number} → {_truncate(repr(event.return_value), 80)}"
            )
        else:
            event_line = (
                f"[{event_tag}] {event.function_name}() at line {event.line_number}"
            )

        lines.append(event_line)

        # Include local vars (abbreviated)
        if event.local_vars:
            var_strs = []
            for k, v in list(event.local_vars.items())[:5]:
                var_strs.append(f"{k}={_truncate(repr(v), 40)}")
            if var_strs:
                lines.append(f"  locals: {', '.join(var_strs)}")

    lines.append("")
    lines.append(f"Hint: {chapter.summary_hint}")

    result = "\n".join(lines)

    # Enforce the 2000 character limit
    if len(result) > 2000:
        result = result[:1950] + "\n... (truncated for context window)"

    return result


def _truncate(text: str, max_len: int) -> str:
    """Truncate a string to max_len characters, adding ellipsis if needed."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."
