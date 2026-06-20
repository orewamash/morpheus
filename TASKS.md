# MORPHEUS — TASKS.md
### The Live Sprint Board
**Maintained by:** Madhesh Y (Project Lead)  
**Last updated:** June 2026  
**Rule:** This file is updated every Monday. Every task has one owner. No task is "in progress" for more than 3 days without a blocker note.

---

## HOW TO USE THIS FILE

1. Read `SUMMARY.md` first if you are new.
2. Find your name in the current sprint below.
3. Pick the first task with status `[ ]` assigned to you.
4. When you start — change `[ ]` to `[~]`
5. When done — change `[~]` to `[x]`
6. If blocked — add a `BLOCKED:` note below the task explaining why.

**Status legend:**
- `[ ]` Not started
- `[~]` In progress
- `[x]` Done
- `[!]` Blocked

---

## CURRENT SPRINT — COMPLETE
**102 tests passing** — all modules implemented, all modes working.

---

### ALL TASKS COMPLETE ✓

- [x] **Environment setup** — Python 3.14, pip install works
- [x] **Task 1: Project scaffold** — pyproject.toml, __init__.py, version 0.1.0
- [x] **Task 2: CLI skeleton** — run/spy/map/diff all work with Rich output
- [x] **Task 3: Tracer engine** — TraceEvent, MorpheusTracer, sys.settrace, stdlib filtering
- [x] **Task 4: Example scripts** — simple.py, ml_train.py, will_crash.py, safe_script.py, malware_sim.py
- [x] **Task 5: Compressor** — ExecutionChapter, compress_trace, chapter_to_prompt
- [x] **Task 6: Ollama narrator** — OllamaClient, streaming, connection error handling
- [x] **Task 7: Storage** — MorpheusStorage with SQLite, RunRecord, save/get/list/delete
- [x] **Task 8: Wire CLI** — trace → compress → narrate → save, Rich panels/spinners/styling

### SPRINT 2 — COMPLETE ✓

- [x] **Prophecy mode** (`prophecy.py`) — 5 pattern detectors, format_prophecy_report
- [x] **Time Travel diff** (`differ.py`) — compute_diff, format_diff_report, load_run_events
- [x] **Spy mode** (`spy.py`) — scan_file, monkey-patch interceptors, risk scoring
- [x] **Teaching mode** (`teacher.py`) — generate_question, run_teaching_session
- [x] **Oracle mode** (`oracle.py`) — detect_language, oracle_trace, 4 personalities
- [x] **Rich formatting polish** — Panels, Rules, spinners, color-coded output
- [x] **Integration tests** — 21 tests covering trace→compress→store→diff→graph pipeline

### SPRINT 3 — COMPLETE ✓

- [x] **Oracle mode** — language detection (py/js/ts/c/cpp/java), personality prompts, event truncation

### SPRINT 4 — COMPLETE ✓

- [x] **FastAPI server** (`api/server.py`) — 6 endpoints on port 4000
- [x] **React dashboard** (`dashboard/`) — Vite + React + D3 force graph + run history table

### SPRINT 5 — COMPLETE ✓

- [x] **ML anomaly detection** (`ml/anomaly.py`) — Isolation Forest, feature vectors
- [x] **ML crash predictor** (`ml/predictor.py`) — RandomForest probability model
- [x] **Execution graph builder** (`ml/execution_graph.py`) — networkx DiGraph from events/chapters
- [x] **GAT model scaffold** (`ml/gat_model.py`) — GATModel with MemoryBank, fallback encoding
- [x] **Execution profiler** (`ml/profiler.py`) — per-function duration tracking
- [x] **Concept writer** (`ml/concept_writer.py`) — behavioral concept inference

### SHIP — COMPLETE ✓

- [x] **GitHub Actions CI** (`.github/workflows/ci.yml`) — lint + format + test on 3.11/3.12

---

## DECISIONS LOG

This section records every significant decision made during development, with the reason. This prevents the same argument from happening twice.

| Date | Decision | Reason |
|---|---|---|
| June 2026 | Use Typer over Click for CLI | Typer has better type inference, cleaner syntax, auto-generates help text |
| June 2026 | Use httpx over requests for Ollama calls | httpx supports streaming natively without workarounds |
| June 2026 | SQLite over PostgreSQL for storage | Zero setup, runs locally, perfect for a CLI tool |
| June 2026 | Mistral 7B as default model | Best balance of speed and quality for local narration on CPU |
| June 2026 | Filter stdlib from traces | Including stdlib creates noise that degrades narration quality |
| June 2026 | Group traces into chapters before sending to LLM | Sending raw traces is too large for context window and produces poor narration |

---

## BLOCKED TASKS

*(Empty — no blockers at project start)*

When a task is blocked, add it here:
```
TASK: [task name]
BLOCKED BY: [reason]
NEEDS: [what would unblock it]
OWNER: [who is responsible for unblocking]
```

---

*Updated by Madhesh Y — check this file every Monday morning*
