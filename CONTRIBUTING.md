# MORPHEUS — CONTRIBUTING.md
### How to Contribute to Morpheus
**For:** All team members, collaborators, and external contributors  
**Read time:** 10 minutes  
**Read after:** SUMMARY.md, SETUP.md, ARCHITECTURE.md

---

## BEFORE YOU WRITE ANY CODE

1. Read `SUMMARY.md` — understand what Morpheus is and why it exists
2. Read `SETUP.md` — set up your environment and verify it works
3. Read `ARCHITECTURE.md` — understand the module you are building
4. Read `TASKS.md` — find the task assigned to you
5. Create a branch for your task (see Git Workflow below)
6. Only then start writing code

**If you skip steps 1–4, your code will very likely conflict with someone else's work.**

---

## CLAIMING A TASK

1. Open `TASKS.md`
2. Find a task with status `[ ]` and no owner other than yours
3. Change `[ ]` to `[~]` in TASKS.md
4. Commit that change: `git commit -m "docs: claim task — cli.py skeleton"`
5. If a task has no owner listed, ask Madhesh Y before claiming it

**One person per task. No exceptions.**

---

## GIT WORKFLOW

### Branch Naming

Every task gets its own branch. Name it by type and what it does:

```
feature/<module>    — new functionality
fix/<what>          — bug fix
docs/<what>         — documentation only
test/<what>         — tests only
```

**Examples:**
```bash
git checkout -b feature/tracer
git checkout -b feature/narrator
git checkout -b fix/ollama-connection-error
git checkout -b docs/architecture-update
git checkout -b test/compressor-tests
```

### Branch Rules

- `main` — stable, always passes all tests. Never commit directly to main.
- `dev` — active integration. Merge your feature branch here first.
- Feature branches — one per task, deleted after merging.

**Never commit directly to `main` or `dev`.** Always use a branch and a pull request.

---

## COMMIT MESSAGE FORMAT

Every commit message must follow this exact format:

```
<type>: <short description in lowercase>
```

**Types:**

| Type | When to use |
|---|---|
| `feat` | Adding new functionality |
| `fix` | Fixing a bug |
| `test` | Adding or fixing tests |
| `docs` | Documentation only |
| `refactor` | Code restructure with no feature change |
| `style` | Formatting, black, ruff — no logic change |
| `chore` | Build scripts, CI, dependencies |

**Good commit messages:**
```
feat: add sys.settrace integration to tracer.py
fix: handle ConnectionError when Ollama is offline
test: add 3 tests for compressor chapter grouping
docs: update TASKS.md with Week 2 progress
refactor: split narrate_chapter into build_prompt and send_to_ollama
```

**Bad commit messages (never do these):**
```
fixed stuff
WIP
asdf
update
changes
```

**One commit = one logical change.** Do not put 5 unrelated changes in one commit.

---

## CODE STANDARDS

Every file in `morpheus/` must follow these rules. Pull requests that violate these rules will not be merged.

### 1. Type hints on every function

```python
# CORRECT
def trace_file(filepath: str) -> list[TraceEvent]:

# WRONG — no hints
def trace_file(filepath):
```

### 2. Docstring on every public function

```python
# CORRECT
def compress_trace(events: list[TraceEvent]) -> list[ExecutionChapter]:
    """
    Group a list of TraceEvents into ExecutionChapters.
    
    Args:
        events: List of TraceEvent objects from trace_file().
        
    Returns:
        List of ExecutionChapter objects.
    """

# WRONG — no docstring
def compress_trace(events):
    pass
```

### 3. No print statements in library code

```python
# CORRECT — use rich.console for output
from rich.console import Console
console = Console()
console.print("[green]Done![/green]")

# WRONG — raw print
print("Done!")
```

Only `cli.py` should produce terminal output. All other modules should be silent. They return values — they do not print.

### 4. No bare except clauses

```python
# CORRECT — catch specific exceptions
try:
    response = client.post(url, json=payload)
except httpx.ConnectError:
    raise ConnectionError("Ollama is not running. Start it with: ollama serve")
except httpx.TimeoutException:
    raise TimeoutError("Ollama took too long to respond.")

# WRONG — catches everything silently
try:
    response = client.post(url, json=payload)
except:
    pass
```

### 5. No hardcoded paths

```python
# CORRECT
import os
db_path = os.getenv("MORPHEUS_DB_PATH", "~/.morpheus/history.db")

# WRONG
db_path = "/home/madhesh/.morpheus/history.db"
```

### 6. No hardcoded model names

```python
# CORRECT
model = os.getenv("MORPHEUS_OLLAMA_MODEL", "mistral")

# WRONG
model = "mistral"
```

### 7. Use pathlib for file paths

```python
# CORRECT
from pathlib import Path
filepath = Path(filepath).resolve()
if not filepath.exists():
    raise FileNotFoundError(f"File not found: {filepath}")

# WRONG
import os
if not os.path.exists(filepath):
    raise Exception("File not found")
```

### 8. Black formatting on every commit

Run this before every commit:
```bash
black morpheus/
```

If black changes your file, commit the formatted version. Do not disable black with `# fmt: off` unless there is a compelling reason.

---

## BEFORE EVERY COMMIT — MANDATORY CHECKLIST

Run these commands. Every one must pass. Do not commit if any fail.

```bash
# 1. Format with black
black morpheus/

# 2. Lint with ruff
ruff check morpheus/

# 3. Run tests
pytest tests/ -v

# 4. Verify import works
python -c "import morpheus; print(morpheus.__version__)"
```

If tests fail — fix them. Do not commit with failing tests. Do not push with failing tests.

---

## PULL REQUEST PROCESS

### When to open a PR

Open a pull request when:
- Your task is fully complete
- All tests for your module pass
- `black` and `ruff` pass with no issues
- You have manually tested your code works end-to-end

### PR title format

Same as commit message format:
```
feat: tracer.py — sys.settrace integration with stdlib filtering
fix: narrator.py — handle Ollama connection timeout gracefully
```

### PR description template

Every PR must fill in this template:

```markdown
## What this PR does
One paragraph explaining what was built or fixed.

## How to test it manually
Step by step instructions to verify it works.

## Tests added
List the test functions added and what they verify.

## Checklist
- [ ] black passes
- [ ] ruff passes  
- [ ] pytest passes
- [ ] TASKS.md updated (task marked [x])
- [ ] No hardcoded paths or model names
- [ ] Type hints on all new functions
- [ ] Docstrings on all public functions
```

### Who reviews PRs

All PRs are reviewed by Madhesh Y before merging. Response within 48 hours.

If feedback is given:
- Address each comment
- Do not argue in the PR — if you disagree, discuss in the GitHub Issue first
- Once all comments are resolved, request a re-review

---

## WHAT TO DO WHEN BLOCKED

A task is blocked when you cannot make progress for more than 24 hours due to something outside your control.

### Step 1 — Mark it blocked

In TASKS.md, change `[~]` to `[!]` and add a note:
```
BLOCKED: Cannot figure out how V8 Inspector WebSocket connection works
NEEDS: Example of V8 Protocol message flow or working code sample
OWNER: Madhesh Y to unblock
```

Commit and push this change immediately.

### Step 2 — Create a GitHub Issue

Title: `BLOCKED: [task name] — [brief reason]`

In the body:
- What you were trying to do
- What you tried that didn't work (show the error messages)
- What you need to unblock

### Step 3 — Pick up another task

Do not sit idle. Look at TASKS.md for any other task with `[ ]` status that is not blocked. Pick it up while waiting to be unblocked.

---

## WHAT NOT TO DO

These are the most common mistakes. Read them before you start.

**Do not rename functions from ARCHITECTURE.md**
`cli.py` calls `trace_file()`. If you name your function `run_tracer()` instead, the whole chain breaks.

**Do not add dependencies not in pyproject.toml**
If you need a library that is not in the dependencies list, ask first. Adding unknown libraries breaks other contributors' environments.

**Do not commit `.env` files**
The `.env` file contains local configuration and must never be committed. It is in `.gitignore`.

**Do not push directly to `main`**
Always use a branch and a pull request. Even if you are the only contributor right now.

**Do not write "in progress" comments in code**
No `# TODO: finish this later` or `# WIP` or `# TEMP`. If it is not done, it does not go in a commit.

**Do not swallow exceptions**
If a function fails, raise a specific exception with a clear message. Do not catch it and return None silently.

---

## ASKING FOR HELP

Before asking for help:
1. Read the relevant section in ARCHITECTURE.md again
2. Search GitHub Issues for similar problems
3. Try for at least 30 minutes on your own

When asking for help:
- Create a GitHub Issue
- Include the error message in full
- Include the code that caused it
- Include what you already tried

Do not send code in Telegram or WhatsApp for debugging. GitHub Issues create a searchable history that helps the whole team.

---

## UNDERSTANDING THE CODEBASE IN 5 MINUTES

If you are completely new, here is the fastest way to understand the code:

**Step 1:** Read `morpheus/__init__.py` — 1 line
**Step 2:** Read `morpheus/tracer.py` — the core of everything
**Step 3:** Run `morpheus run examples/simple.py` and watch what happens
**Step 4:** Add a `console.print(events)` call in `cli.py` to see raw events
**Step 5:** Now read `compressor.py` — you'll understand what it's compressing

After this, the rest of the architecture will make sense.

---

## THE ONE RULE ABOVE ALL OTHERS

**If it doesn't have a test, it doesn't exist.**

Every module you build needs at least 2 passing tests before it is considered done. A function that works on your machine but has no tests is a liability, not an asset. It will break silently when something else changes.

Write the test first if you can. It forces you to think about what your function should actually do before you write it.

---

*CONTRIBUTING.md — Created by Madhesh Y*  
*Questions? Open a GitHub Issue. Do not DM.*
