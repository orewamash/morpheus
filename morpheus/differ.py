from __future__ import annotations

from dataclasses import dataclass

from morpheus.compressor import compress_trace
from morpheus.storage import MorpheusStorage
from morpheus.tracer import TraceEvent


@dataclass
class DiffSegment:
    status: str  # "SAME", "CHANGED", "ADDED", "REMOVED"
    context: str  # function name or chapter description
    run1_info: str  # what happened in run 1
    run2_info: str  # what happened in run 2


def load_run_events(run_id_or_path: str) -> list[TraceEvent]:
    try:
        storage = MorpheusStorage()
        record = storage.get_run(run_id_or_path)
        return _reconstruct_events(record)
    except (KeyError, Exception):
        from morpheus.tracer import trace_file
        return trace_file(run_id_or_path)


def _reconstruct_events(record) -> list[TraceEvent]:
    import json
    import time
    try:
        chapters_data = json.loads(record.chapters)
    except Exception:
        chapters_data = []

    events: list[TraceEvent] = []
    t = time.time()
    for i, ch in enumerate(chapters_data):
        title = ch.get("title", f"Chapter {i + 1}")
        func_name = title.split(": ")[-1].rstrip("()") if ": " in title else "unknown"
        events.append(TraceEvent("call", func_name, record.filepath, i * 10 + 1, {}, t + i * 0.001))
        events.append(TraceEvent("return", func_name, record.filepath, i * 10 + 5, {}, t + i * 0.002))
    return events


def compute_diff(
    events1: list[TraceEvent],
    events2: list[TraceEvent],
) -> list[DiffSegment]:
    chapters1 = compress_trace(events1)
    chapters2 = compress_trace(events2)

    segments: list[DiffSegment] = []
    max_len = max(len(chapters1), len(chapters2))

    for i in range(max_len):
        if i < len(chapters1) and i < len(chapters2):
            ch1 = chapters1[i]
            ch2 = chapters2[i]

            if ch1.function_name == ch2.function_name and ch1.event_count == ch2.event_count:
                status = "SAME"
            else:
                status = "CHANGED"

            segments.append(DiffSegment(
                status=status,
                context=ch1.function_name if ch1.function_name == ch2.function_name
                else f"{ch1.function_name} vs {ch2.function_name}",
                run1_info=f"{ch1.title} ({ch1.event_count} events, {ch1.duration_ms:.1f}ms)",
                run2_info=f"{ch2.title} ({ch2.event_count} events, {ch2.duration_ms:.1f}ms)",
            ))
        elif i < len(chapters1):
            ch1 = chapters1[i]
            segments.append(DiffSegment(
                status="REMOVED",
                context=ch1.function_name,
                run1_info=f"{ch1.title} ({ch1.event_count} events, {ch1.duration_ms:.1f}ms)",
                run2_info="(not present)",
            ))
        else:
            ch2 = chapters2[i]
            segments.append(DiffSegment(
                status="ADDED",
                context=ch2.function_name,
                run1_info="(not present)",
                run2_info=f"{ch2.title} ({ch2.event_count} events, {ch2.duration_ms:.1f}ms)",
            ))

    return segments


def format_diff_report(segments: list[DiffSegment], name1: str, name2: str) -> str:
    lines = [
        "Morpheus Time Travel Diff",
        f"Comparing: {name1} vs {name2}",
        "=" * 60,
    ]

    if not segments:
        lines.append("No chapters to compare.")
        return "\n".join(lines)

    same_count = sum(1 for s in segments if s.status == "SAME")
    changed_count = sum(1 for s in segments if s.status == "CHANGED")
    added_count = sum(1 for s in segments if s.status == "ADDED")
    removed_count = sum(1 for s in segments if s.status == "REMOVED")

    lines.append(f"\nSame: {same_count} | Changed: {changed_count} | Added: {added_count} | Removed: {removed_count}")
    lines.append("")

    for seg in segments:
        if seg.status == "SAME":
            lines.append(f"[SAME]   {seg.context}")
            lines.append(f"         Run 1: {seg.run1_info}")
            lines.append(f"         Run 2: {seg.run2_info}")
        elif seg.status == "CHANGED":
            lines.append(f"[CHANGE] {seg.context}")
            lines.append(f"         Run 1: {seg.run1_info}")
            lines.append(f"         Run 2: {seg.run2_info}")
        elif seg.status == "ADDED":
            lines.append(f"[ADDED]  {seg.context}")
            lines.append(f"         Run 2: {seg.run2_info}")
        elif seg.status == "REMOVED":
            lines.append(f"[REMOVED]{seg.context}")
            lines.append(f"         Run 1: {seg.run1_info}")

        lines.append("")

    return "\n".join(lines)
