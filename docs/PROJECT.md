# MORPHEUS — PROJECT BIBLE
### The Complete Technical & Conceptual Document
**Author:** Madhesh Y (Register Number: 192512387)  
**Institution:** Saveetha School of Engineering, SIMATS  
**Project Type:** Open Source CLI Tool + Web Dashboard + ML Intelligence Layer  
**Status:** v1.0 — Released  
**License:** MIT

---

## TABLE OF CONTENTS

1. [What is Morpheus?](#1-what-is-morpheus)
2. [The Problem Morpheus Solves](#2-the-problem-morpheus-solves)
3. [Why Morpheus Cannot Be Replaced by Claude, Cursor, or Any AI Chat Tool](#3-why-morpheus-cannot-be-replaced)
4. [What Type of Software Is Morpheus?](#4-what-type-of-software-is-morpheus)
5. [How Users Install and Use Morpheus](#5-how-users-install-and-use-morpheus)
6. [All Modes — Complete Breakdown](#6-all-modes)
7. [Oracle Mode — The Insane Mode](#7-oracle-mode)
8. [The ML Brain — How Morpheus Evolves](#8-the-ml-brain)
9. [The 5 Generations of Morpheus](#9-the-5-generations)
10. [Who Uses Morpheus — Complete Audience](#10-who-uses-morpheus)
11. [Full Tech Stack — Everything Is Free](#11-full-tech-stack)
12. [Complete Folder Structure](#12-complete-folder-structure)
13. [Team Documentation Files](#13-team-documentation-files)
14. [Week-by-Week Build Roadmap — v1](#14-build-roadmap)
15. [How Users Access Morpheus (Distribution)](#15-distribution)
16. [How Morpheus Earns Revenue — All Paths](#16-revenue-paths)
17. [The Honest Reality — Limitations and Strengths](#17-honest-reality)
18. [The One-Line Identity of Morpheus](#18-identity)

---

## 1. What is Morpheus?

Morpheus is a **self-evolving execution intelligence system** for code.

It is NOT:
- A website or hosted web application
- A mobile app
- A browser extension
- An IDE or code editor
- A static code analyzer that reads files

It IS:
- A **CLI tool** (command-line tool) that users install once and run from their terminal
- An **execution watcher** — it observes code as it actually runs, not as it sits in a file
- An **ML-powered brain** that narrates, predicts, learns, and evolves over time
- An **optional web dashboard** that opens locally in your browser for visual run history and mind maps

The best analogy: **Morpheus is to code understanding what VLC is to video.** You point it at a file, it does something powerful with it — completely offline, completely free.

### The Robot Chef Analogy (For Non-Technical Understanding)

Imagine a robot chef in a kitchen. You give it a recipe and it starts cooking. You are sitting outside. You have no idea what it is doing in there — is it boiling water? Did it add salt? Is something burning?

Now imagine the robot chef has a microphone and narrates every step out loud in plain English as it cooks:

> *"Okay, I'm boiling water now... adding 2 cups of rice... heat is too high, turning it down... forgot the salt, adding it now... rice looks cooked, turning off the flame!"*

**That is Morpheus.** The robot chef is any computer program. The kitchen is the runtime — the moment the code actually executes. Morpheus is the microphone that makes the program narrate itself, live, in plain English, as it runs.

---

## 2. The Problem Morpheus Solves

### The 2026 Reality

In 2026, AI tools like Claude, Cursor, GitHub Copilot, and ChatGPT can write hundreds of lines of code from a single prompt. This has created an entirely new category of developer: **the vibe coder**.

A vibe coder:
- Prompts AI to write code
- Runs it
- It works (sometimes)
- Has **absolutely no idea why it works**
- The moment it breaks — they are completely lost

This is not 10 people. This is **millions of developers globally** right now.

### The Static vs Dynamic Gap

Every AI tool in 2026 — Claude, Cursor, Copilot, Antigravity, all of them — does the same thing:

**They read dead code.** Static text sitting in a file. They explain what the code **says**.

Morpheus does something fundamentally different:

**It watches what the code does when it actually runs.**

### A Concrete Example

```python
def calculate_score(user):
    return user["points"] * 1.5
```

You show this to Claude → Claude says: *"It multiplies the user's points by 1.5."* Correct. Done. No need for Morpheus here.

Now imagine a vibe coder has a 3,000-line app. They run it. A user's score goes negative. They have no idea why.

You paste 3,000 lines into Claude → Claude guesses from text. It does not know:
- What actual values flowed through functions at runtime
- Which path the code actually took that day
- Which function was called 4,000 times vs never called at all
- What the exact value was at the exact moment the score went negative

**Morpheus was there.** It watched the execution live. It saw the exact moment. It knows the chain of calls that caused it.

### The Key Distinction

| What Claude/Cursor does | What Morpheus does |
|---|---|
| Reads the recipe | Watches the cooking |
| Explains what code says | Narrates what code did |
| Guesses from text | Reports from live memory |
| Reacts when you ask | Speaks up unprompted |
| Forgets after conversation | Stores every run permanently |
| Same for everyone | Learns YOUR patterns specifically |

---

## 3. Why Morpheus Cannot Be Replaced

This is the most important question and it has a definitive answer.

**You cannot paste a running program into Claude.**

You cannot ask Cursor: *"What values did my variables have at runtime 3 days ago?"*

You cannot ask Copilot: *"Why did my program behave differently on Tuesday vs Wednesday even though the code didn't change?"*

Morpheus has the **execution history**. No other tool on Earth will ever have that — because no other tool was there when it happened.

The evolved Morpheus goes further: its ML layer builds a **permanent memory** of every execution, learns what **normal** looks like for YOUR specific codebase, and alerts you the moment something deviates — **unprompted**, **automatically**, **before you even ask**.

That is not a chat assistant. **That is a guardian that lives in your codebase.**

---

## 4. What Type of Software Is Morpheus?

**Morpheus is a CLI tool with an optional local web dashboard.**

### The Three Layers

| Layer | What it is | Technology |
|---|---|---|
| Layer 1: CLI | Terminal commands the user runs | Python + Typer |
| Layer 2: Engine | The trace + LLM + ML core | Python + sys.settrace + Ollama + scikit-learn |
| Layer 3: Dashboard | Optional visual UI in browser | FastAPI + React + D3.js |

### What "CLI Tool" means practically

- User opens Windows PowerShell or Command Prompt
- Types `morpheus run mycode.py`
- Morpheus runs and outputs narration directly in the terminal
- No browser needed for basic use
- No account, no sign-in, no internet required

### What the Dashboard is

- Not a hosted website
- Opens at `http://localhost:4000` — runs on the user's own machine
- Shows run history, mind maps, narration logs, spy reports
- Like a local admin panel, not a cloud service

---

## 5. How Users Install and Use Morpheus

### Installation (Windows, Mac, Linux)

```bash
# Install once — works on Windows PowerShell, Mac Terminal, Linux
pip install morpheus-cli
```

That is the entire installation. One command. No sign-up. No API key. No internet dependency after install.

### Basic Usage

```bash
# Narrator mode — explain what this script does as it runs
morpheus run mycode.py

# Oracle mode — any language, with personality
morpheus run app.js --mode oracle --personality critic

# Spy mode — security scan an unknown script
morpheus spy mystery_script.py

# Prophecy mode — predict crashes before they happen
morpheus run scraper.py --mode prophecy

# Teaching mode — interactive learning while code runs
morpheus run sort_algo.py --mode teach

# Time travel mode — compare two runs
morpheus diff run1.log run2.log

# Mind map — open visual browser dashboard
morpheus map mycode.py --browser
```

### What the user sees in their terminal (Narrator mode example)

```
PS C:\projects\ml> morpheus run train_model.py

Morpheus v1.0 — narrator mode
watching  : train_model.py
llm model : mistral-7b via Ollama (running locally)
─────────────────────────────────────────────────

[0.01s] Opening the dataset — found 4,200 rows across 8 columns.
[0.03s] Cleaning data — removing 312 rows with missing values.
[0.05s] Splitting into 80% training, 20% testing. Standard split.
[0.12s] Training started — SVR model with RBF kernel.
[0.89s] Epoch 8: validation loss dropping steadily — model is learning.
[1.20s] Epoch 14: loss flattened at 0.21 — model converged. Stopped early.
[1.22s] Saving model to models/svr_model.pkl — complete.

✓ Done — 1.22s — 7 events narrated — run saved to history
```

---

## 6. All Modes

Morpheus has 6 core modes. Each is accessed via the `--mode` flag or a dedicated command.

---

### Mode 1: Narrator Mode (Entry Level)

**Command:** `morpheus run file.py`

**What it does:** Watches a program execute step by step, line by line, and narrates each meaningful action in plain English in real time.

**Who it's for:** Vibe coders, students, anyone running code they don't fully understand.

**What makes it different from asking Claude:** Claude reads the static file. Narrator mode watches the live execution — it reports what actually happened, not what the code says should happen.

---

### Mode 2: Time Travel Mode

**Command:** `morpheus diff run1.log run2.log`

**What it does:** Runs the same program twice with different inputs. Morpheus compares the two execution stories side by side and identifies the exact moment and reason the two paths diverged.

**Example output:**
```
[SAME]  Reading dataset — both loaded 4,200 rows
[SAME]  Cleaning — both removed ~310 rows
[SPLIT] train_model() — Run 1 converged at epoch 14
        Run 2 never converged — loss kept rising
[ROOT]  Difference began at normalize() in run2
        — scaling was applied twice by mistake
```

**Who it's for:** Developers debugging why the same code behaves differently with different data.

---

### Mode 3: Prophecy Mode

**Command:** `morpheus run file.py --mode prophecy`

**What it does:** Detects dangerous execution patterns BEFORE the program crashes. Warns the user what is about to go wrong — before it happens.

**This is what no debugger on Earth does.** A debugger tells you what broke after it breaks. Morpheus tells you it's about to break. Like a doctor reading your vitals and saying "your blood pressure is climbing, you're going to have a problem in about 3 minutes."

**Example output:**
```
⚠ PROPHECY WARNING at line 47:
List index is growing unbounded inside loop.
At current rate it will exceed memory in ~140 iterations.
This program will crash around page 143.
Suggested fix: add a flush every 50 iterations.
```

---

### Mode 4: Spy Mode

**Command:** `morpheus spy mystery_script.py`

**What it does:** Runs any unknown Python script in a sandboxed trace and reports every sensitive action it attempts — reading files, accessing system directories, making network connections, sending data.

**Why this matters in 2026:** People blindly run AI-generated scripts all the time. Spy mode catches malware that antivirus misses because it watches what code actually does at runtime, not what its signature looks like.

**Example output:**
```
SECURITY REPORT — mystery_script.py

[LOW]    reads current working directory
[LOW]    reads Python version info
[HIGH]   reads C:\Users\Madhesh\.ssh\known_hosts
[HIGH]   reads C:\Users\Madhesh\Documents\ folder listing
[DANGER] reads C:\Users\Madhesh\.env — may contain API keys
[DANGER] opens socket connection to 185.220.101.47:443
[DANGER] attempting HTTP POST with your file contents

VERDICT: This script is almost certainly malware.
         It is reading your sensitive files and attempting
         to send them to an external server. DO NOT run it.
```

---

### Mode 5: Teaching Mode

**Command:** `morpheus run file.py --mode teach`

**What it does:** Instead of just narrating, Morpheus pauses at key moments during execution and asks the user questions about what just happened. Turns code execution into an interactive lesson.

**Why it exists:** Universities and coding bootcamps could adopt this. It makes learning to understand code active rather than passive.

**Example output:**
```
[Running...] Array: [5, 2, 8, 1, 9]

❓ QUESTION: The program just compared index 0 and index 1.
   Value at 0 is 5. Value at 1 is 2.
   What do you think it will do next?

   a) Swap them    b) Skip    c) Stop

You answered: a
✓ Correct! It swapped because 5 > 2.
  The larger value is bubbling to the right.
```

---

### Mode 6: Mind Map Mode

**Command:** `morpheus map file.py --browser`

**What it does:** Builds a live interactive visual graph in the browser showing which functions called which, how data flowed between them, and where the program spent the most time.

**Output:** Opens at `localhost:4000` — an interactive D3.js force graph. Clicking any node shows its narration. Bottlenecks are highlighted.

**Example terminal output:**
```
Nodes:    12 functions mapped
Hot path: load_data → clean → normalize → train
Bottleneck detected: normalize() called 4,200 times
          — 67% of total runtime spent here
Unused:   helper_backup() was never called
```

---

## 7. Oracle Mode — The Insane Mode

Oracle is not a separate application. **Oracle is a mode inside Morpheus** — specifically the mode that removes the "Python only" limitation.

### One-Line Definition

> **Oracle is the mode inside Morpheus that removes the Python-only restriction and lets Morpheus watch, understand, and narrate ANY code in ANY programming language — explained the way a genius developer would actually talk about it.**

### The Core Problem Oracle Solves

Original Morpheus used Python's `sys.settrace` hook — which only exists in Python. This meant it was completely blind to:
- JavaScript / TypeScript
- C / C++
- Java
- Rust
- Go
- Shell scripts
- Any non-Python language

Oracle solves this by switching to a completely different approach.

### How Oracle Works

**Step 1: Tree-sitter — the universal code reader**

Tree-sitter is a free, open-source parser that reads and understands the structure of 40+ programming languages. It converts any code file into an AST (Abstract Syntax Tree) — a structural map of what the code means — regardless of language. This is Oracle's eyes.

**Step 2: Language-specific runtime bridges**

For each language, Oracle uses the appropriate tracing tool:
- Python → `sys.settrace` (built-in)
- Node.js / JavaScript → V8 Inspector Protocol
- Java → JVMTI agent
- C / C++ → GDB's Python API
- Rust → LLDB scripting

Oracle wraps all of these behind one unified interface. **One command, any language.**

**Step 3: The Genius Narrator**

The local LLM doesn't just describe what happened — it reasons like a senior developer. It connects patterns across the entire execution, notices architectural problems, and narrates with opinions: *"this approach works but will break at scale because..."*

**Step 4: Personality Engine**

Oracle lets you choose the style of the narrator. Same execution, four completely different genius-level explanations:

| Personality | Style |
|---|---|
| The Mentor | Constructive, educational, points out one improvement at the end |
| The Critic | Direct, no-nonsense, calls out every problem immediately |
| The Paranoid | Security-focused, flags every potential vulnerability |
| The Teacher | Pauses and asks you questions — turns narration into learning |

### Example — The Critic narrating JavaScript

```bash
morpheus run app.js --mode oracle --personality critic
```

```
[0.04s] [Critic] validateUser() — works, but bcrypt.compare() is running
        synchronously. Under any real load this blocks the entire event loop.
        Classic mistake.

[0.07s] [Critic] ⚠ fetchUserData() — zero error handling on the DB call.
        What happens when the DB is down? Silence. Your app just dies quietly.

[0.09s] [Critic] Route returned 200. Works. Barely.
```

### Stats

- **40+ languages** supported via tree-sitter
- **4 genius narrator personalities**
- **₹0 cost** — fully local, forever free

---

## 8. The ML Brain

The evolved Morpheus integrates a machine learning core that transforms it from a narration tool into a living, learning intelligence system.

### ML Module 1: Execution Pattern Recognition

**Algorithm:** Isolation Forest / LSTM Autoencoder

After 50 runs of a project, Morpheus has learned what "normal" looks like for that specific codebase. When run 51 deviates — a function taking 3x longer, a variable hitting an unusual value — it flags it immediately.

Not because it was programmed with rules. **Because it learned what normal is.**

---

### ML Module 2: Crash Prediction Before You Run

**Algorithm:** Random Forest Classifier on trace features

Morpheus learns which execution patterns historically led to crashes across all its runs. When it sees the same pattern building up — before the crash happens — it warns the user:

> *"This looks like the pattern from 3 weeks ago that caused a memory overflow."*

Time machine meets fortune teller.

---

### ML Module 3: Personal Coding Pattern Profiler

**Algorithm:** Clustering on per-user trace history

Morpheus builds a profile of how YOU specifically code. Your common mistakes. The functions you always forget to handle errors in. The loops you always write inefficiently.

After a month of use, it knows your weaknesses better than you do — and tells you when you are repeating them.

---

### ML Module 4: Concept Writer — Writes the Idea and Architecture

**Algorithm:** NLP + Execution Graph Embedding

This is the most powerful ML feature. After watching your code run many times, the ML layer does not just narrate the steps. It **infers the architectural intent** and writes a **living concept document** for your codebase automatically:

> *"This module is acting as a rate limiter, not just a timer."*
> *"This class behaves like a state machine with 4 distinct states."*

**Your codebase explains itself — not from reading the files, but from watching the behavior.** No developer has to write documentation ever again. Morpheus writes it from execution.

---

### ML Module 5: Performance Degradation Detector

**Algorithm:** Time-series Anomaly Detection

Run your app every day. Morpheus tracks how long each function takes across every run. The moment a function starts getting slower over time — even by milliseconds — it alerts you with a trend graph:

> *"login() has been getting 12% slower each week for the past month."*

No other tool does this passively.

---

### ML Module 6: Codebase DNA Fingerprint

**Algorithm:** Cosine Similarity on Execution Embeddings

Over time, Morpheus builds a unique fingerprint of your project — its execution personality. When you add new AI-generated code, Morpheus compares the new code's behavior fingerprint against your project's DNA:

> *"This module doesn't match your project's patterns. It behaves like a foreign object."*

This is how Morpheus tells you when vibe-coded additions don't actually belong in your codebase — not by reading them, but by watching them execute.

---

## 9. The 5 Generations of Morpheus

Morpheus is designed to evolve. Each generation is smarter than the last — not by manual feature addition, but by the ML layer learning from real-world usage.

### Generation 1 — The Narrator (v1, Week 12)
What it does: Watches execution, narrates in plain English, stores run history in SQLite.

This is what gets built and published. Simple, useful, real. This is the foundation everything else stands on.

---

### Generation 2 — The Memory (v2, Month 6)
What it does: Remembers every run. Compares current behavior to past behavior. Detects when something changed even if the code didn't.

The ML anomaly detection layer goes live. Users start saying: *"It caught something I never would have noticed."*

---

### Generation 3 — The Predictor (v3, Month 10)
What it does: Has seen thousands of execution patterns across all users (anonymously, privately). Predicts crashes before they happen with real accuracy. The concept writer goes live — auto-generates documentation from execution behavior.

---

### Generation 4 — The Profiler (v4, Year 2)
What it does: Has built a personal coding profile for each user. Knows their patterns, mistakes, and strengths. Adapts narration style to match the user's level. A beginner and a senior developer get completely different explanations of the same execution — automatically.

---

### Generation 5 — The Guardian (v5, Year 3)
What it does: No longer a tool you run. A permanent layer in your development environment. Watches every file save, every test run, every execution — and builds a continuous living understanding of your entire project.

**At this point it is not a tool anymore. It is infrastructure.**

---

## 10. Who Uses Morpheus

Morpheus is NOT only for vibe coders. The vibe coder audience is the loudest and most obvious — but the real market is much broader.

| User Type | Their Pain | How Morpheus Helps |
|---|---|---|
| Vibe coders | AI wrote their code, they understand none of it | Narrator + ML brain explains everything live |
| CS students | Running algorithms they half-understand | Teaching mode turns execution into interactive learning |
| ML engineers | Training runs with zero visibility | Narrates the entire training loop — loss patterns, convergence signals, bottlenecks |
| Companies with legacy code | 50,000 lines nobody understands | Concept writer auto-generates living documentation from execution |
| Security researchers | Need to analyze unknown scripts behaviorally | Spy mode + ML = behavioral malware analyzer that catches what antivirus misses |
| Senior developers | No visibility into production runtime behavior | Searchable, narrated, historical execution record |
| Educators | Teaching programming concepts | Teaching mode + Oracle = interactive multi-language learning tool |

**Vibe coders will be the loudest fans.** They will share it, star it, and make it go viral. Everyone else makes it last.

---

## 11. Full Tech Stack — Everything Is Free

### Core Engine (Python)

| Tool | Purpose | Cost |
|---|---|---|
| Python `sys.settrace` | Runtime trace hook — watches every execution step | Free — built into Python |
| Python `ast` module | Parse code structure before running | Free — built into Python |
| `libcst` | Advanced AST parsing and code transformation | Free — open source |
| `tree-sitter` | Universal code parser — 40+ languages for Oracle | Free — open source |
| Ollama | Run local LLMs (Mistral, Llama 3, Phi-3) | Free — runs on your own machine |
| `scikit-learn` | ML algorithms — Isolation Forest, Random Forest, clustering | Free — open source |
| `SQLite` | Store run history permanently | Free — built into Python |
| `Rich` | Beautiful terminal output and streaming narration | Free — open source |
| `Typer` | CLI command framework | Free — open source |
| `watchdog` | File system watcher for daemon mode | Free — open source |
| `GitPython` | Read Git commit history for time travel mode | Free — open source |

### Dashboard (Web UI)

| Tool | Purpose | Cost |
|---|---|---|
| `FastAPI` | REST API backend connecting engine to dashboard | Free — open source |
| React + Vite | Frontend dashboard | Free — open source |
| D3.js | Interactive mind map / force graph visualization | Free — open source |

### Distribution & Publishing

| Tool | Purpose | Cost |
|---|---|---|
| GitHub | Host repository, issues, releases | Free for public repos |
| PyPI | `pip install morpheus-cli` | Free for open source |
| GitHub Actions | CI/CD — auto-test on every push | Free for public repos |

### Ollama — The Critical Free Component

Ollama is the tool that makes Morpheus's LLM narration completely free forever. It runs open-weight models locally:
- **Mistral 7B** — fast, capable, good for narration
- **Llama 3 8B** — strong reasoning
- **Phi-3 Mini** — very fast, good for lower-spec machines

**Installation on Windows:**
```bash
# Download from ollama.com — free, one-time install
# Then pull a model:
ollama pull mistral
```

No API key. No billing. No internet needed after download. Runs on CPU (slower) or GPU (faster). Madhesh's existing Windows machine handles this with no additional cost.

---

## 12. Complete Folder Structure

```
morpheus/                          ← Root repo (GitHub)
│
├── README.md                      ← Public face — what GitHub visitors see first
├── CONTRIBUTING.md                ← How others contribute to the project
├── LICENSE                        ← MIT license
├── pyproject.toml                 ← pip package configuration
├── .gitignore
├── .env.template                  ← Environment variable template
│
├── .github/                       ← GitHub configuration
│   ├── FUNDING.yml                ← GitHub Sponsors config
│   └── workflows/
│       ├── ci.yml                 ← CI: lint + test on push
│       └── publish.yml            ← Auto-publish to PyPI on tags
│
├── docs/                          ← All planning and technical documentation
│   ├── README.md                  ← Documentation index
│   ├── PROJECT.md                 ← This file — the complete project bible
│   ├── SUMMARY.md                 ← Onboarding guide
│   ├── SETUP.md                   ← Environment setup instructions
│   ├── ARCHITECTURE.md            ← Code blueprint — function signatures
│   ├── TASKS.md                   ← Sprint board — who does what, current week
│   ├── FRONTEND.md                ← Dashboard UI specs for the React developer
│   ├── ORACLE.md                  ← Full Oracle mode specification
│   └── EVOLUTION.md               ← ML architecture specification
│
├── morpheus/                      ← Main Python package
│   ├── __init__.py                ← Version string
│   ├── cli.py                     ← All terminal commands (Typer)
│   ├── tracer.py                  ← sys.settrace engine — the core watcher
│   ├── compressor.py              ← Converts raw trace events into readable chapters
│   ├── narrator.py                ← Multi-provider LLM narration engine
│   ├── oracle.py                  ← Tree-sitter multi-language engine
│   ├── prophecy.py                ← Crash prediction and pattern detection
│   ├── spy.py                     ← Security scanner mode
│   ├── teacher.py                 ← Interactive teaching mode
│   ├── storage.py                 ← SQLite run history storage
│   ├── config.py                  ← Configuration management
│   ├── differ.py                  ← Time Travel diff engine
│   └── ml/
│       ├── __init__.py
│       ├── anomaly.py             ← Isolation Forest — execution anomaly detection
│       ├── predictor.py           ← Random Forest — crash prediction
│       ├── profiler.py            ← HDBSCAN user profiler
│       ├── concept_writer.py      ← Behavioral concept inference from execution
│       ├── fingerprint.py         ← Codebase DNA — execution embedding similarity
│       ├── execution_graph.py     ← networkx DiGraph builder + features
│       ├── gat_model.py           ← GAT model + MemoryBank
│       ├── degradation.py         ← Performance degradation analysis
│       └── static_analyzer.py     ← Tree-sitter static code analysis
│
├── dashboard/                     ← React web UI (optional visual layer)
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── MindMap.jsx            ← D3.js force graph component
│       ├── RunHistory.jsx         ← List of all past runs with narration logs
│       └── SpyReport.jsx          ← Security scan report viewer
│
├── api/                           ← FastAPI backend serving the dashboard
│   ├── __init__.py
│   ├── server.py
│   └── routes/
│       └── __init__.py            ← 6 REST endpoints
│
├── examples/                      ← Test scripts for development
│   ├── simple.py
│   ├── simple.js
│   ├── simple.c
│   ├── ml_train.py
│   ├── will_crash.py
│   ├── safe_script.py
│   └── malware_sim.py
│
└── tests/                         ← 193 pytest tests
    ├── conftest.py
    ├── test_tracer.py
    ├── test_compressor.py
    ├── test_narrator.py
    ├── test_storage.py
    ├── test_prophecy.py
    ├── test_spy.py
    ├── test_teacher.py
    ├── test_oracle.py
    ├── test_cli.py
    ├── test_differ.py
    ├── test_integration.py
    ├── test_ml.py
    ├── test_mock_llm.py
    ├── test_concept_writer.py
    ├── test_degradation.py
    ├── test_execution_graph.py
    ├── test_gat_model.py
    ├── test_profiler.py
    └── test_static_analyzer.py
```

---

## 13. Team Documentation Files

These five files are what employees read to understand and contribute to Morpheus. Every team member must read them before writing a single line of code.

### docs/PROJECT.md (This file)
**The constitution of Morpheus.** Everything about the project — vision, architecture, all modes, ML brain, evolution roadmap. Anyone who reads this should be able to explain Morpheus to a stranger in 5 minutes.

### docs/TASKS.md
**The live sprint board.** Updated every week by Madhesh.

Contains:
- Current week's tasks broken by module
- Who owns what task
- Status column: Not started / In progress / Done / Blocked
- Backlog of future tasks
- Decisions log — why X was chosen over Y

### docs/FRONTEND.md
**For whoever builds the React dashboard.** Contains:
- Every page and component listed with its purpose
- All API endpoints the frontend needs from FastAPI
- Mind Map visual specification — what nodes look like, what clicking does
- Design rules — colors, typography, layout decisions
- Responsive behavior requirements

### docs/ORACLE.md
**Full specification for Oracle insane mode.** Contains:
- Tree-sitter integration guide per language
- Runtime bridge specs — V8 inspector, GDB Python API, JVMTI
- Personality engine prompts for all 4 narrator personalities
- Priority language support order (JavaScript first, then C, then Java)
- Testing strategy for multi-language execution

### README.md (Root — public)
**The public face of the project.** Contains:
- One punchy line that defines Morpheus
- Demo GIF at the very top (most important — this is what people share)
- Install + quickstart in under 5 lines
- All modes listed with one-line descriptions
- Link to CONTRIBUTING.md
- GitHub Sponsors / Ko-fi badge

---

## 14. Build Roadmap — Week by Week to v1

### Week 1–2: Foundation

Tasks:
- Write `PROJECT.md` and `TASKS.md`
- Create GitHub repository with MIT license
- Set up `pyproject.toml` for pip packaging
- Build `cli.py` with Typer — define all commands (empty stubs for now)
- Build `tracer.py` — get `sys.settrace` working on a simple test script
- Print the raw trace to terminal — ugly but working
- Install and test Ollama locally with Mistral 7B

Goal: Running `morpheus run test.py` produces any output, even raw trace data.

---

### Week 3–4: Core Engine

Tasks:
- Build `compressor.py` — group raw trace events into meaningful chapters
- Integrate Ollama in `narrator.py` — send chapters, receive narration
- Stream narration live to terminal using Rich
- Store each run in SQLite via `storage.py`
- Test on 5 different real Python scripts (ML training, web scraping, file processing, sorting algorithm, data analysis)

Goal: `morpheus run train_model.py` produces readable, accurate English narration.

---

### Week 5–6: More Modes

Tasks:
- Build `prophecy.py` — pattern detection before crashes
- Build diff logic for Time Travel mode
- Build `spy.py` — flag sensitive file and network access
- Add `--mode` flag to CLI for switching between modes
- Build `teacher.py` — pause-and-question interactive mode
- Write unit tests in `tests/`

Goal: All 6 modes work end-to-end on Python files.

---

### Week 7–8: Oracle Mode

Tasks:
- Install tree-sitter, configure language parsers
- Build `oracle.py` — JavaScript support first (largest vibe coder audience)
- Add V8 Inspector Protocol bridge for Node.js runtime tracing
- Build personality engine — implement all 4 narrator styles in prompts
- Test Oracle thoroughly on JS projects
- Expand to one additional language (C or Java)

Goal: `morpheus run app.js --mode oracle --personality critic` works correctly.

---

### Week 9–10: Dashboard

Tasks:
- Write `FRONTEND.md` specification in full
- Build `api/server.py` FastAPI — endpoints for run history, narration logs, mind map data
- Build React dashboard — run list + narration log viewer
- Build `MindMap.jsx` — D3.js interactive force graph
- `morpheus map` command automatically opens browser to `localhost:4000`

Goal: Full dashboard loads, shows run history, mind map renders correctly.

---

### Week 11–12: Ship v1

Tasks:
- Record demo GIF showing Morpheus narrating a real Python script (this is the most important marketing asset)
- Write `README.md` — punchy, clean, demo GIF at the top
- Publish to PyPI — `pip install morpheus-cli` must work globally
- Set up GitHub Actions CI — auto-run tests on every push
- Enable GitHub Sponsors
- Post on GitHub, Dev.to, Hacker News Show HN, and LinkedIn
- Tag `v1.0.0` — Morpheus is live

---

## 15. Distribution

### How People Get Morpheus

There are three ways users can get Morpheus. All are free.

**Method 1 — pip (primary)**
```bash
pip install morpheus-cli
```
Published to PyPI (Python Package Index). Free for open source packages. Works on Windows, Mac, and Linux.

**Method 2 — GitHub**
```bash
git clone https://github.com/madhesh-y/morpheus
cd morpheus
pip install -e .
```
For users who want to contribute or run the latest dev version.

**Method 3 — Windows installer (future)**
Build a `.exe` installer using PyInstaller (free tool). Users download, double-click, done. For non-technical users.

### No Hosting Required

Morpheus requires **zero servers**. The only "infrastructure" is:
- GitHub repository — free forever for public open source
- PyPI package listing — free forever for open source
- Ollama models run on the user's machine — zero cloud cost

---

## 16. Revenue Paths

Morpheus is free and open source forever. But free does not mean zero income.

### Phase 1 — Ship It (Month 1–3)

**GitHub Sponsors**
Enable the Sponsor button in GitHub settings. Add a `FUNDING.yml` file. Developers and companies who use Morpheus can pay monthly voluntarily.
*Realistic: ₹500–5,000/month once established.*

**Ko-fi**
One link in the README: "If Morpheus saved you time, buy me a coffee." Sign up at ko-fi.com — free, they take a small percentage only when you earn.
*Realistic: ₹200–3,000/month.*

---

### Phase 2 — Grow It (Month 4–6)

**Technical Blog Posts**
Write on Dev.to, Hashnode, or Medium about building Morpheus. "How I built a tool that makes Python explain itself." These get thousands of reads and drive GitHub stars. Dev.to and Hashnode pay per view. Write once, earn forever.

**YouTube — Build in Public**
Record building Morpheus week by week. "Building an open source tool that reads your code's mind — Week 3." YouTube monetization at 1,000 subscribers + 4,000 watch hours. Phone camera is enough to start.
*Realistic at scale: ₹5,000–50,000/month.*

**Morpheus Pro — Paid Tier**
Keep the core tool 100% free and open source. Build a Pro version with:
- VS Code extension
- Cloud-synced run history (team feature)
- Team dashboard for multiple developers
- Priority support

Use Gumroad or Lemon Squeezy for payments — free to set up. Charge ₹299/month.
*50 paying users = ₹15,000/month.*

---

### Phase 3 — Scale It (Year 2+)

**Enterprise Support Contracts**
When a company uses Morpheus internally, they often want guaranteed support, custom features, or integration help. One enterprise contract can pay more than 1,000 individual sponsors combined.

**Job Offers and Internships Find You**
A GitHub repo with 500+ stars gets noticed by recruiters. Morpheus on your portfolio = instant credibility at interviews. This is the biggest return of all — it changes your entire career trajectory.

---

### The Honest Timeline

| Period | Earnings | What's happening |
|---|---|---|
| Month 1–3 | ₹0 | Building and shipping. Foundation only. |
| Month 4–6 | ₹500–5,000/month | First stars, first blog post, first Ko-fi donations. |
| Month 7–12 | ₹10,000–30,000/month | YouTube growing, Pro tier live, sponsors increasing. |
| Year 2+ | ₹50,000–2,00,000/month | Consistent effort, enterprise clients, strong portfolio. |

**Total cost to run Morpheus: ₹0. Always.**

---

## 17. The Honest Reality — Limitations and Strengths

Every great project needs honest documentation of both.

### Genuine Strengths

1. **No other tool watches live execution and narrates it** — this gap is real and permanent.
2. **Execution history is irreplaceable** — you cannot paste a running program into Claude.
3. **ML layer gets smarter with every run** — the more it's used, the better it becomes.
4. **Completely free stack** — zero cost to build, run, distribute, and maintain.
5. **The demo is viral** — watching code narrate itself is visually stunning and shareable.
6. **Oracle makes it universal** — any language means any developer on Earth.
7. **Concept writer creates documentation from execution** — no developer writes docs ever again.

### Real Limitations (be honest with employees)

1. **When AI-generated code works perfectly**, Morpheus adds less value in that moment. For the happy path, a vibe coder who just wants to run code doesn't need it.
2. **Ollama requires a capable machine** — low-spec computers may run the LLM slowly. This is a hardware dependency.
3. **Oracle runtime bridges are complex** — the V8 Inspector Protocol and GDB Python API are non-trivial to build. This is the hardest engineering challenge in the project.
4. **First 3 months produce ₹0** — this is a long-term investment, not a quick income.

### The Right Framing

Morpheus is not "for vibe coders." That is the loudest early audience. The correct framing is:

> **Morpheus is for anyone whose code runs and doesn't explain itself. Which is every developer on Earth.**

---

## 18. Identity

### What Morpheus Actually Is — Final Answer

Morpheus is a **self-evolving execution intelligence system**. It starts as a tool that explains running code in plain English. It grows into an ML-powered guardian that learns your codebase, predicts your problems, profiles your patterns, and evolves with every single run — for every single user. It is not for one type of developer. It is for anyone whose code runs and doesn't explain itself.

### The README Headline

> *"AI wrote your code. Morpheus explains what it's actually doing."*

### The One-Line That Defines Everything

> **Every other tool reads what your code says. Morpheus remembers what your code did — and learns from it forever.**

---

*Document created by Madhesh Y — Morpheus Project Lead*  
*For internal team use. Do not distribute outside the project.*
