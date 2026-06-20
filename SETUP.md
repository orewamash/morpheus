# MORPHEUS — SETUP.md
### Complete Development Environment Setup
**For:** Claude Code, new developers, contributors  
**Platform:** Windows (primary), Mac/Linux (supported)  
**Read time:** 10 minutes  
**Read this before:** Writing any code, creating any file, running any command

---

## CRITICAL — READ THIS FIRST

Morpheus uses a local LLM (Ollama) as its narration brain. This must be installed and running before any narrator or ML tests will pass. It is free. It requires no API key. Everything runs on your own machine.

Do not skip the Ollama setup. Every core feature depends on it.

---

## STEP 1 — Python Version

Morpheus requires Python 3.11 or higher.

**Verify your version:**
```bash
python --version
# Must show: Python 3.11.x or 3.12.x
```

**If you need to install Python 3.11:**
- Windows: Download from python.org → check "Add Python to PATH" during install
- Mac: `brew install python@3.11`
- Linux: `sudo apt install python3.11 python3.11-venv`

---

## STEP 2 — Clone the Repository

```bash
git clone https://github.com/madhesh-y/morpheus
cd morpheus
```

If the repo does not exist yet (first-time setup):
```bash
mkdir morpheus
cd morpheus
git init
```

---

## STEP 3 — Create Virtual Environment

**Always use a virtual environment. Never install into system Python.**

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Mac / Linux
python3.11 -m venv .venv
source .venv/bin/activate
```

**Verify it is active:**
```bash
which python
# Should show: path ending in .venv/Scripts/python or .venv/bin/python
```

---

## STEP 4 — Install the Package in Dev Mode

```bash
pip install -e ".[dev]"
```

This installs Morpheus in editable mode — meaning code changes take effect immediately without reinstalling.

**If pyproject.toml does not exist yet**, create it first (see Project Structure section below).

**Verify install:**
```bash
morpheus --help
# Should show all available commands
```

---

## STEP 5 — Install Ollama (Critical)

Ollama runs open-source LLMs locally on your machine. It is free forever.

**Windows:**
1. Go to https://ollama.com
2. Click "Download for Windows"
3. Run the installer
4. Ollama starts automatically as a background service

**Mac:**
```bash
brew install ollama
ollama serve  # start the service
```

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Verify Ollama is running:**
```bash
ollama --version
# Should print version number

curl http://localhost:11434
# Should return: "Ollama is running"
```

---

## STEP 6 — Pull the Mistral Model

```bash
ollama pull mistral
```

This downloads Mistral 7B (~4GB). Download it once, use it forever offline.

**This will take several minutes.** Wait for it to complete fully.

**Verify the model works:**
```bash
ollama run mistral "Say hello in one sentence"
# Should print a greeting — if it does, Ollama is ready
```

---

## STEP 7 — Run the Test Suite

```bash
pytest tests/ -v
```

At the start of the project (Week 1), this will show 0 tests collected. That is fine.

As tests are written, this command must pass with 0 failures before any code is pushed.

---

## PROJECT STRUCTURE

This is the exact folder and file structure to create. Do not deviate from this structure. Every file has a specific purpose defined in ARCHITECTURE.md.

```
morpheus/                          ← Git repository root
│
├── pyproject.toml                 ← Package config — CREATE THIS FIRST
├── README.md                      ← Public documentation (write last)
├── CONTRIBUTING.md                ← Contributor guide (write at Week 11)
├── LICENSE                        ← MIT license text
│
├── docs/                          ← All planning documents
│   ├── PROJECT.md                 ← Vision and complete spec
│   ├── SUMMARY.md                 ← Onboarding guide
│   ├── EVOLUTION.md               ← ML architecture spec
│   ├── TASKS.md                   ← THIS FILE'S SIBLING — sprint board
│   ├── SETUP.md                   ← THIS FILE
│   ├── ARCHITECTURE.md            ← Code blueprint — function signatures
│   ├── FRONTEND.md                ← Dashboard specs
│   └── ORACLE.md                  ← Oracle mode spec
│
├── morpheus/                      ← Main Python package
│   ├── __init__.py                ← Version string
│   ├── cli.py                     ← Typer CLI entry point
│   ├── tracer.py                  ← sys.settrace engine
│   ├── compressor.py              ← Trace → chapters
│   ├── narrator.py                ← Ollama integration
│   ├── prophecy.py                ← Crash prediction mode
│   ├── spy.py                     ← Security scanner mode
│   ├── teacher.py                 ← Teaching mode
│   ├── storage.py                 ← SQLite run history
│   ├── oracle.py                  ← Multi-language engine
│   └── ml/
│       ├── __init__.py
│       ├── anomaly.py             ← Isolation Forest
│       ├── predictor.py           ← XGBoost crash predictor
│       ├── profiler.py            ← HDBSCAN user profiler
│       ├── concept_writer.py      ← NLP concept docs
│       └── fingerprint.py        ← Codebase DNA
│
├── dashboard/                     ← React frontend
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx
│       ├── MindMap.jsx
│       ├── RunHistory.jsx
│       └── SpyReport.jsx
│
├── api/                           ← FastAPI backend
│   ├── server.py
│   └── routes/
│       ├── runs.py
│       └── mindmap.py
│
├── examples/                      ← Test scripts for development
│   ├── simple.py
│   ├── ml_train.py
│   ├── will_crash.py
│   ├── safe_script.py
│   └── malware_sim.py
│
└── tests/                         ← Pytest test suite
    ├── conftest.py
    ├── test_tracer.py
    ├── test_compressor.py
    ├── test_narrator.py
    ├── test_storage.py
    ├── test_prophecy.py
    └── test_spy.py
```

---

## pyproject.toml — EXACT CONTENT

Create this file at the repository root. This is the exact content to use:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "morpheus-cli"
version = "0.1.0"
description = "A self-evolving execution intelligence system. Every other tool reads what your code says. Morpheus remembers what your code did."
readme = "README.md"
license = { file = "LICENSE" }
requires-python = ">=3.11"
authors = [
  { name = "Madhesh Y", email = "your-email@example.com" }
]
keywords = ["cli", "debugging", "execution", "narration", "ai", "developer-tools"]
classifiers = [
  "Development Status :: 3 - Alpha",
  "Environment :: Console",
  "Intended Audience :: Developers",
  "License :: OSI Approved :: MIT License",
  "Programming Language :: Python :: 3.11",
  "Topic :: Software Development :: Debuggers",
]

dependencies = [
  "typer>=0.9.0",
  "rich>=13.0.0",
  "httpx>=0.25.0",
  "libcst>=1.1.0",
  "tree-sitter>=0.20.0",
  "scikit-learn>=1.3.0",
  "xgboost>=2.0.0",
  "hdbscan>=0.8.33",
  "networkx>=3.2.0",
  "torch>=2.0.0",
  "torch-geometric>=2.4.0",
]

[project.optional-dependencies]
dev = [
  "pytest>=7.4.0",
  "pytest-cov>=4.1.0",
  "pytest-mock>=3.12.0",
  "black>=23.0.0",
  "ruff>=0.1.0",
  "mypy>=1.6.0",
]

[project.scripts]
morpheus = "morpheus.cli:app"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]

[tool.black]
line-length = 88
target-version = ["py311"]

[tool.ruff]
line-length = 88
target-version = "py311"
```

---

## ENVIRONMENT VARIABLES

Morpheus uses these environment variables. They are all optional — defaults work for local development.

Create a `.env` file at the repository root (never commit this file):

```bash
# Ollama configuration
MORPHEUS_OLLAMA_URL=http://localhost:11434
MORPHEUS_OLLAMA_MODEL=mistral

# Storage
MORPHEUS_DB_PATH=~/.morpheus/history.db

# Dashboard
MORPHEUS_DASHBOARD_PORT=4000

# Logging
MORPHEUS_LOG_LEVEL=INFO
```

Load these in code using:
```python
import os
OLLAMA_URL = os.getenv("MORPHEUS_OLLAMA_URL", "http://localhost:11434")
```

Do NOT use python-dotenv — it is an unnecessary dependency. Use `os.getenv` with defaults.

---

## RUNNING THE PROJECT

### Run Morpheus (after Week 2)
```bash
# Basic narrator mode
morpheus run examples/simple.py

# Oracle mode with personality
morpheus run examples/simple.py --mode oracle --personality critic

# Spy mode
morpheus spy examples/malware_sim.py

# Open dashboard
morpheus map examples/ml_train.py --browser
```

### Run tests
```bash
# All tests
pytest tests/ -v

# Specific module
pytest tests/test_tracer.py -v

# With coverage
pytest tests/ --cov=morpheus --cov-report=term-missing
```

### Run linter
```bash
ruff check morpheus/
black --check morpheus/
```

### Run the dashboard API (after Week 9)
```bash
cd api
uvicorn server:app --reload --port 4000
```

### Run the React dashboard (after Week 9)
```bash
cd dashboard
npm install
npm run dev
```

---

## COMMON ERRORS AND FIXES

**Error: `morpheus: command not found`**
Fix: Virtual environment is not activated. Run `.venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (Mac/Linux).

**Error: `Connection refused` when calling Ollama**
Fix: Ollama service is not running. On Windows, check system tray — Ollama should be running. On Linux/Mac, run `ollama serve` in a separate terminal.

**Error: `ModuleNotFoundError: No module named 'morpheus'`**
Fix: Package is not installed. Run `pip install -e ".[dev]"` from the repo root.

**Error: `torch-geometric` install fails**
Fix: Install PyTorch first, then torch-geometric. Run:
```bash
pip install torch==2.1.0
pip install torch-geometric
```

**Error: Mistral model not found**
Fix: Run `ollama pull mistral` and wait for full download.

**Error: `hdbscan` install fails on Windows**
Fix: Install build tools first:
```bash
pip install --upgrade pip setuptools wheel
pip install hdbscan
```

---

## CODE STANDARDS

Every file in `morpheus/` must follow these rules. Claude Code will enforce them.

1. **Type hints on every function** — no function without parameter types and return type
2. **Docstring on every public function** — one-line minimum
3. **No print statements in library code** — use `rich.console.Console` for output
4. **No bare except clauses** — always catch specific exceptions
5. **Every module has tests** — no module merged without at least 2 passing tests
6. **Black formatting** — run `black morpheus/` before every commit
7. **No hardcoded paths** — always use `os.path` or `pathlib.Path`
8. **No hardcoded model names** — always read from environment variable with default

**Example of correct code style:**

```python
from dataclasses import dataclass
from pathlib import Path
import sys

@dataclass
class TraceEvent:
    """A single captured event from sys.settrace."""
    event_type: str
    function_name: str
    filename: str
    line_number: int
    timestamp: float

def trace_file(filepath: Path) -> list[TraceEvent]:
    """
    Execute a Python file and capture all trace events.
    
    Args:
        filepath: Path to the Python file to trace.
        
    Returns:
        List of TraceEvent objects captured during execution.
        
    Raises:
        FileNotFoundError: If filepath does not exist.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    tracer = MorpheusTracer()
    tracer.start()
    # ... rest of implementation
    return tracer.get_events()
```

---

## GIT WORKFLOW

**Branch naming:**
- `main` — stable, always works
- `dev` — active development
- `feature/tracer` — feature branches
- `fix/narrator-crash` — bug fix branches

**Commit message format:**
```
feat: add sys.settrace integration to tracer.py
fix: handle ConnectionError when Ollama is offline
docs: update TASKS.md with Week 2 progress
test: add 3 tests for compressor chapter grouping
```

**Before every commit:**
```bash
black morpheus/
ruff check morpheus/
pytest tests/ -v
```

Never commit with failing tests.

---

*Read ARCHITECTURE.md next — it defines exactly what functions to write inside each file.*
