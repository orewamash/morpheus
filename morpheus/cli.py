"""
morpheus/cli.py — Typer CLI entry point for Morpheus.

Orchestrates the entire execution flow:
1. Validates the file path.
2. Traces execution.
3. Compresses the raw trace events into chapters.
4. Narrates chapters (or runs an interactive teaching session/oracle trace).
5. Saves results to the database history.
6. Prints a summary.

Dependency rules: May import from tracer, compressor, narrator, storage,
prophecy, spy, teacher, oracle, config.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule

from morpheus import __version__
from morpheus.compressor import compress_trace, ExecutionChapter as EC
from morpheus.config import MorpheusConfig, format_config, load_config, save_config
from morpheus.differ import compute_diff, format_diff_report, load_run_events
from morpheus.ml.concept_writer import ConceptWriter
from morpheus.ml.degradation import analyze_degradation, format_degradation_report
from morpheus.ml.execution_graph import build_graph_from_chapters, extract_graph_features
from morpheus.ml.profiler import ExecutionProfiler
from morpheus.narrator import OllamaClient, stream_narration
from morpheus.oracle import oracle_trace
from morpheus.prophecy import analyze_for_prophecy, format_prophecy_report
from morpheus.spy import scan_file, format_spy_report
from morpheus.storage import MorpheusStorage, RunRecord
from morpheus.teacher import run_teaching_session
from morpheus.tracer import trace_file

# ---------------------------------------------------------------------------
#  App setup
# ---------------------------------------------------------------------------

app = typer.Typer(
    name="morpheus",
    help=(
        "A self-evolving execution intelligence system. "
        "Every other tool reads what your code says. "
        "Morpheus remembers what your code did."
    ),
    add_completion=False,
    no_args_is_help=True,
)

# Load config once at module level
_cfg: MorpheusConfig = load_config()
console = Console(highlight=False)


def _should_use_json() -> bool:
    """Check if MORPHEUS_JSON env var is set for programmatic use."""
    return os.getenv("MORPHEUS_JSON", "").lower() in ("1", "true", "yes")


# ---------------------------------------------------------------------------
#  Helpers
# ---------------------------------------------------------------------------


def _validate_file(file: str) -> Path:
    resolved = Path(file).resolve()
    if not resolved.exists():
        console.print(f"[bold red]Error: File not found: {file}[/bold red]")
        raise typer.Exit(code=1)
    return resolved


def _print_json(data: dict[str, Any]) -> None:
    """Print data as JSON and exit."""
    console.print(json.dumps(data, indent=2, default=str))
    raise typer.Exit(code=0)


def _version_callback(show_version: bool) -> None:
    if show_version:
        console.print(f"morpheus v{__version__}")
        raise typer.Exit(code=0)


# ---------------------------------------------------------------------------
#  run  —  Trace and narrate
# ---------------------------------------------------------------------------


@app.command()
def run(
    file: str = typer.Argument(
        ..., help="Path to the Python file to trace and narrate."
    ),
    mode: str = typer.Option(
        "narrator",
        "--mode",
        "-m",
        help="Narration mode: narrator, prophecy, teach, oracle",
        case_sensitive=False,
    ),
    personality: str = typer.Option(
        "mentor",
        "--personality",
        "-p",
        help="Oracle personality: mentor, critic, paranoid, teacher",
        case_sensitive=False,
    ),
    backend: str = typer.Option(
        "",
        "--backend",
        "-b",
        help="LLM backend: ollama, openrouter, auto",
        case_sensitive=False,
    ),
    model: str = typer.Option(
        "",
        "--model",
        help="LLM model name override (e.g. gpt-4, claude-3, mistral)",
    ),
    no_store: bool = typer.Option(
        False,
        "--no-store",
        "-n",
        help="Dry run — do not save to database",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output results as JSON (for programmatic use)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed execution information",
    ),
    timeout: float = typer.Option(
        _cfg.llm_timeout,
        "--timeout",
        "-t",
        help="LLM request timeout in seconds",
    ),
) -> None:
    """
    Trace a Python file and narrate its execution in plain English.

    Modes: narrator, prophecy, teach, oracle
    Backends: ollama, openrouter, auto
    """
    _mode_validate(mode)
    _personality_validate(personality)

    resolved_path = _validate_file(file)
    mode_lower = mode.lower()
    personality_lower = personality.lower()

    client = OllamaClient(model=model, backend=backend)

    result: dict[str, Any] = {
        "file": str(resolved_path),
        "mode": mode_lower,
        "backend": client.provider_name or "auto",
        "model": client.model,
    }

    if not json_output and not _should_use_json():
        console.print(
            Panel.fit(
                f"[bold purple]Morpheus Execution Intelligence[/bold purple]\n"
                f"[bold cyan]Target File:[/bold cyan] {resolved_path}\n"
                f"[bold cyan]Mode:[/bold cyan] {mode_lower} | "
                f"[bold cyan]Personality:[/bold cyan] {personality_lower}\n"
                f"[bold cyan]Backend:[/bold cyan] {client.provider_name or 'auto'} | "
                f"[bold cyan]Model:[/bold cyan] {client.model}",
                border_style="purple",
            )
        )

    # 1. Tracing
    start_time = time.time()
    events: list[Any] = []
    oracle_result = None
    use_json = json_output or _should_use_json()

    if mode_lower == "oracle":
        status_msg = f"[bold magenta]Oracle tracing {resolved_path.name}...[/bold magenta]"
        with console.status(status_msg, spinner="dots"):
            try:
                oracle_result = oracle_trace(str(resolved_path), personality_lower)
                events = oracle_result.events
            except Exception as e:
                _handle_error(e, use_json, result)
    else:
        status_msg = f"[bold blue]Tracing execution of {resolved_path.name}...[/bold blue]"
        with console.status(status_msg, spinner="dots"):
            try:
                events = trace_file(str(resolved_path))
            except Exception as e:
                _handle_error(e, use_json, result)

    end_time = time.time()
    duration_ms = (end_time - start_time) * 1000

    # 2. Compression
    chapters = compress_trace(events)
    if verbose and not use_json:
        console.print(
            f"[bold green][OK][/bold green] Captured {len(events)} events. "
            f"Compressed into {len(chapters)} chapter(s).\n"
        )

    error_msg = ""
    for event in events:
        if event.function_name.startswith("<exception:"):
            error_msg = str(event.return_value)
            break

    narrations: list[str] = []

    # 3. Narration / Presentation
    if mode_lower == "oracle" and oracle_result is not None:
        if not use_json:
            console.print(Rule("[bold magenta]Oracle Narration[/bold magenta]"))
            console.print(oracle_result.narration)
            console.print()
        narrations.append(oracle_result.narration)

    elif mode_lower == "teach":
        if not use_json:
            console.print(
                Rule("[bold yellow]Interactive Teaching Session[/bold yellow]")
            )
        try:
            score = run_teaching_session(chapters, client, console)
            if not use_json:
                console.print(
                    f"\n[bold green]Session Complete![/bold green] "
                    f"Score: {score['correct']}/{score['total']} "
                    f"({score['percentage']:.1f}%)\n"
                )
            narrations.append(f"Teaching Session score: {score['percentage']:.1f}%")
        except Exception as e:
            _handle_error(e, use_json, result)

    else:
        for chapter in chapters:
            if not use_json:
                console.print(
                    Rule(f"[bold yellow]{chapter.title}[/bold yellow]")
                )
            narration = stream_narration(
                chapter, client, console, mode=mode_lower
            )
            narrations.append(narration)

        if mode_lower == "prophecy" and not use_json:
            warnings = analyze_for_prophecy(events)
            report = format_prophecy_report(warnings)
            console.print(Rule("[bold red]Prophecy Analysis Report[/bold red]"))
            console.print(report)
            console.print()

    # 4. Storage
    run_id = "N/A"
    if not no_store:
        storage = MorpheusStorage()
        chapters_serialized = json.dumps(
            [
                {
                    "title": ch.title,
                    "event_count": ch.event_count,
                    "duration_ms": ch.duration_ms,
                    "function": ch.function_name,
                }
                for ch in chapters
            ]
        )
        narrations_serialized = json.dumps(narrations)

        record = RunRecord(
            run_id="",
            filepath=str(resolved_path),
            timestamp=time.time(),
            mode=mode_lower,
            chapters=chapters_serialized,
            narrations=narrations_serialized,
            duration_ms=round(duration_ms, 2),
            event_count=len(events),
            error=error_msg,
        )
        try:
            run_id = storage.save_run(record)
        except Exception as e:
            if not use_json:
                console.print(
                    f"[bold yellow]Warning: Failed to save run history: "
                    f"{e}[/bold yellow]"
                )

    # 5. Output
    if use_json:
        result.update(
            {
                "status": "error" if error_msg else "success",
                "events": len(events),
                "chapters": len(chapters),
                "duration_ms": round(duration_ms, 2),
                "run_id": run_id,
                "error": error_msg,
                "narrations": narrations,
            }
        )
        _print_json(result)

    status_str = (
        "[bold red]CRASHED[/bold red]"
        if error_msg
        else "[bold green]SUCCESS[/bold green]"
    )
    summary_panel = Panel(
        f"[bold cyan]Status:[/bold cyan] {status_str}\n"
        f"[bold cyan]Total Events:[/bold cyan] {len(events)}\n"
        f"[bold cyan]Duration:[/bold cyan] {duration_ms:.2f} ms\n"
        f"[bold cyan]Run ID Saved:[/bold cyan] {run_id}",
        title="[bold purple]Execution Summary[/bold purple]",
        expand=False,
    )
    console.print(summary_panel)

    if error_msg:
        console.print(
            f"\n[bold red]Execution crashed with error:[/bold red] {error_msg}"
        )
        raise typer.Exit(code=1)


def _mode_validate(mode: str) -> None:
    valid = ("narrator", "prophecy", "teach", "oracle")
    if mode.lower() not in valid:
        console.print(
            f"[bold red]Error: Invalid mode: {mode}. "
            f"Supported modes: {', '.join(valid)}[/bold red]"
        )
        raise typer.Exit(code=1)


def _personality_validate(personality: str) -> None:
    valid = ("mentor", "critic", "paranoid", "teacher")
    if personality.lower() not in valid:
        console.print(
            f"[bold red]Error: Invalid personality: {personality}. "
            f"Supported personalities: {', '.join(valid)}[/bold red]"
        )
        raise typer.Exit(code=1)


def _handle_error(
    e: Exception, json_output: bool, result: dict[str, Any]
) -> None:
    if json_output:
        result["error"] = str(e)
        result["status"] = "error"
        _print_json(result)
    console.print(f"[bold red]Error: {e}[/bold red]")
    raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
#  spy  —  Security scan
# ---------------------------------------------------------------------------


@app.command()
def spy(
    file: str = typer.Argument(
        ..., help="Path to the Python script to security scan."
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output results as JSON"
    ),
    output: str = typer.Option(
        "", "--output", "-o", help="Save report to file path"
    ),
) -> None:
    """
    Security scan an unknown Python script.

    Reports all sensitive actions: file access, network calls, system
    directory reads.
    """
    resolved_path = _validate_file(file)
    use_json = json_output or _should_use_json()

    if not use_json:
        console.print(
            Panel.fit(
                f"[bold purple]Morpheus Spy Mode[/bold purple]\n"
                f"[bold cyan]Scanning File:[/bold cyan] {resolved_path}",
                border_style="yellow",
            )
        )

    with console.status(
        "[bold yellow]Scanning script behavior...[/bold yellow]",
        spinner="bouncingBar",
    ):
        events = scan_file(str(resolved_path))
        report = format_spy_report(events, str(resolved_path))

    if output:
        try:
            Path(output).write_text(report, encoding="utf-8")
            console.print(f"[bold green]Report saved to: {output}[/bold green]")
        except OSError as e:
            console.print(f"[bold red]Failed to save report: {e}[/bold red]")

    if use_json:
        _print_json(
            {
                "file": str(resolved_path),
                "events": len(events),
                "report": report,
            }
        )

    console.print(report)


# ---------------------------------------------------------------------------
#  map  —  Execution mind map
# ---------------------------------------------------------------------------


@app.command()
def map(
    file: str = typer.Argument(
        ..., help="Path to the Python file to visualize."
    ),
    port: int = typer.Option(
        _cfg.dashboard_port,
        "--port",
        help="Dashboard server port",
    ),
    no_open: bool = typer.Option(
        False,
        "--no-open",
        help="Do not auto-open browser",
    ),
    browser: bool = typer.Option(
        False,
        "--browser",
        help="Open the dashboard in the browser (deprecated, use --no-open to disable)",
    ),
) -> None:
    """
    Build a visual execution mind map of a Python file.

    Opens the Morpheus dashboard with the execution graph.
    """
    import subprocess
    import webbrowser

    import httpx

    resolved_path = _validate_file(file)

    console.print(
        Panel.fit(
            f"[bold purple]Morpheus Execution Map[/bold purple]\n"
            f"[bold cyan]Target File:[/bold cyan] {resolved_path}\n"
            f"[bold cyan]Dashboard Port:[/bold cyan] {port}",
            border_style="purple",
        )
    )

    # 1. Tracing
    start_time = time.time()
    with console.status(
        f"[bold blue]Tracing execution of {resolved_path.name}...[/bold blue]",
        spinner="dots",
    ):
        try:
            events = trace_file(str(resolved_path))
        except Exception as e:
            console.print(f"[bold red]Tracer error: {e}[/bold red]")
            raise typer.Exit(code=1)

    end_time = time.time()
    duration_ms = (end_time - start_time) * 1000
    chapters = compress_trace(events)

    console.print(
        f"[bold green][OK][/bold green] Captured {len(events)} events. "
        f"Compressed into {len(chapters)} chapter(s).\n"
    )

    error_msg = ""
    for event in events:
        if event.function_name.startswith("<exception:"):
            error_msg = str(event.return_value)
            break

    # 2. Storage
    storage = MorpheusStorage()
    chapters_serialized = json.dumps(
        [
            {
                "title": ch.title,
                "event_count": ch.event_count,
                "duration_ms": ch.duration_ms,
                "function": ch.function_name,
            }
            for ch in chapters
        ]
    )
    record = RunRecord(
        run_id="",
        filepath=str(resolved_path),
        timestamp=time.time(),
        mode="map",
        chapters=chapters_serialized,
        narrations=json.dumps([]),
        duration_ms=round(duration_ms, 2),
        event_count=len(events),
        error=error_msg,
    )
    try:
        run_id = storage.save_run(record)
    except Exception as e:
        console.print(
            f"[bold yellow]Warning: Failed to save run history: {e}[/bold yellow]"
        )
        run_id = "N/A"

    # 3. Check & Start server
    server_url = f"http://127.0.0.1:{port}"

    def is_server_running() -> bool:
        try:
            response = httpx.get(f"{server_url}/api/health", timeout=0.5)
            return response.status_code == 200
        except Exception:
            return False

    if not is_server_running():
        console.print("[yellow]FastAPI server is not running. Starting it...[/yellow]")
        package_root = Path(__file__).resolve().parent.parent
        api_server_path = package_root / "api" / "server.py"

        env = os.environ.copy()
        env["PYTHONPATH"] = (
            str(package_root) + os.pathsep + env.get("PYTHONPATH", "")
        )

        kwargs: dict[str, Any] = {}
        if sys.platform == "win32":
            kwargs["creationflags"] = 0x00000008
        else:
            kwargs["close_fds"] = True

        try:
            subprocess.Popen(
                [sys.executable, str(api_server_path)],
                cwd=str(package_root),
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                **kwargs,
            )
            for _ in range(10):
                time.sleep(0.5)
                if is_server_running():
                    console.print(
                        "[bold green]FastAPI server started on port "
                        f"{port}.[/bold green]"
                    )
                    break
            else:
                console.print(
                    "[bold red]Warning: FastAPI server is taking longer "
                    "than expected to start.[/bold red]"
                )
        except Exception as e:
            console.print(
                f"[bold red]Failed to start FastAPI server: {e}[/bold red]"
            )
    else:
        console.print(
            f"[bold green]FastAPI server is already running on port "
            f"{port}.[/bold green]"
        )

    # 4. Output
    target_url = f"{server_url}/?run_id={run_id}"
    console.print(
        Panel(
            f"[bold green]Execution Graph mapped successfully![/bold green]\n"
            f"[bold cyan]Run ID:[/bold cyan] {run_id}\n"
            f"[bold cyan]Dashboard URL:[/bold cyan] [underline]{target_url}[/underline]\n\n"
            "Keep this terminal open to keep the backend server running.",
            title="[bold purple]Morpheus Execution Map[/bold purple]",
            expand=False,
        )
    )

    if not no_open and browser and run_id != "N/A":
        console.print(f"[cyan]Opening browser to: {target_url}[/cyan]")
        webbrowser.open(target_url)


# ---------------------------------------------------------------------------
#  diff  —  Time Travel Diff
# ---------------------------------------------------------------------------


@app.command()
def diff(
    log1: str = typer.Argument(
        ..., help="Path or run ID of the first run log."
    ),
    log2: str = typer.Argument(
        ..., help="Path or run ID of the second run log."
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output results as JSON"
    ),
) -> None:
    """
    Compare two Morpheus runs and show where execution diverged.
    """
    resolved_path1 = Path(log1).resolve() if Path(log1).exists() else log1
    resolved_path2 = Path(log2).resolve() if Path(log2).exists() else log2
    use_json = json_output or _should_use_json()

    if not use_json:
        console.print(
            Panel.fit(
                f"[bold purple]Morpheus Time Travel Diff[/bold purple]\n"
                f"[bold cyan]Comparing:[/bold cyan] {log1} vs {log2}",
                border_style="purple",
            )
        )

    try:
        with console.status("[bold blue]Loading runs...[/bold blue]", spinner="dots"):
            events1 = load_run_events(
                str(resolved_path1)
                if isinstance(resolved_path1, Path)
                else log1
            )
            events2 = load_run_events(
                str(resolved_path2)
                if isinstance(resolved_path2, Path)
                else log2
            )
    except Exception as e:
        console.print(f"[bold red]Error loading runs: {e}[/bold red]")
        raise typer.Exit(code=1)

    with console.status("[bold blue]Computing diff...[/bold blue]", spinner="dots"):
        segments = compute_diff(events1, events2)
        report = format_diff_report(segments, str(log1), str(log2))

    if use_json:
        _print_json(
            {
                "log1": log1,
                "log2": log2,
                "segments": [
                    {
                        "chapter_id": s.chapter_id,
                        "status": s.status,
                        "title": s.title,
                    }
                    for s in segments
                ],
                "total": len(segments),
            }
        )

    console.print(report)

    if not segments:
        console.print("[bold yellow]No chapter data to compare.[/bold yellow]")
        return

    same = sum(1 for s in segments if s.status == "SAME")
    changed = sum(1 for s in segments if s.status == "CHANGED")
    added = sum(1 for s in segments if s.status == "ADDED")
    removed = sum(1 for s in segments if s.status == "REMOVED")
    console.print(
        f"\n[bold]Summary:[/bold] [green]{same} same[/green], "
        f"[yellow]{changed} changed[/yellow], "
        f"[blue]{added} added[/blue], "
        f"[red]{removed} removed[/red]"
    )


# ---------------------------------------------------------------------------
#  analyze  —  ML analysis pipeline
# ---------------------------------------------------------------------------


@app.command()
def analyze(
    run_id: str = typer.Argument(
        ..., help="Run ID to analyze (from a previous `morpheus run`)."
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output results as JSON"
    ),
) -> None:
    """
    Run the full ML analysis pipeline on a previously saved run.

    Reports execution graph features, behavioral concept classification,
    performance degradation, and function profiling.
    """
    storage = MorpheusStorage()
    use_json = json_output or _should_use_json()

    try:
        record = storage.get_run(run_id)
    except KeyError:
        console.print(
            f"[bold red]Error: No run found with ID: {run_id}[/bold red]"
        )
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[bold red]Error loading run: {e}[/bold red]")
        raise typer.Exit(code=1)

    if not use_json:
        console.print(
            Panel.fit(
                f"[bold purple]Morpheus ML Analysis[/bold purple]\n"
                f"[bold cyan]Run ID:[/bold cyan] {run_id}\n"
                f"[bold cyan]File:[/bold cyan] {record.filepath}\n"
                f"[bold cyan]Mode:[/bold cyan] {record.mode}",
                border_style="purple",
            )
        )

    # Parse chapters
    try:
        chapters_data = json.loads(record.chapters)
    except (json.JSONDecodeError, TypeError):
        chapters_data = []

    chapters: list[EC] = []
    for cd in chapters_data:
        chapters.append(
            EC(
                chapter_id=chapters_data.index(cd) + 1,
                title=cd.get("title", "Unknown"),
                events=[],
                summary_hint="",
                duration_ms=cd.get("duration_ms", 0.0),
                function_name=cd.get("function", "").replace(
                    "Chapter: ", ""
                ).replace("()", ""),
                event_count=cd.get("event_count", 0),
            )
        )

    with console.status(
        "[bold blue]Running ML analysis...[/bold blue]", spinner="dots"
    ):
        cw = ConceptWriter()
        concept_result = cw.infer_concept(chapters)

        G = build_graph_from_chapters(chapters)
        graph_features = extract_graph_features(G)

        all_runs = storage.list_runs(limit=50)
        hist_durations = [
            r.duration_ms
            for r in all_runs
            if r.duration_ms > 0 and r.run_id != run_id
        ]
        hist_event_counts = [
            [r.event_count]
            for r in all_runs
            if r.event_count > 0 and r.run_id != run_id
        ]
        degradation = analyze_degradation(
            run_id=run_id,
            current_duration_ms=record.duration_ms,
            current_event_count=record.event_count,
            history_durations=hist_durations,
            history_event_counts=hist_event_counts,
        )

        profiler = ExecutionProfiler()
        if chapters:
            profiler.add_run(chapters)
        profile = profiler.get_profile()

    if use_json:
        _print_json(
            {
                "run_id": run_id,
                "concept": concept_result["concept"],
                "graph_features": graph_features,
                "degradation": {
                    "severity": degradation.severity,
                    "duration_zscore": round(degradation.duration_zscore, 2),
                    "event_zscore": round(degradation.event_zscore, 2),
                    "duration_trend_slope": round(
                        degradation.duration_trend_slope, 2
                    ),
                    "details": degradation.details,
                },
                "functions": [
                    {"name": n, **d}
                    for n, d in profile.get("functions", {}).items()
                ],
            }
        )

    console.print(Rule("[bold green]Concept Classification[/bold green]"))
    console.print(
        f"[bold cyan]Concept:[/bold cyan] {concept_result['concept']}\n"
        f"[bold]Description:[/bold] "
        f"{concept_result.get('description', '')}\n"
        f"[bold cyan]Functions ({len(concept_result.get('functions', []))}):"
        f"[/bold cyan] "
        f"{', '.join(concept_result.get('functions', [])[:8])}"
    )

    console.print(Rule("[bold green]Execution Graph Features[/bold green]"))
    console.print(
        Panel(
            f"[bold cyan]Nodes:[/bold cyan] "
            f"{graph_features['num_nodes']:.0f}\n"
            f"[bold cyan]Edges:[/bold cyan] "
            f"{graph_features['num_edges']:.0f}\n"
            f"[bold cyan]Density:[/bold cyan] "
            f"{graph_features['density']:.3f}\n"
            f"[bold cyan]Max Depth:[/bold cyan] "
            f"{graph_features['max_depth']:.0f}\n"
            f"[bold cyan]Roots:[/bold cyan] "
            f"{graph_features['num_roots']:.0f} | "
            f"[bold cyan]Leaves:[/bold cyan] "
            f"{graph_features['num_leaves']:.0f}\n"
            f"[bold cyan]Avg Call Count:[/bold cyan] "
            f"{graph_features['avg_call_count']:.1f}\n"
            f"[bold cyan]Total Time:[/bold cyan] "
            f"{graph_features['total_time_ms']:.1f} ms\n"
            f"[bold cyan]Connected Components:[/bold cyan] "
            f"{graph_features['num_connected_components']:.0f}",
            title="[bold]Graph Metrics[/bold]",
            expand=False,
        )
    )

    console.print(Rule("[bold green]Performance Degradation[/bold green]"))
    console.print(format_degradation_report(degradation))

    console.print(Rule("[bold green]Function Profile[/bold green]"))
    funcs = profile.get("functions", {})
    if funcs:
        for fname, fdata in list(funcs.items())[:10]:
            console.print(
                f"  [bold]{fname}:[/bold] "
                f"{fdata['runs']} run(s), "
                f"avg {fdata['avg_duration_ms']:.1f}ms, "
                f"max {fdata['max_duration_ms']:.1f}ms"
            )
        if len(funcs) > 10:
            console.print(
                f"  ... and {len(funcs) - 10} more functions"
            )
    else:
        console.print(
            "  [yellow]No profile data available[/yellow]"
        )
    console.print()


# ---------------------------------------------------------------------------
#  list  —  List recent runs
# ---------------------------------------------------------------------------


@app.command()
def list_runs(
    limit: int = typer.Option(
        20, "--limit", "-l", help="Maximum number of runs to show"
    ),
    mode: str = typer.Option(
        "",
        "--mode",
        "-m",
        help="Filter by mode (narrator, prophecy, spy, map, oracle)",
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output results as JSON"
    ),
) -> None:
    """
    List recent execution runs from the database.
    """
    storage = MorpheusStorage()
    use_json = json_output or _should_use_json()

    try:
        runs = storage.list_runs(limit=limit)
    except Exception as e:
        console.print(f"[bold red]Error reading database: {e}[/bold red]")
        raise typer.Exit(code=1)

    if mode:
        runs = [r for r in runs if r.mode == mode.lower()]

    if use_json:
        _print_json(
            {
                "total": len(runs),
                "runs": [
                    {
                        "run_id": r.run_id,
                        "file": r.filepath,
                        "mode": r.mode,
                        "events": r.event_count,
                        "duration_ms": r.duration_ms,
                        "timestamp": r.timestamp,
                        "error": bool(r.error),
                    }
                    for r in runs
                ],
            }
        )

    if not runs:
        console.print("[yellow]No runs found in database.[/yellow]")
        return

    console.print(
        Panel.fit(
            f"[bold purple]Recent Runs ({len(runs)})[/bold purple]",
            border_style="purple",
        )
    )
    for r in runs:
        status = "[red]ERROR[/red]" if r.error else "[green]OK[/green]"
        console.print(
            f"  [bold cyan]{r.run_id[:12]}...[/bold cyan] "
            f"{r.mode:12s} "
            f"{Path(r.filepath).name:25s} "
            f"{r.event_count:4d} events "
            f"{r.duration_ms:8.1f}ms "
            f"{status}"
        )


# ---------------------------------------------------------------------------
#  get  —  Get run details
# ---------------------------------------------------------------------------


@app.command()
def get(
    run_id: str = typer.Argument(..., help="Run ID to retrieve."),
) -> None:
    """
    Get full details of a specific run.
    """
    storage = MorpheusStorage()

    try:
        record = storage.get_run(run_id)
    except KeyError:
        console.print(
            f"[bold red]Error: No run found with ID: {run_id}[/bold red]"
        )
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise typer.Exit(code=1)

    console.print(
        Panel(
            f"[bold cyan]Run ID:[/bold cyan] {record.run_id}\n"
            f"[bold cyan]File:[/bold cyan] {record.filepath}\n"
            f"[bold cyan]Mode:[/bold cyan] {record.mode}\n"
            f"[bold cyan]Timestamp:[/bold cyan] "
            f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(record.timestamp))}\n"
            f"[bold cyan]Events:[/bold cyan] {record.event_count}\n"
            f"[bold cyan]Duration:[/bold cyan] {record.duration_ms:.1f} ms\n"
            f"[bold cyan]Error:[/bold cyan] "
            f"{'[red]' + record.error + '[/red]' if record.error else '[green]None[/green]'}\n",
            title="[bold purple]Run Details[/bold purple]",
            expand=False,
        )
    )


# ---------------------------------------------------------------------------
#  delete  —  Delete a run
# ---------------------------------------------------------------------------


@app.command()
def delete(
    run_id: str = typer.Argument(..., help="Run ID to delete."),
    force: bool = typer.Option(
        False, "--force", "-f", help="Skip confirmation."
    ),
) -> None:
    """
    Delete a run record from the database.
    """
    storage = MorpheusStorage()

    if not force:
        console.print(
            f"[yellow]Are you sure you want to delete run {run_id}? "
            f"Use --force to confirm.[/yellow]"
        )
        raise typer.Exit(code=1)

    try:
        deleted = storage.delete_run(run_id)
    except Exception as e:
        console.print(f"[bold red]Error deleting run: {e}[/bold red]")
        raise typer.Exit(code=1)

    if deleted:
        console.print(f"[bold green]Run {run_id} deleted.[/bold green]")
    else:
        console.print(
            f"[bold yellow]No run found with ID: {run_id}[/bold yellow]"
        )


# ---------------------------------------------------------------------------
#  version  —  Show version
# ---------------------------------------------------------------------------


@app.command()
def version() -> None:
    """
    Show the installed Morpheus version.
    """
    from morpheus import __version__ as ver

    console.print(f"[bold purple]morpheus[/bold purple] v{ver}")
    console.print("A self-evolving execution intelligence system.")
    console.print(f"Python: {sys.version}")


# ---------------------------------------------------------------------------
#  config  —  Show or set configuration
# ---------------------------------------------------------------------------


@app.command()
def config(
    show: bool = typer.Option(
        False, "--show", "-s", help="Display current configuration."
    ),
    set_key: str = typer.Option(
        "",
        "--set",
        metavar="KEY=VALUE",
        help="Set a configuration value (e.g. ollama_model=llama3)",
    ),
) -> None:
    """
    View or modify Morpheus configuration.

    Configuration is read from environment variables, config file
    (~/.morpheus/config.json), and defaults.

    Example:
        morpheus config --show
        morpheus config --set ollama_model=llama3
        morpheus config --set llm_backend=openrouter
    """
    cfg = load_config()

    if set_key:
        if "=" not in set_key:
            console.print(
                "[bold red]Error: --set must be in KEY=VALUE format[/bold red]"
            )
            raise typer.Exit(code=1)
        key, val = set_key.split("=", 1)
        if hasattr(cfg, key):
            current = getattr(cfg, key)
            if isinstance(current, bool):
                setattr(cfg, key, val.lower() in ("1", "true", "yes"))
            elif isinstance(current, int):
                try:
                    setattr(cfg, key, int(val))
                except (ValueError, TypeError):
                    console.print(
                        f"[bold red]Error: {key} expects an integer[/bold red]"
                    )
                    raise typer.Exit(code=1)
            elif isinstance(current, float):
                try:
                    setattr(cfg, key, float(val))
                except (ValueError, TypeError):
                    console.print(
                        f"[bold red]Error: {key} expects a number[/bold red]"
                    )
                    raise typer.Exit(code=1)
            else:
                setattr(cfg, key, val)
            save_config(cfg)
            console.print(f"[bold green]Set {key}={val}[/bold green]")
        else:
            console.print(
                f"[bold red]Error: Unknown config key: {key}[/bold red]"
            )
            raise typer.Exit(code=1)

    if show:
        console.print(format_config(cfg))


# ---------------------------------------------------------------------------
#  Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app()
