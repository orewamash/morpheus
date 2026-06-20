"""
morpheus/spy.py — Security scanner engine.

Scans python scripts for sensitive actions (file access, network calls).
Uses dynamic monkeypatching to intercept sensitive operations at runtime.
"""

from __future__ import annotations

import builtins
import inspect
import os
import runpy
import socket
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SpyEvent:
    """A single sensitive action detected during spy mode tracing."""

    risk_level: str  # "LOW", "HIGH", "DANGER"
    action: str  # What happened: "reads file", "opens socket", "accesses env"
    target: str  # What it targeted: file path, IP address, env variable name
    function_name: str  # Which function triggered this action
    line_number: int  # Line number where it occurred


# Global list to accumulate intercepted events during tracing
_captured_spy_events: list[SpyEvent] = []
_traced_file_path: str = ""


def _get_caller_info() -> tuple[str, int]:
    """Inspect stack to trace the call back to the scanned file."""
    stack = inspect.stack()
    for frame_info in stack:
        filename = frame_info.filename
        if filename:
            try:
                resolved_file = Path(filename).resolve()
                target_file = Path(_traced_file_path).resolve()
                if resolved_file == target_file:
                    return frame_info.function, frame_info.lineno
            except Exception:
                pass
    return "<unknown>", 0


def scan_file(filepath: str) -> list[SpyEvent]:
    """
    Run a Python script under the tracer and analyze every event for sensitive behavior.

    Args:
        filepath: Path to the script to scan.

    Returns:
        List of SpyEvent objects ordered by risk level (DANGER first).
    """
    global _captured_spy_events, _traced_file_path
    _captured_spy_events = []
    resolved_path = Path(filepath).resolve()
    _traced_file_path = str(resolved_path)

    # Save originals
    original_open = builtins.open
    original_socket_connect = socket.socket.connect
    original_socket_connect_ex = socket.socket.connect_ex
    original_system = os.system
    original_popen = subprocess.Popen
    original_getenv = os.getenv
    original_environ_get = os.environ.get
    original_environ_getitem = os.environ.__getitem__

    # Define wraps
    def wrapped_open(file, *args, **kwargs):
        try:
            expanded = os.path.expanduser(str(file))
            abs_path = os.path.abspath(expanded)
        except Exception:
            abs_path = str(file)

        func, line = _get_caller_info()

        # Danger files
        danger_files = (".env", ".ssh", ".aws", "id_rsa", "credentials")
        if any(df in abs_path.lower() for df in danger_files):
            _captured_spy_events.append(
                SpyEvent(
                    risk_level="DANGER",
                    action="reads sensitive file",
                    target=abs_path,
                    function_name=func,
                    line_number=line,
                )
            )
        # System directories
        elif any(
            sys_dir in abs_path.lower()
            for sys_dir in ("/etc/", "windows/system32", "windows/syswow64")
        ):
            _captured_spy_events.append(
                SpyEvent(
                    risk_level="HIGH",
                    action="accesses system directory",
                    target=abs_path,
                    function_name=func,
                    line_number=line,
                )
            )
        # Home directory
        elif abs_path.startswith(os.path.expanduser("~")):
            _captured_spy_events.append(
                SpyEvent(
                    risk_level="HIGH",
                    action="reads from home directory (~)",
                    target=abs_path,
                    function_name=func,
                    line_number=line,
                )
            )
        # Outside CWD
        elif not abs_path.startswith(os.getcwd()):
            _captured_spy_events.append(
                SpyEvent(
                    risk_level="HIGH",
                    action="reads file outside CWD",
                    target=abs_path,
                    function_name=func,
                    line_number=line,
                )
            )

        return original_open(file, *args, **kwargs)

    def wrapped_socket_connect(self, address, *args, **kwargs):
        func, line = _get_caller_info()
        _captured_spy_events.append(
            SpyEvent(
                risk_level="DANGER",
                action="opens socket",
                target=str(address),
                function_name=func,
                line_number=line,
            )
        )
        return original_socket_connect(self, address, *args, **kwargs)

    def wrapped_socket_connect_ex(self, address, *args, **kwargs):
        func, line = _get_caller_info()
        _captured_spy_events.append(
            SpyEvent(
                risk_level="DANGER",
                action="opens socket",
                target=str(address),
                function_name=func,
                line_number=line,
            )
        )
        return original_socket_connect_ex(self, address, *args, **kwargs)

    def wrapped_system(command, *args, **kwargs):
        func, line = _get_caller_info()
        _captured_spy_events.append(
            SpyEvent(
                risk_level="HIGH",
                action="os.system call",
                target=str(command),
                function_name=func,
                line_number=line,
            )
        )
        return original_system(command, *args, **kwargs)

    def wrapped_popen(*args, **kwargs):
        func, line = _get_caller_info()
        cmd_args = args[0] if args else ""
        cmd_str = " ".join(cmd_args) if isinstance(cmd_args, list) else str(cmd_args)
        _captured_spy_events.append(
            SpyEvent(
                risk_level="HIGH",
                action="subprocess call",
                target=cmd_str,
                function_name=func,
                line_number=line,
            )
        )
        return original_popen(*args, **kwargs)

    def wrapped_getenv(key, default=None):
        func, line = _get_caller_info()
        _captured_spy_events.append(
            SpyEvent(
                risk_level="LOW",
                action="accesses env",
                target=str(key),
                function_name=func,
                line_number=line,
            )
        )
        return original_getenv(key, default)

    def wrapped_environ_get(key, default=None):
        func, line = _get_caller_info()
        _captured_spy_events.append(
            SpyEvent(
                risk_level="LOW",
                action="accesses env",
                target=str(key),
                function_name=func,
                line_number=line,
            )
        )
        return original_environ_get(key, default)

    def wrapped_environ_getitem(self, key):
        func, line = _get_caller_info()
        _captured_spy_events.append(
            SpyEvent(
                risk_level="LOW",
                action="accesses env",
                target=str(key),
                function_name=func,
                line_number=line,
            )
        )
        return original_environ_getitem(self, key)

    # Apply patches
    builtins.open = wrapped_open
    socket.socket.connect = wrapped_socket_connect
    socket.socket.connect_ex = wrapped_socket_connect_ex
    os.system = wrapped_system
    subprocess.Popen = wrapped_popen
    os.getenv = wrapped_getenv
    os.environ.get = wrapped_environ_get
    try:
        os.environ.__getitem__ = wrapped_environ_getitem
    except Exception:
        pass

    try:
        # Run the file inside the patched context
        runpy.run_path(str(resolved_path), run_name="__main__")
    except SystemExit:
        pass
    except Exception:
        # We ignore crashes inside the script during security scans
        pass
    finally:
        # Restore original functions
        builtins.open = original_open
        socket.socket.connect = original_socket_connect
        socket.socket.connect_ex = original_socket_connect_ex
        os.system = original_system
        subprocess.Popen = original_popen
        os.getenv = original_getenv
        os.environ.get = original_environ_get
        try:
            os.environ.__getitem__ = original_environ_getitem
        except Exception:
            pass

    # Sort events by risk priority: DANGER first, HIGH second, LOW last
    risk_priority = {"DANGER": 0, "HIGH": 1, "LOW": 2}
    _captured_spy_events.sort(
        key=lambda e: risk_priority.get(e.risk_level, 3)
    )

    return list(_captured_spy_events)


def format_spy_report(events: list[SpyEvent], filepath: str) -> str:
    """
    Format SpyEvents into a human-readable security report.

    Args:
        events: List of SpyEvent objects from scan_file().
        filepath: Path of the scanned file.

    Returns:
        Formatted multi-line string report.
    """
    danger_count = sum(1 for e in events if e.risk_level == "DANGER")
    high_count = sum(1 for e in events if e.risk_level == "HIGH")

    # Verdict logic
    # SAFE = 0 DANGER events, fewer than 3 HIGH events
    # SUSPICIOUS = 1+ HIGH events or 1 DANGER event
    # MALWARE = 2+ DANGER events
    if danger_count >= 2:
        verdict = "MALWARE"
    elif danger_count == 1 or high_count >= 1:
        verdict = "SUSPICIOUS"
    else:
        verdict = "SAFE"

    lines = []
    lines.append(f"Security Scan Report for: {filepath}")
    lines.append("=" * 60)

    if not events:
        lines.append("No sensitive actions detected.")
    else:
        for ev in events:
            lines.append(
                f"[{ev.risk_level}] {ev.action} on '{ev.target}' "
                f"in {ev.function_name}() at line {ev.line_number}"
            )

    lines.append("=" * 60)
    lines.append(f"Verdict: {verdict}")

    return "\n".join(lines)
