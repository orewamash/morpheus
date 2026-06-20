from __future__ import annotations

from morpheus.spy import SpyEvent, format_spy_report


def test_format_spy_report_safe():
    events: list[SpyEvent] = []
    report = format_spy_report(events, "/path/to/script.py")
    assert "SAFE" in report
    assert "No sensitive actions detected" in report


def test_format_spy_report_malware():
    events = [
        SpyEvent(
            risk_level="DANGER",
            action="opens socket",
            target="192.168.1.1:443",
            function_name="connect_server",
            line_number=10,
        ),
        SpyEvent(
            risk_level="DANGER",
            action="reads sensitive file",
            target="/home/user/.env",
            function_name="load_config",
            line_number=5,
        ),
    ]
    report = format_spy_report(events, "/path/to/malware.py")
    assert "MALWARE" in report
    assert "DANGER" in report


def test_format_spy_report_suspicious():
    events = [
        SpyEvent(
            risk_level="HIGH",
            action="reads file outside CWD",
            target="/etc/passwd",
            function_name="read_file",
            line_number=8,
        ),
    ]
    report = format_spy_report(events, "/path/to/script.py")
    assert "SUSPICIOUS" in report


def test_spy_event_dataclass():
    ev = SpyEvent(
        risk_level="LOW",
        action="accesses env",
        target="HOME",
        function_name="main",
        line_number=3,
    )
    assert ev.risk_level == "LOW"
    assert ev.action == "accesses env"
    assert ev.target == "HOME"
