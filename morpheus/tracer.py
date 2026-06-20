"""
morpheus/tracer.py — sys.settrace execution engine.

Watches a Python file execute using sys.settrace. Captures every meaningful
event into a list of TraceEvent objects. This is the core of Morpheus.

Dependency rules: This module imports nothing from inside morpheus.
"""

from __future__ import annotations

import os
import runpy
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class TraceEvent:
    """A single captured event from sys.settrace."""

    event_type: str  # "call" or "return" — never "line"
    function_name: str  # Name of the function being called/returned
    filename: str  # Absolute path to the source file
    line_number: int  # Line number where event occurred
    local_vars: dict[str, Any]  # Snapshot of local variables at this moment
    timestamp: float  # time.time() at capture — used for duration math
    return_value: Any = None  # Only populated for "return" events


class MorpheusTracer:
    """
    Wraps sys.settrace to capture execution events from a target Python file.

    Usage:
        tracer = MorpheusTracer(target_file="/path/to/script.py")
        tracer.start()
        # ... run code here ...
        tracer.stop()
        events = tracer.get_events()
    """

    def __init__(self, target_file: str) -> None:
        """
        Args:
            target_file: Absolute path to the Python file being traced.
                         Only events from this file will be captured.
        """
        self._target_file: str = os.path.abspath(target_file)
        self._events: list[TraceEvent] = []
        self._tracing: bool = False

    def start(self) -> None:
        """
        Install the trace handler with sys.settrace.
        Must be called before executing the target file.
        """
        self._tracing = True
        sys.settrace(self._trace_handler)

    def stop(self) -> None:
        """
        Remove the trace handler with sys.settrace(None).
        Always call this — even if an exception occurs during tracing.
        """
        sys.settrace(None)
        self._tracing = False

    def get_events(self) -> list[TraceEvent]:
        """
        Return all captured TraceEvent objects in chronological order.

        Returns:
            List of TraceEvent objects. Empty list if nothing was captured.
        """
        return list(self._events)

    def _trace_handler(self, frame: Any, event: str, arg: Any) -> Any:
        """
        The sys.settrace callback. Called by Python for every execution event.

        Args:
            frame: Python frame object — contains locals, filename, line number
            event: "call", "return", or "line" — only process call and return
            arg: Return value for "return" events, None otherwise

        Returns:
            self._trace_handler to continue tracing inside the called function,
            or None to stop tracing inside that function.
        """
        if not self._tracing:
            return None

        # Only process "call" and "return" events — skip "line" events
        if event not in ("call", "return"):
            return self._trace_handler

        # Skip module-level execution events to allow correct function-level grouping
        if frame.f_code.co_name == "<module>":
            return self._trace_handler

        filename = frame.f_code.co_filename

        # Normalize for comparison
        try:
            filename = os.path.abspath(filename)
        except (ValueError, OSError):
            return self._trace_handler

        # Filter: only capture events from the target file
        if not self._should_trace(filename):
            return self._trace_handler

        # Safely snapshot local variables
        try:
            local_vars = self._safe_copy_locals(frame.f_locals)
        except Exception:
            local_vars = {}

        trace_event = TraceEvent(
            event_type=event,
            function_name=frame.f_code.co_name,
            filename=filename,
            line_number=frame.f_lineno,
            local_vars=local_vars,
            timestamp=time.time(),
            return_value=arg if event == "return" else None,
        )

        self._events.append(trace_event)
        return self._trace_handler

    def _should_trace(self, filename: str) -> bool:
        """
        Determine if an event from this filename should be captured.

        Filters out:
        - Python stdlib (paths containing 'lib/python' or 'lib\\python')
        - Third-party packages (paths containing 'site-packages')
        - The tracer itself (morpheus/tracer.py)
        - Any <string>, <frozen>, or similar synthetic filenames
        """
        # Skip synthetic filenames
        if filename.startswith("<") or filename.endswith(">"):
            return False

        # Normalize path separators for cross-platform comparison
        normalized = filename.replace("\\", "/").lower()

        # Skip stdlib
        if "lib/python" in normalized:
            return False

        # Skip third-party packages
        if "site-packages" in normalized:
            return False

        # Skip the tracer itself
        if "morpheus/tracer.py" in normalized or "morpheus\\tracer.py" in normalized:
            return False

        # Only capture events from the target file
        target_normalized = self._target_file.replace("\\", "/").lower()
        return normalized == target_normalized

    @staticmethod
    def _safe_copy_locals(local_vars: dict[str, Any]) -> dict[str, Any]:
        """
        Create a safe copy of frame local variables.

        Converts values to their repr strings for anything that cannot be
        trivially serialized. Never stores frame objects directly.
        """
        result: dict[str, Any] = {}
        for key, value in local_vars.items():
            try:
                # Store simple types directly
                if isinstance(value, (int, float, str, bool, type(None))):
                    result[key] = value
                elif isinstance(value, (list, tuple)):
                    if len(value) > 100:
                        result[key] = (
                            f"<{type(value).__name__} with {len(value)} items>"
                        )
                    else:
                        result[key] = repr(value)
                elif isinstance(value, dict):
                    if len(value) > 50:
                        result[key] = f"<dict with {len(value)} keys>"
                    else:
                        result[key] = repr(value)
                else:
                    result[key] = f"<{type(value).__name__}>"
            except Exception:
                result[key] = "<unrepresentable>"
        return result


def trace_file(filepath: str) -> list[TraceEvent]:
    """
    Execute a Python file under the Morpheus tracer and return all captured events.

    This is the main entry point for the tracer module.
    Called by cli.py when `morpheus run <file>` is invoked.

    Args:
        filepath: Path to the Python file to trace. Can be relative or absolute.

    Returns:
        List of TraceEvent objects in execution order.
        Returns empty list if the script produces no traceable events.

    Raises:
        FileNotFoundError: If filepath does not point to an existing file.
        SyntaxError: If the target file has Python syntax errors.

    Example:
        events = trace_file("examples/simple.py")
        print(f"Captured {len(events)} events")
    """
    resolved = Path(filepath).resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"File not found: {resolved}")

    target_file = str(resolved)
    tracer = MorpheusTracer(target_file=target_file)

    tracer.start()
    try:
        # Use runpy.run_path to execute the file in its own namespace
        runpy.run_path(target_file, run_name="__main__")
    except SystemExit:
        # Allow scripts that call sys.exit() — not a tracing failure
        pass
    except Exception as exc:
        # Capture the exception as a final TraceEvent
        tracer._events.append(
            TraceEvent(
                event_type="return",
                function_name=f"<exception: {type(exc).__name__}>",
                filename=target_file,
                line_number=0,
                local_vars={"error": str(exc)},
                timestamp=time.time(),
                return_value=str(exc),
            )
        )
    finally:
        tracer.stop()

    return tracer.get_events()
