# Morpheus

A self-evolving execution intelligence system. Every other tool reads what your code says; Morpheus remembers what your code did.

## Features

- **Tracer Engine** — `sys.settrace` runner capturing call/return events with stdlib filtering
- **Trace Compressor** — Groups execution streams into semantic "chapters"
- **Narrator** — Local Ollama LLM integration for natural English narration
- **Oracle Mode** — Multi-language support (Python, JS/TS, C/C++, Java) with personality-driven analysis (mentor, critic, paranoid, teacher)
- **Time Travel Diff** — Compare two runs to see where execution diverged
- **Spy Mode** — Security scan scripts for sensitive operations (file access, network, system calls)
- **Teaching Mode** — Interactive Q&A session about code execution
- **Prophecy Mode** — Proactive warning detection (rapid calls, missing returns, large locals)
- **Execution Graph** — Build networkx DiGraph from trace events for structural analysis
- **GAT Model** — Graph Attention Network scaffold with MemoryBank for similarity search
- **ML Engine** — Anomaly detection (Isolation Forest), crash prediction (RandomForest), execution fingerprints
- **API Server** — FastAPI backend with 6 REST endpoints (port 4000)
- **React Dashboard** — Vite + React SPA with D3 mind map and run history

## Installation

```bash
git clone https://github.com/yourusername/morpheus.git
cd morpheus
pip install -e ".[dev,api]"
```

## Usage

```bash
# Run execution narration
morpheus run examples/simple.py

# Prophecy mode — analyze warnings
morpheus run examples/simple.py --mode prophecy

# Security scan
morpheus spy examples/malware_sim.py

# Compare two runs
morpheus diff <run-id-1> <run-id-2>

# Teaching mode
morpheus run examples/simple.py --mode teach

# Oracle mode with personalities
morpheus run examples/simple.js --mode oracle --personality critic
```

## Dashboard

```bash
cd api && python server.py     # Start API (port 4000)
cd dashboard && npm run dev    # Start React app
```

## Testing

```bash
pytest tests/ -v    # 102 tests
```

## Architecture

```
morpheus/
├── tracer.py        — TraceEvent + MorpheusTracer + trace_file()
├── compressor.py    — ExecutionChapter + compress_trace()
├── narrator.py      — OllamaClient + stream_narration()
├── cli.py           — Typer CLI (run/spy/map/diff)
├── differ.py        — Time Travel diff
├── storage.py       — SQLite run history
├── prophecy.py      — Warning pattern detectors
├── spy.py           — Security scanner
├── teacher.py       — Interactive teaching
├── oracle.py        — Multi-language + personality engine
└── ml/
    ├── anomaly.py       — Isolation Forest anomaly detection
    ├── predictor.py     — RandomForest crash prediction
    ├── profiler.py      — Per-function execution profiling
    ├── concept_writer.py — Behavioral concept inference
    ├── fingerprint.py   — Execution fingerprinting + comparison
    ├── execution_graph.py — networkx DiGraph builder + features
    └── gat_model.py      — GAT model + MemoryBank
api/
├── server.py         — FastAPI entry point (port 4000)
└── routes/__init__.py — 6 REST endpoints
dashboard/             — Vite + React SPA
```
