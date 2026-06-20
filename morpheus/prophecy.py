"""
morpheus/prophecy.py — Proactive execution pattern analysis.

Detects potential crash-prone execution patterns before they cause errors.
Implemented checks:
1. Unbounded list growth
2. Recursion depth (>50)
3. Large variable sizes (>10,000 items)
4. Missing return value
5. Rapid repeated calls (>100)
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from rich.console import Console
from rich.table import Table

from morpheus.tracer import TraceEvent


@dataclass
class ProphecyWarning:
    """A single detected warning from prophecy analysis."""

    severity: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    function_name: str  # Function where the pattern was detected
    line_number: int  # Line number of concern
    message: str  # Plain English warning message
    suggestion: str  # What the user should do about it


def _get_collection_size(val_str: str) -> int | None:
    """Helper to parse size of collections from serialized string representation."""
    if not isinstance(val_str, str):
        return None

    # Check for truncated lists
    match_list = re.search(r"<list with (\d+) items>", val_str)
    if match_list:
        return int(match_list.group(1))

    # Check for truncated dicts
    match_dict = re.search(r"<dict with (\d+) keys>", val_str)
    if match_dict:
        return int(match_dict.group(1))

    # Parse short lists
    if val_str.startswith("[") and val_str.endswith("]"):
        if val_str == "[]":
            return 0
        return val_str.count(",") + 1

    # Parse short dicts
    if val_str.startswith("{") and val_str.endswith("}"):
        if val_str == "{}":
            return 0
        return val_str.count(":")

    return None


def analyze_for_prophecy(events: list[TraceEvent]) -> list[ProphecyWarning]:
    """
    Analyze a list of TraceEvents for dangerous patterns.

    Args:
        events: List of TraceEvent objects from trace_file().

    Returns:
        List of ProphecyWarning objects sorted by severity.
    """
    warnings: list[ProphecyWarning] = []
    if not events:
        return warnings

    # --- 1. Unbounded List Growth & 3. Large Variables ---
    # Track variable sizes per function: func_vars[func_name][var_name] = list of (line_number, size)
    func_vars: dict[str, dict[str, list[tuple[int, int]]]] = {}

    # --- 2. Recursion Depth ---
    stack: list[str] = []

    # --- 5. Rapid Repeated Calls ---
    call_counts: dict[str, int] = {}
    func_lines: dict[str, int] = {}

    for event in events:
        func_name = event.function_name
        line_num = event.line_number

        if event.event_type == "call":
            call_counts[func_name] = call_counts.get(func_name, 0) + 1
            func_lines[func_name] = line_num

            # Recursion check
            stack.append(func_name)
            depth = stack.count(func_name)
            if depth > 50:
                warnings.append(
                    ProphecyWarning(
                        severity="CRITICAL",
                        function_name=func_name,
                        line_number=line_num,
                        message=f"Deep recursion detected. function '{func_name}' is nested {depth} times.",
                        suggestion="Refactor recursion to an iterative loop or increase stack depth limit.",
                    )
                )

            # Analyze local variables for growth and large size
            if func_name not in func_vars:
                func_vars[func_name] = {}

            for var_name, var_val in event.local_vars.items():
                size = _get_collection_size(str(var_val))
                if size is not None:
                    if var_name not in func_vars[func_name]:
                        func_vars[func_name][var_name] = []
                    func_vars[func_name][var_name].append((line_num, size))

                    # Check large size
                    if size > 10000:
                        warnings.append(
                            ProphecyWarning(
                                severity="HIGH",
                                function_name=func_name,
                                line_number=line_num,
                                message=f"Large variable '{var_name}' detected. Holds {size} items.",
                                suggestion="Verify if holding this many items in memory is necessary; consider generator.",
                            )
                        )

        elif event.event_type == "return":
            if stack and func_name in stack:
                # Remove from stack from the end
                for idx in range(len(stack) - 1, -1, -1):
                    if stack[idx] == func_name:
                        stack.pop(idx)
                        break

            # --- 4. Missing Return Value ---
            # If function returns None, but name suggests a computation/getter
            computational_prefixes = (
                "calculate",
                "add",
                "multiply",
                "get",
                "parse",
                "process",
                "solve",
                "make",
                "create",
            )
            is_computational = any(
                func_name.lower().startswith(p) for p in computational_prefixes
            )
            if (
                event.return_value is None or str(event.return_value) == "None"
            ) and is_computational:
                # Check that it is not a constructor/init
                if func_name != "__init__":
                    warnings.append(
                        ProphecyWarning(
                            severity="MEDIUM",
                            function_name=func_name,
                            line_number=line_num,
                            message=f"Function '{func_name}' returned None, but is named like a computational function.",
                            suggestion="Check if a return statement was omitted or a edge-case returned None unexpectedly.",
                        )
                    )

    # Check unbounded growth after gathering history
    for func_name, vars_dict in func_vars.items():
        for var_name, size_history in vars_dict.items():
            if len(size_history) >= 3:
                sizes = [item[1] for item in size_history]
                # Check if strictly increasing
                is_growing = all(
                    sizes[i] < sizes[i + 1] for i in range(len(sizes) - 1)
                )
                if is_growing:
                    # Report growth warning at the last recorded line
                    last_line = size_history[-1][0]
                    warnings.append(
                        ProphecyWarning(
                            severity="HIGH",
                            function_name=func_name,
                            line_number=last_line,
                            message=f"Unbounded collection growth for '{var_name}'. Size grew continuously: {sizes}.",
                            suggestion="Ensure items are popped or cleared, or check for infinite loops adding elements.",
                        )
                    )

    # Check rapid repeated calls
    for func_name, count in call_counts.items():
        if count > 100:
            warnings.append(
                ProphecyWarning(
                    severity="MEDIUM",
                    function_name=func_name,
                    line_number=func_lines.get(func_name, 0),
                    message=f"Rapid repeated calls. Function '{func_name}' was called {count} times.",
                    suggestion="Optimize caller to cache results or batch execution to prevent overhead.",
                )
            )

    # Deduplicate warnings (same message, line, and function)
    unique_warnings: list[ProphecyWarning] = []
    seen = set()
    for w in warnings:
        key = (w.severity, w.function_name, w.line_number, w.message)
        if key not in seen:
            seen.add(key)
            unique_warnings.append(w)

    # Sort by severity priority: CRITICAL, HIGH, MEDIUM, LOW
    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    unique_warnings.sort(
        key=lambda w: severity_order.get(w.severity, 4)
    )

    return unique_warnings


def format_prophecy_report(warnings: list[ProphecyWarning]) -> str:
    """
    Format a list of ProphecyWarning objects into a terminal-ready report string.

    Args:
        warnings: List of ProphecyWarning objects.

    Returns:
        Formatted multi-line string.
    """
    if not warnings:
        return "No warnings detected."

    table = Table(title="Morpheus Prophecy warnings", show_header=True)
    table.add_column("Severity", style="bold red")
    table.add_column("Function", style="cyan")
    table.add_column("Line", style="magenta")
    table.add_column("Message", style="yellow")
    table.add_column("Suggestion", style="green")

    for w in warnings:
        severity_color = "red"
        if w.severity == "CRITICAL":
            severity_color = "bold red"
        elif w.severity == "HIGH":
            severity_color = "orange3"
        elif w.severity == "MEDIUM":
            severity_color = "yellow"
        elif w.severity == "LOW":
            severity_color = "blue"

        table.add_row(
            f"[{severity_color}]{w.severity}[/{severity_color}]",
            w.function_name,
            str(w.line_number),
            w.message,
            w.suggestion,
        )

    # Render Rich table to string
    console = Console(width=100, record=True)
    with console.capture() as capture:
        console.print(table)

    return capture.get()
