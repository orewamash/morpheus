# MORPHEUS — SUMMARY & ONBOARDING GUIDE
### Everything You Need to Know in One Read
**For:** New team members, contributors, collaborators  
**Read time:** 15–20 minutes  
**After reading this:** Read `PROJECT.md` for the complete technical deep-dive

---

## START HERE — What Is Morpheus in One Line?

> **Every other tool reads what your code says. Morpheus remembers what your code did — and learns from it forever.**

---

## The Story of Why Morpheus Exists

### The World in 2026

AI tools — Claude, Cursor, GitHub Copilot — can write hundreds of lines of code from a single prompt. This created a new kind of developer called a **vibe coder**. A vibe coder prompts AI, runs the code, it works (sometimes), and has absolutely no idea why. The moment it breaks — they are lost.

This is millions of developers globally right now.

### What Every Existing Tool Does

Claude, Cursor, Copilot, ChatGPT — all of them do the same thing: they read the code file and explain what it says. They explain dead code. Static text sitting in a file.

**None of them can tell you what the code actually did when it ran.**

### What Morpheus Does Instead

Morpheus watches live execution. It sits inside a running program and observes every step — every function call, every variable change, every branch decision — and narrates it in plain English, in real time, as it happens.

The best way to understand this:

> **Claude explains the recipe. Morpheus watches the cooking.**

You can read a biryani recipe perfectly and still not know the chef added too much salt at step 7 on Tuesday. The recipe didn't change. But what happened in the kitchen was different.

---

## What Type of Software Is This?

**Morpheus is a CLI tool with an optional local web dashboard.**

| What it is NOT | What it IS |
|---|---|
| Not a website | A command-line tool — like Git or pip |
| Not a mobile app | Installed once via `pip install morpheus-cli` |
| Not a browser extension | Runs in PowerShell / Terminal |
| Not an IDE | Opens a local dashboard at localhost:4000 |
| Not a cloud service | 100% offline — runs on your own machine |

### How a user installs and runs it

```bash
# Install once
pip install morpheus-cli

# Run any Python file
morpheus run mycode.py

# Run JavaScript (Oracle mode)
morpheus run app.js --mode oracle

# Security scan an unknown file
morpheus spy mystery_script.py
```

---

## The 6 Modes — Quick Reference

| Mode | Command | What it does |
|---|---|---|
| **Narrator** | `morpheus run file.py` | Explains every step as the program runs — live, in plain English |
| **Time Travel** | `morpheus diff run1.log run2.log` | Runs the same program twice, finds exactly where the two paths diverged |
| **Prophecy** | `--mode prophecy` | Detects crash patterns BEFORE the program actually crashes |
| **Spy** | `morpheus spy file.py` | Security scans any unknown script — flags file access, network calls, data exfiltration |
| **Teaching** | `--mode teach` | Pauses during execution and asks the user quiz questions — interactive learning |
| **Mind Map** | `morpheus map file.py --browser` | Builds a live visual graph of how functions called each other and where time was spent |

### The one mode nobody else has: Prophecy

Every debugger on Earth tells you what broke **after** it breaks. Prophecy tells you what is **about to** break before it does. Like a doctor who reads your vitals and says "your blood pressure is climbing, you'll have a problem in 3 minutes" — not "you had a heart attack, here's what happened."

---

## Oracle — The Insane Mode

Original Morpheus only worked on Python. Oracle removes that limitation entirely.

**Oracle in one line:**
> Oracle is the mode inside Morpheus that lets it watch, understand, and narrate ANY code in ANY programming language.

### How Oracle works

- Uses **tree-sitter** (free, open source) — a universal parser that understands 40+ languages
- Connects to language-specific runtime bridges:
  - JavaScript → V8 Inspector Protocol
  - C/C++ → GDB Python API
  - Java → JVMTI agent
- All of this is wrapped behind one command — `--mode oracle`

### The Personality Engine

Oracle lets you choose how the genius narrator explains the code:

| Personality | Flag | What it sounds like |
|---|---|---|
| The Mentor | `--personality mentor` | Educational, constructive, notes one improvement at the end |
| The Critic | `--personality critic` | Direct, calls out every problem immediately |
| The Paranoid | `--personality paranoid` | Security-focused, flags every vulnerability |
| The Teacher | `--personality teacher` | Pauses and asks you questions during execution |

Same code. Four completely different perspectives. The demo of switching personalities on live code is what makes people share the project.

---

## The ML Brain — How Morpheus Evolves

This is what separates Morpheus from a simple narration tool. The ML layer makes it a **living, learning system**.

### 6 ML Modules

**1. Execution Pattern Recognition** *(Isolation Forest)*
After 50 runs of your project, Morpheus learns what "normal" looks like. When something deviates — it flags it. Not from rules. From learning.

**2. Crash Prediction** *(Random Forest Classifier)*
Learns which execution patterns historically led to crashes. Warns you when it sees the same pattern forming again — before the crash.

**3. Personal Coding Profiler** *(Clustering)*
Builds a profile of your specific coding patterns, common mistakes, and weak spots. Tells you when you're repeating them.

**4. Concept Writer** *(NLP + Execution Graph Embedding)*
The most powerful feature. After watching code run many times, the ML layer infers the architectural intent and auto-generates a living concept document:
> *"This module is acting as a rate limiter, not just a timer."*

**No developer has to write documentation ever again. Morpheus writes it from execution.**

**5. Performance Degradation Detector** *(Time-series Anomaly Detection)*
Tracks function execution time across every run. Alerts when a function is getting slower week over week — passively, automatically.

**6. Codebase DNA Fingerprint** *(Cosine Similarity on Execution Embeddings)*
Builds an execution personality for your project. When you add new AI-generated code, it tells you if the new code behaves like it belongs — or like a foreign object.

---

## The 5 Generations

Morpheus is not built once and frozen. It evolves.

| Generation | Name | When | What changes |
|---|---|---|---|
| Gen 1 | The Narrator | v1 — Week 12 | Narrates execution, stores history. Ship this first. |
| Gen 2 | The Memory | v2 — Month 6 | Anomaly detection live. Compares current vs past behavior. |
| Gen 3 | The Predictor | v3 — Month 10 | Crash prediction + concept writer live. |
| Gen 4 | The Profiler | v4 — Year 2 | Personal coding profile per user. Adaptive narration by skill level. |
| Gen 5 | The Guardian | v5 — Year 3 | Permanent layer in your dev environment. Not a tool — infrastructure. |

---

## Who Uses This?

**Primary audience (makes it go viral):** Vibe coders — they have the most pain and will share it the loudest.

**Full audience (makes it last):**

- **CS students** — Teaching mode turns execution into interactive learning
- **ML engineers** — Training loop narration, convergence signals, bottleneck detection
- **Companies with legacy code** — Concept writer auto-documents 50,000 lines nobody understands
- **Security researchers** — Spy mode = behavioral malware analysis
- **Senior developers** — Searchable execution history for production debugging
- **Educators** — Universities could adopt Teaching + Oracle as a classroom tool

---

## The Complete Free Stack

**Nothing in this project costs money — ever.**

| Component | Tool | Why free |
|---|---|---|
| Runtime tracer | Python `sys.settrace` | Built into Python |
| AST parser | Python `ast`, `libcst` | Open source |
| Universal language parser | `tree-sitter` | Open source |
| Local LLM | Ollama + Mistral 7B | Free, runs locally |
| ML algorithms | `scikit-learn` | Open source |
| Database | SQLite | Built into Python |
| Terminal UI | Rich | Open source |
| CLI framework | Typer | Open source |
| Web API | FastAPI | Open source |
| Frontend | React + Vite | Open source |
| Data visualization | D3.js | Open source |
| Repository | GitHub | Free for public repos |
| Package distribution | PyPI | Free for open source |
| CI/CD | GitHub Actions | Free for public repos |

---

## The Folder Structure (Quick Reference)

```
morpheus/
├── README.md                 ← Public face
├── docs/
│   ├── PROJECT.md            ← Full technical bible (read this second)
│   ├── TASKS.md              ← Sprint board — check this every week
│   ├── FRONTEND.md           ← Dashboard specs
│   └── ORACLE.md             ← Oracle mode full spec
├── morpheus/                 ← Python package
│   ├── cli.py                ← Commands
│   ├── tracer.py             ← Core watcher (sys.settrace)
│   ├── compressor.py         ← Trace → chapters
│   ├── narrator.py           ← Chapters → Ollama → narration
│   ├── oracle.py             ← Multi-language engine
│   ├── prophecy.py           ← Crash prediction
│   ├── spy.py                ← Security scanner
│   ├── ml/                   ← All ML modules
│   └── storage.py            ← SQLite history
├── dashboard/                ← React web UI
└── api/server.py             ← FastAPI backend
```

---

## The Build Roadmap (12 Weeks to v1)

| Weeks | Focus | Deliverable |
|---|---|---|
| 1–2 | Foundation | sys.settrace working, CLI stubs, Ollama installed |
| 3–4 | Core engine | Full narration streaming in terminal, SQLite storage |
| 5–6 | More modes | Prophecy, Time Travel, Spy, Teaching all working |
| 7–8 | Oracle | JavaScript support + personality engine |
| 9–10 | Dashboard | FastAPI + React + D3 mind map live |
| 11–12 | Ship | Demo GIF, README, PyPI publish, public announcement |

---

## How People Earn From This

The tool is free. The income is not.

| Method | When | Realistic earning |
|---|---|---|
| GitHub Sponsors + Ko-fi | Month 1 — set up immediately | ₹500–5,000/month |
| Blog posts (Dev.to, Hashnode) | Month 4 onwards | Passive view income + GitHub stars |
| YouTube — build in public | Month 3 onwards | ₹5,000–50,000/month at scale |
| Morpheus Pro (paid tier) | Month 6 | ₹299/month per user |
| Enterprise support contracts | Year 2+ | ₹50,000–2,00,000/month |
| Career value — job offers | Ongoing | Recruiters find you from your GitHub |

**Total cost to run this business: ₹0.**

---

## The Honest Limitations

These must be understood before joining the project:

1. **Month 1–3 earns ₹0.** This is a long-term investment.
2. **When AI code works perfectly**, Morpheus adds less value. It shines when things break or need understanding.
3. **Ollama needs a capable machine.** Low-spec computers will run slowly.
4. **Oracle runtime bridges are the hardest engineering challenge.** V8 Inspector Protocol and GDB Python API are complex.

---

## Questions New Team Members Ask

**Q: Is this a web app we host online?**
No. It runs entirely on the user's machine. Zero servers. Zero hosting cost.

**Q: Does it need internet?**
No. After installing Morpheus and downloading the Ollama model once, it works fully offline forever.

**Q: Can't Claude or ChatGPT do the same thing?**
No. Claude reads static files. Morpheus watches live execution. You cannot paste a running program into Claude. Morpheus was there when it ran — Claude was not.

**Q: Is it only for Python?**
No. Oracle mode supports 40+ languages via tree-sitter. Python is just the first supported language.

**Q: Is it only for vibe coders?**
No. That is the loudest early audience. The real market is every developer who runs code and wants to understand it, predict problems, or audit behavior.

**Q: What should I read first?**
This file first. Then `PROJECT.md` for the complete technical details. Then `TASKS.md` for your assigned work.

---

## The Identity of This Project

**The README headline:**
> *"AI wrote your code. Morpheus explains what it's actually doing."*

**The one-liner that defines everything:**
> *"Every other tool reads what your code says. Morpheus remembers what your code did — and learns from it forever."*

**What Morpheus is at its largest scale:**
Not a tool. A self-evolving execution intelligence system. A permanent guardian layer in your development environment that knows your codebase better than you do.

---

*This is Morpheus. Welcome to the team.*

*For the complete technical spec, read `PROJECT.md`.*  
*For your current tasks, read `TASKS.md`.*  
*Questions? Raise a GitHub issue or ping the project lead.*

---

*Summary document created by Madhesh Y — Morpheus Project Lead*
