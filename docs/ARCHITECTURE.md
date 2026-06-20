# MORPHEUS — ARCHITECTURE.md
### The Complete Code Blueprint
**Author:** Madhesh Y  
**Purpose:** Define every function signature, class design, input/output contract, and module responsibility for every file in the Morpheus codebase.  
**Rule:** Every developer reads this before writing a single line. Every function listed here must be implemented exactly as specified — same name, same parameters, same return type. This ensures every module connects cleanly.

---

## HOW TO USE THIS FILE

1. Find the module you are assigned to build.
2. Read the full section — class names, method signatures, dataclass fields, and notes.
3. Implement exactly what is specified. Do not rename, do not reorder parameters.
4. If something seems wrong or unclear, raise it in GitHub Issues before changing it.

**Why strict signatures matter:** `cli.py` calls `tracer.trace_file()`. `compressor.py` calls `compress_trace()`. If the function name or return type is different, the chain breaks and nothing runs.

---

## MODULE MAP

```
morpheus/
├── __init__.py          ← version string only
├── cli.py               ← entry point — calls everything else
├── tracer.py            ← sys.settrace engine
├── compressor.py        ← TraceEvent[] → ExecutionChapter[]
├── narrator.py          ← ExecutionChapter → Ollama → narration string
├── storage.py           ← SQLite run history
├── prophecy.py          ← crash prediction patterns
├── spy.py               ← security scanner
├── teacher.py           ← interactive teaching mode
├── oracle.py            ← multi-language engine
└── ml/
    ├── __init__.py
    ├── anomaly.py       ← Isolation Forest
    ├── predictor.py     ← XGBoost crash prediction
    ├── profiler.py      ← HDBSCAN user profiler
    ├── concept_writer.py← NLP concept docs
    └── fingerprint.py   ← Codebase DNA
```

**Data flow:**
```
trace_file() → [TraceEvent]
                    ↓
           compress_trace() → [ExecutionChapter]
                                      ↓
                          narrate_chapter() → str (narration)
                                                    ↓
                                        MorpheusStorage.save_run()
```

---

## morpheus/__init__.py

**Purpose:** Package version string. Nothing else goes here.

```python
__version__ = "0.1.0"
```

---

## morpheus/tracer.py

**Purpose:** Watch a Python file execute using `sys.settrace`. Capture every meaningful event into a list of `TraceEvent` objects.

### Dataclass: TraceEvent

```python
from dataclasses import dataclass, field
from typing import Any

@dataclass
class TraceEvent:
    """A single captured event from sys.settrace."""
    event_type: str            # "call" or "return" — never "line"
    function_name: str         # Name of the function being called/returned
    filename: str              # Absolute path to the source file
    line_number: int           # Line number where event occurred
    local_vars: dict[str, Any] # Snapshot of local variables at this moment
    timestamp: float           # time.time() at capture — used for duration math
    return_value: Any = None   # Only populated for "return" events
```

**Notes on local_vars:** Copy local variables using `dict(frame.f_locals)`. Never store the frame object itself — frames cannot be serialized.

**Notes on filtering:** Only capture events where `filename` matches the target file being traced. Discard events from:
- Python stdlib (paths containing `lib/python` or `site-packages`)
- The tracer itself (`morpheus/tracer.py`)
- Any `<string>` or `<frozen>` filenames

---

### Class: MorpheusTracer

```python
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

    def start(self) -> None:
        """
        Install the trace handler with sys.settrace.
        Must be called before executing the target file.
        """

    def stop(self) -> None:
        """
        Remove the trace handler with sys.settrace(None).
        Always call this — even if an exception occurs during tracing.
        """

    def get_events(self) -> list[TraceEvent]:
        """
        Return all captured TraceEvent objects in chronological order.
        
        Returns:
            List of TraceEvent objects. Empty list if nothing was captured.
        """

    def _trace_handler(self, frame, event: str, arg: Any) -> callable:
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
```

---

### Function: trace_file

```python
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
```

**Implementation notes:**
- Convert `filepath` to absolute path with `os.path.abspath()` before tracing
- Use `runpy.run_path()` to execute the file — not `exec(open(...).read())`
- Wrap execution in try/except to capture the exception as a final TraceEvent
- Always call `tracer.stop()` in a `finally` block

---

## morpheus/compressor.py

**Purpose:** Convert a raw list of TraceEvents into grouped ExecutionChapters that can be sent to the LLM. Raw traces are too large and too noisy for direct LLM consumption.

### Dataclass: ExecutionChapter

```python
from dataclasses import dataclass, field

@dataclass
class ExecutionChapter:
    """
    A grouped, summarized segment of an execution trace.
    Each chapter represents one logical unit of work — typically one top-level function call.
    """
    chapter_id: int                    # Sequential ID starting from 1
    title: str                         # Human-readable title e.g. "Chapter 3: train_model()"
    events: list[TraceEvent]           # The raw events that belong to this chapter
    summary_hint: str                  # Short context string passed to LLM: "function call with 3 nested calls"
    duration_ms: float                 # Total time from first to last event in this chapter
    function_name: str                 # Name of the top-level function for this chapter
    event_count: int                   # Total number of events in this chapter
```

---

### Function: compress_trace

```python
def compress_trace(events: list[TraceEvent]) -> list[ExecutionChapter]:
    """
    Group a list of TraceEvents into ExecutionChapters.
    
    Grouping rules:
    1. Group by top-level function boundary: each "call" event starts a potential chapter.
    2. Max 10 events per chapter. If a function has more than 10 events, split it.
    3. Each chapter includes timing: duration_ms = (last_event.timestamp - first_event.timestamp) * 1000
    4. Empty event list returns empty chapter list.
    
    Args:
        events: List of TraceEvent objects from trace_file().
        
    Returns:
        List of ExecutionChapter objects. At least 1 chapter for any non-empty event list.
        
    Example:
        chapters = compress_trace(events)
        print(f"Compressed {len(events)} events into {len(chapters)} chapters")
    """
```

---

### Function: chapter_to_prompt

```python
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
        
    Example output:
        "Chapter 1: load_data()
         Duration: 45.2ms | Events: 3
         
         [CALL] load_data() at line 12
           locals: filepath='/data/train.csv'
         [CALL] validate() at line 8
           locals: data=<DataFrame 4200 rows>
         [RETURN] validate() → True
         [RETURN] load_data() → DataFrame(4200, 8)
         
         Hint: top-level function with 1 nested call, returned successfully"
    """
```

---

## morpheus/narrator.py

**Purpose:** Send ExecutionChapters to Ollama and stream back narration in plain English.

### Class: OllamaClient

```python
import httpx

class OllamaClient:
    """
    HTTP client for the Ollama local LLM API.
    Ollama must be running at localhost:11434 before any method is called.
    """

    def __init__(self, model: str = "mistral") -> None:
        """
        Args:
            model: Ollama model name to use. Defaults to "mistral".
                   Can be overridden via MORPHEUS_OLLAMA_MODEL env var.
        """

    def generate(self, prompt: str) -> str:
        """
        Send a prompt to Ollama and return the complete response as a string.
        
        Uses streaming internally but collects all tokens before returning.
        
        Args:
            prompt: The full prompt string to send to the model.
            
        Returns:
            Complete response string from the model.
            
        Raises:
            ConnectionError: If Ollama is not running or not reachable.
                            Message must say: "Ollama is not running. Start it with: ollama serve"
            httpx.TimeoutException: If the model takes too long to respond.
        """

    def stream(self, prompt: str) -> Generator[str, None, None]:
        """
        Send a prompt to Ollama and yield response tokens as they arrive.
        
        Args:
            prompt: The full prompt string to send to the model.
            
        Yields:
            Individual token strings as they stream from the model.
            
        Raises:
            ConnectionError: If Ollama is not running or not reachable.
        """
```

**Ollama API call format:**
```python
# POST http://localhost:11434/api/generate
# Body:
{
    "model": "mistral",
    "prompt": "...",
    "stream": True
}
# Each streamed line is JSON: {"response": "token", "done": false}
# Final line: {"response": "", "done": true}
```

---

### Function: build_narration_prompt

```python
def build_narration_prompt(chapter: ExecutionChapter, mode: str = "narrator") -> str:
    """
    Build the full system + user prompt for narrating a chapter.
    
    The system prompt instructs the LLM to:
    - Explain what happened in plain English
    - Use past tense ("the function loaded...", "it then called...")
    - Be concise — 2-4 sentences per chapter maximum
    - Never mention variable names unless they are meaningful
    - Never say "the code" — say "the program"
    
    Args:
        chapter: The ExecutionChapter to narrate.
        mode: Narration mode — affects system prompt tone.
              "narrator" = plain English explanation
              "prophecy" = focus on warnings and anomalies
              "teach" = pause and explain concepts
              
    Returns:
        Complete prompt string ready to send to OllamaClient.generate()
    """
```

---

### Function: narrate_chapter

```python
def narrate_chapter(
    chapter: ExecutionChapter,
    client: OllamaClient,
    mode: str = "narrator"
) -> str:
    """
    Narrate a single ExecutionChapter using the Ollama LLM.
    
    This is the main entry point for the narrator module.
    Called by cli.py for each chapter after compression.
    
    Args:
        chapter: The ExecutionChapter to narrate.
        client: An initialized OllamaClient instance.
        mode: Narration mode string. Default "narrator".
        
    Returns:
        Non-empty narration string in plain English.
        Returns a fallback message if LLM fails: "Chapter {id}: {function_name} ran for {duration_ms}ms"
        
    Raises:
        ConnectionError: Propagated from OllamaClient if Ollama is offline.
    """
```

---

### Function: stream_narration

```python
def stream_narration(
    chapter: ExecutionChapter,
    client: OllamaClient,
    console: "rich.console.Console",
    mode: str = "narrator"
) -> str:
    """
    Stream narration tokens to the Rich console as they arrive from Ollama.
    
    Used by cli.py to provide live output during narration.
    
    Args:
        chapter: The ExecutionChapter to narrate.
        client: An initialized OllamaClient instance.
        console: Rich Console object for terminal output.
        mode: Narration mode string.
        
    Returns:
        Complete narration string (all tokens joined) after streaming finishes.
    """
```

---

## morpheus/storage.py

**Purpose:** Persist every Morpheus run to a local SQLite database. Enables run history, time travel comparisons, and ML training data.

### Dataclass: RunRecord

```python
from dataclasses import dataclass
import json

@dataclass
class RunRecord:
    """A complete record of one Morpheus run, stored in SQLite."""
    run_id: str          # UUID4 string — generated at save time
    filepath: str        # Absolute path of the traced file
    timestamp: float     # Unix timestamp when the run was saved
    mode: str            # "narrator", "prophecy", "spy", "teach", "oracle"
    chapters: str        # JSON-serialized list of chapter titles and event counts
    narrations: str      # JSON-serialized list of narration strings per chapter
    duration_ms: float   # Total run duration in milliseconds
    event_count: int     # Total number of TraceEvents captured
    error: str = ""      # Error message if the traced script crashed, else empty string
```

---

### Class: MorpheusStorage

```python
import sqlite3
from pathlib import Path

class MorpheusStorage:
    """
    Manages the SQLite database for Morpheus run history.
    Database is created automatically if it does not exist.
    Default location: ~/.morpheus/history.db
    """

    def __init__(self, db_path: str = "~/.morpheus/history.db") -> None:
        """
        Initialize storage and create the database + table if they don't exist.
        
        Args:
            db_path: Path to the SQLite database file.
                     Can be overridden via MORPHEUS_DB_PATH env var.
                     Parent directories are created automatically.
        """

    def save_run(self, record: RunRecord) -> str:
        """
        Save a completed run record to the database.
        Generates a new UUID for run_id if record.run_id is empty.
        
        Args:
            record: Populated RunRecord dataclass.
            
        Returns:
            The run_id string of the saved record.
            
        Raises:
            sqlite3.Error: If the database write fails.
        """

    def get_run(self, run_id: str) -> RunRecord:
        """
        Retrieve a single run by its ID.
        
        Args:
            run_id: UUID string returned by save_run().
            
        Returns:
            RunRecord dataclass populated from the database row.
            
        Raises:
            KeyError: If no run with this ID exists.
            sqlite3.Error: If the database read fails.
        """

    def list_runs(self, limit: int = 20) -> list[RunRecord]:
        """
        Return the most recent runs, newest first.
        
        Args:
            limit: Maximum number of runs to return. Default 20.
            
        Returns:
            List of RunRecord objects ordered by timestamp descending.
            Returns empty list if no runs exist.
        """

    def delete_run(self, run_id: str) -> bool:
        """
        Delete a run record by ID.
        
        Args:
            run_id: UUID string of the run to delete.
            
        Returns:
            True if a record was deleted. False if no record with that ID exists.
        """

    def _create_table(self) -> None:
        """
        Create the runs table if it does not exist.
        Called automatically in __init__. Never call this directly.
        
        Table schema:
            run_id TEXT PRIMARY KEY
            filepath TEXT NOT NULL
            timestamp REAL NOT NULL
            mode TEXT NOT NULL
            chapters TEXT NOT NULL
            narrations TEXT NOT NULL
            duration_ms REAL NOT NULL
            event_count INTEGER NOT NULL
            error TEXT DEFAULT ''
        """
```

---

## morpheus/cli.py

**Purpose:** The Typer CLI application. All user-facing commands live here. This module orchestrates all other modules — it imports and calls tracer, compressor, narrator, and storage.

### App Setup

```python
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

app = typer.Typer(
    name="morpheus",
    help="A self-evolving execution intelligence system. Every other tool reads what your code says. Morpheus remembers what your code did.",
    add_completion=False,
)
console = Console()
```

---

### Command: run

```python
@app.command()
def run(
    file: str = typer.Argument(..., help="Path to the Python file to trace and narrate."),
    mode: str = typer.Option(
        "narrator",
        "--mode", "-m",
        help="Narration mode.",
        case_sensitive=False,
    ),
    personality: str = typer.Option(
        "mentor",
        "--personality", "-p",
        help="Oracle personality for narration style.",
        case_sensitive=False,
    ),
) -> None:
    """
    Trace a Python file and narrate its execution in plain English.
    
    Valid modes: narrator, prophecy, teach, oracle
    Valid personalities: mentor, critic, paranoid, teacher
    
    Example:
        morpheus run examples/simple.py
        morpheus run examples/ml_train.py --mode prophecy
        morpheus run app.js --mode oracle --personality critic
    """
```

**Implementation sequence inside `run()`:**
1. Validate file exists — print clear error and exit if not
2. Print header with Rich: file name, mode, model name
3. Call `trace_file(file)` — show spinner while running
4. Call `compress_trace(events)` — print chapter count
5. For each chapter: call `stream_narration()` to print live tokens
6. Build `RunRecord` and call `MorpheusStorage().save_run()`
7. Print completion summary: total time, event count, run_id

---

### Command: spy

```python
@app.command()
def spy(
    file: str = typer.Argument(..., help="Path to the Python script to security scan."),
) -> None:
    """
    Security scan an unknown Python script.
    Reports all sensitive actions: file access, network calls, system directory reads.
    
    Example:
        morpheus spy mystery_script.py
    """
```

---

### Command: map

```python
@app.command()
def map(
    file: str = typer.Argument(..., help="Path to the Python file to visualize."),
    browser: bool = typer.Option(False, "--browser", help="Open the dashboard in the browser automatically."),
) -> None:
    """
    Build a visual execution mind map of a Python file.
    Opens the Morpheus dashboard at localhost:4000.
    
    Example:
        morpheus map examples/ml_train.py --browser
    """
```

---

### Command: diff

```python
@app.command()
def diff(
    log1: str = typer.Argument(..., help="Path or run ID of the first run log."),
    log2: str = typer.Argument(..., help="Path or run ID of the second run log."),
) -> None:
    """
    Compare two Morpheus runs and show where execution diverged.
    
    Example:
        morpheus diff run-abc123 run-def456
    """
```

---

### Entry Point Registration in pyproject.toml

```toml
[project.scripts]
morpheus = "morpheus.cli:app"
```

---

## morpheus/prophecy.py

**Purpose:** Detect crash-prone execution patterns before a crash occurs. Warn the user proactively.

### Dataclass: ProphecyWarning

```python
@dataclass
class ProphecyWarning:
    """A single detected warning from prophecy analysis."""
    severity: str        # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    function_name: str   # Function where the pattern was detected
    line_number: int     # Line number of concern
    message: str         # Plain English warning message
    suggestion: str      # What the user should do about it
```

---

### Function: analyze_for_prophecy

```python
def analyze_for_prophecy(events: list[TraceEvent]) -> list[ProphecyWarning]:
    """
    Analyze a list of TraceEvents for dangerous patterns.
    
    Patterns to detect (implement all of these):
    1. Unbounded list growth — list variable grows on every call event
    2. Recursion depth — same function called more than 50 times without returning
    3. Large variable sizes — variable holding more than 10,000 items
    4. Missing return value — function returns None when caller expects a value
    5. Rapid repeated calls — same function called more than 100 times total
    
    Args:
        events: List of TraceEvent objects from trace_file().
        
    Returns:
        List of ProphecyWarning objects. Empty list if no warnings.
        Sorted by severity: CRITICAL first, LOW last.
    """
```

---

### Function: format_prophecy_report

```python
def format_prophecy_report(warnings: list[ProphecyWarning]) -> str:
    """
    Format a list of ProphecyWarning objects into a terminal-ready report string.
    
    Args:
        warnings: List of ProphecyWarning objects from analyze_for_prophecy().
        
    Returns:
        Formatted multi-line string. Returns "No warnings detected." if list is empty.
    """
```

---

## morpheus/spy.py

**Purpose:** Scan a script for sensitive runtime behaviors — file access, network calls, system reads. Output a security report.

### Dataclass: SpyEvent

```python
@dataclass
class SpyEvent:
    """A single sensitive action detected during spy mode tracing."""
    risk_level: str      # "LOW", "HIGH", "DANGER"
    action: str          # What happened: "reads file", "opens socket", "accesses env"
    target: str          # What it targeted: file path, IP address, env variable name
    function_name: str   # Which function triggered this action
    line_number: int     # Line number where it occurred
```

---

### Function: scan_file

```python
def scan_file(filepath: str) -> list[SpyEvent]:
    """
    Run a Python script under the tracer and analyze every event for sensitive behavior.
    
    Sensitive behaviors to flag:
    - File reads outside the current working directory → HIGH
    - File reads from home directory (~) → HIGH
    - Reads of .env, .ssh, .aws, or similar files → DANGER
    - Any socket creation or connection → DANGER
    - Any subprocess or os.system call → HIGH
    - Reading environment variables → LOW
    - Accessing /etc/ or system directories → HIGH
    
    Args:
        filepath: Path to the script to scan.
        
    Returns:
        List of SpyEvent objects ordered by risk level (DANGER first).
    """
```

---

### Function: format_spy_report

```python
def format_spy_report(events: list[SpyEvent], filepath: str) -> str:
    """
    Format SpyEvents into a human-readable security report.
    
    Report must include:
    - Header with filename
    - Each event with risk label, action, and target
    - A VERDICT at the bottom: "SAFE", "SUSPICIOUS", or "MALWARE"
    
    VERDICT logic:
        SAFE = 0 DANGER events, fewer than 3 HIGH events
        SUSPICIOUS = 1+ HIGH events or 1 DANGER event
        MALWARE = 2+ DANGER events
    
    Args:
        events: List of SpyEvent objects from scan_file().
        filepath: Path of the scanned file (for the report header).
        
    Returns:
        Formatted multi-line string report.
    """
```

---

## morpheus/teacher.py

**Purpose:** Pause execution at key moments and ask the user quiz questions. Turn narration into interactive learning.

### Dataclass: TeachingQuestion

```python
@dataclass
class TeachingQuestion:
    """A single quiz question generated from an execution event."""
    question: str              # The question to ask the user
    options: list[str]         # 3 answer options (a, b, c)
    correct_index: int         # Index of the correct option (0, 1, or 2)
    explanation: str           # Explanation shown after the user answers
    chapter: ExecutionChapter  # The chapter this question relates to
```

---

### Function: generate_question

```python
def generate_question(
    chapter: ExecutionChapter,
    client: "OllamaClient"
) -> TeachingQuestion:
    """
    Generate a quiz question for a given ExecutionChapter using the LLM.
    
    Args:
        chapter: The ExecutionChapter to generate a question about.
        client: An initialized OllamaClient instance.
        
    Returns:
        A TeachingQuestion with 3 options and a correct answer.
    """
```

---

### Function: run_teaching_session

```python
def run_teaching_session(
    chapters: list[ExecutionChapter],
    client: "OllamaClient",
    console: "rich.console.Console"
) -> dict[str, int]:
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
```

---

## morpheus/oracle.py

**Purpose:** Multi-language execution tracing using tree-sitter for parsing and language-specific runtime bridges.

### Dataclass: OracleResult

```python
@dataclass
class OracleResult:
    """Result of an Oracle mode trace on any supported language."""
    language: str               # "python", "javascript", "c", "java"
    filepath: str               # Path of the traced file
    events: list[TraceEvent]    # Normalized trace events (same format as tracer.py)
    narration: str              # Complete narration string
    personality: str            # Which personality was used
```

---

### Function: detect_language

```python
def detect_language(filepath: str) -> str:
    """
    Detect the programming language of a file from its extension.
    
    Args:
        filepath: Path to the file.
        
    Returns:
        Language string: "python", "javascript", "typescript", "c", "cpp", "java"
        
    Raises:
        ValueError: If the file extension is not supported.
                    Message: "Unsupported language. Oracle supports: Python, JavaScript, TypeScript, C, C++, Java"
    """
```

---

### Function: oracle_trace

```python
def oracle_trace(
    filepath: str,
    personality: str = "mentor"
) -> OracleResult:
    """
    Trace any supported file and return narration using the selected personality.
    
    This is the main entry point for oracle.py.
    Called by cli.py when --mode oracle is used.
    
    Args:
        filepath: Path to the file to trace.
        personality: One of "mentor", "critic", "paranoid", "teacher".
        
    Returns:
        OracleResult with narration in the selected personality style.
        
    Raises:
        ValueError: If language is not supported.
        FileNotFoundError: If file does not exist.
    """
```

---

### Function: build_oracle_prompt

```python
def build_oracle_prompt(
    events: list[TraceEvent],
    personality: str,
    language: str
) -> str:
    """
    Build a personality-specific prompt for Oracle narration.
    
    Personality system prompts:
    
    mentor:   "You are a senior developer mentoring a junior. Explain what happened
               clearly and constructively. End with one improvement suggestion."
               
    critic:   "You are a no-nonsense senior engineer doing a code review.
               Call out every problem directly. Be specific. No sugarcoating."
               
    paranoid: "You are a security researcher. Examine this execution for every
               possible vulnerability, data leak, or unsafe operation."
               
    teacher:  "You are a CS professor. Explain each step as a teaching moment.
               Connect the execution to computer science concepts the student should know."
    
    Args:
        events: List of TraceEvent objects.
        personality: One of the four personality strings.
        language: Language string for context.
        
    Returns:
        Complete prompt string.
    """
```

---

## morpheus/ml/anomaly.py

**Purpose:** Detect unusual execution patterns by comparing current run against historical runs using Isolation Forest.

### Function: build_feature_vector

```python
def build_feature_vector(chapters: list[ExecutionChapter]) -> list[float]:
    """
    Convert a list of ExecutionChapters into a numerical feature vector for ML.
    
    Features to extract (in this exact order):
    1. Total event count
    2. Number of chapters
    3. Average chapter duration_ms
    4. Max chapter duration_ms
    5. Min chapter duration_ms
    6. Number of unique function names
    7. Max recursion depth (same function appearing in nested calls)
    8. Total duration_ms
    
    Args:
        chapters: List of ExecutionChapter objects.
        
    Returns:
        List of 8 float values representing this run.
    """
```

---

### Function: detect_anomaly

```python
def detect_anomaly(
    current_vector: list[float],
    history_vectors: list[list[float]]
) -> dict[str, float | bool]:
    """
    Use Isolation Forest to determine if the current run is anomalous.
    
    Requires at least 10 historical vectors to produce meaningful results.
    
    Args:
        current_vector: Feature vector of the current run from build_feature_vector().
        history_vectors: Feature vectors of all previous runs.
        
    Returns:
        Dict with keys:
            "is_anomaly": bool — True if this run is unusual
            "anomaly_score": float — Isolation Forest score (-1 to 1, lower = more anomalous)
            "confidence": float — 0.0 to 1.0
            "message": str — Human-readable explanation
            
    Returns {"is_anomaly": False, "message": "Not enough history yet (need 10+ runs)"} 
    if fewer than 10 historical vectors are provided.
    """
```

---

## morpheus/ml/predictor.py

**Purpose:** Predict whether a current execution is likely to crash, based on patterns from historical runs.

### Function: predict_crash_probability

```python
def predict_crash_probability(
    current_vector: list[float],
    history_vectors: list[list[float]],
    history_labels: list[int]
) -> dict[str, float | str]:
    """
    Predict the probability that the current execution will crash.
    
    Args:
        current_vector: Feature vector of the current run.
        history_vectors: Feature vectors of historical runs.
        history_labels: 1 = crashed, 0 = succeeded (one per history vector).
        
    Returns:
        Dict with keys:
            "crash_probability": float — 0.0 to 1.0
            "risk_level": str — "LOW", "MEDIUM", "HIGH", "CRITICAL"
            "message": str — Human-readable prediction
            
        risk_level thresholds:
            LOW = probability < 0.3
            MEDIUM = 0.3 to 0.6
            HIGH = 0.6 to 0.85
            CRITICAL = above 0.85
            
    Returns {"crash_probability": 0.0, "risk_level": "LOW", "message": "Not enough history yet"}
    if fewer than 20 labeled examples are available.
    """
```

---

## morpheus/ml/fingerprint.py

**Purpose:** Generate and compare behavioral fingerprints (Codebase DNA) for a project.

### Function: generate_fingerprint

```python
def generate_fingerprint(chapters: list[ExecutionChapter]) -> list[float]:
    """
    Generate a behavioral fingerprint vector for a set of execution chapters.
    
    The fingerprint encodes:
    - Function call frequency distribution
    - Execution timing patterns
    - Depth of call nesting
    - Variable type patterns
    
    Args:
        chapters: List of ExecutionChapter objects from one or more runs.
        
    Returns:
        List of floats representing this codebase's behavioral fingerprint.
        Always returns a vector of length 32.
    """
```

---

### Function: compare_fingerprints

```python
def compare_fingerprints(
    fingerprint_a: list[float],
    fingerprint_b: list[float]
) -> dict[str, float | str]:
    """
    Compare two behavioral fingerprints using cosine similarity.
    
    Args:
        fingerprint_a: Fingerprint from generate_fingerprint().
        fingerprint_b: Another fingerprint from generate_fingerprint().
        
    Returns:
        Dict with keys:
            "similarity": float — 0.0 (completely different) to 1.0 (identical)
            "verdict": str — "MATCHES", "SIMILAR", "DIFFERENT", "FOREIGN"
            "message": str — Human-readable explanation
            
        verdict thresholds:
            MATCHES = similarity >= 0.9
            SIMILAR = 0.7 to 0.9
            DIFFERENT = 0.4 to 0.7
            FOREIGN = below 0.4
    """
```

---

## tests/ — Test File Contracts

Every test file must follow this structure. No test can import from another test file.

### tests/conftest.py

```python
# Shared pytest fixtures used across all test files

import pytest
from morpheus.tracer import TraceEvent
from morpheus.compressor import ExecutionChapter

@pytest.fixture
def sample_events() -> list[TraceEvent]:
    """Returns a minimal list of 3 TraceEvents for use in tests."""

@pytest.fixture
def sample_chapters() -> list[ExecutionChapter]:
    """Returns a minimal list of 2 ExecutionChapters for use in tests."""
```

---

### tests/test_tracer.py — Required Tests

```python
def test_tracer_captures_call_events():
    """trace_file() must return at least one TraceEvent with event_type == "call"."""

def test_tracer_captures_return_events():
    """trace_file() must return at least one TraceEvent with event_type == "return"."""

def test_tracer_ignores_stdlib():
    """trace_file() must not return any TraceEvent where filename contains 'site-packages' or 'lib/python'."""
```

---

### tests/test_compressor.py — Required Tests

```python
def test_compress_creates_chapters():
    """compress_trace() must return at least 1 chapter when given a non-empty event list."""

def test_chapter_to_prompt_returns_string():
    """chapter_to_prompt() must return a non-empty string."""
```

---

### tests/test_narrator.py — Required Tests

```python
def test_ollama_client_raises_on_offline(mocker):
    """OllamaClient.generate() must raise ConnectionError when Ollama is not running.
    Mock the httpx call to simulate a refused connection."""
```

---

### tests/test_storage.py — Required Tests

```python
def test_save_and_retrieve_run(tmp_path):
    """save_run() then get_run() must return a RunRecord with matching filepath."""

def test_list_runs_returns_correct_count(tmp_path):
    """After saving 5 runs, list_runs(limit=3) must return exactly 3 records."""

def test_db_created_at_path(tmp_path):
    """MorpheusStorage(db_path) must create the SQLite file at the given path."""
```

---

## NAMING CONVENTIONS

These apply to every file in `morpheus/`:

| Thing | Convention | Example |
|---|---|---|
| Classes | PascalCase | `MorpheusTracer`, `OllamaClient` |
| Functions | snake_case | `trace_file`, `compress_trace` |
| Dataclasses | PascalCase | `TraceEvent`, `ExecutionChapter` |
| Constants | UPPER_SNAKE | `DEFAULT_MODEL`, `MAX_EVENTS_PER_CHAPTER` |
| Private methods | _underscore_prefix | `_trace_handler`, `_create_table` |
| Test functions | test_ prefix | `test_tracer_captures_call_events` |

---

## INTER-MODULE DEPENDENCY RULES

These import rules must be followed. Circular imports will break the package.

```
cli.py          → may import from: tracer, compressor, narrator, storage, prophecy, spy, teacher, oracle
tracer.py       → may import from: nothing inside morpheus
compressor.py   → may import from: tracer
narrator.py     → may import from: compressor, tracer
storage.py      → may import from: nothing inside morpheus
prophecy.py     → may import from: tracer
spy.py          → may import from: tracer
teacher.py      → may import from: compressor, narrator
oracle.py       → may import from: tracer, narrator
ml/*.py         → may import from: tracer, compressor (never from cli or narrator)
```

**Rule: No module imports from cli.py. cli.py is the top of the dependency tree.**

---

*ARCHITECTURE.md — Created by Madhesh Y*  
*Read this before writing any code. Every signature here is final unless changed via GitHub Issue.*
