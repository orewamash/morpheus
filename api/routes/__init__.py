from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import os
from morpheus.spy import scan_file, format_spy_report
from morpheus.storage import MorpheusStorage, RunRecord

app = FastAPI(
    title="Morpheus API",
    description="Backend API for the Morpheus execution intelligence dashboard",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _run_to_dict(r: RunRecord) -> dict:
    return {
        "run_id": r.run_id,
        "filepath": r.filepath,
        "timestamp": r.timestamp,
        "mode": r.mode,
        "chapters": json.loads(r.chapters) if r.chapters else [],
        "narrations": json.loads(r.narrations) if r.narrations else [],
        "duration_ms": r.duration_ms,
        "event_count": r.event_count,
        "error": r.error,
    }


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "morpheus-api"}


@app.get("/api/runs")
def list_runs(limit: int = 20):
    storage = MorpheusStorage()
    try:
        runs = storage.list_runs(limit=limit)
        return {"runs": [_run_to_dict(r) for r in runs], "count": len(runs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/runs/{run_id}")
def get_run(run_id: str):
    storage = MorpheusStorage()
    try:
        record = storage.get_run(run_id)
        return _run_to_dict(record)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/runs/{run_id}")
def delete_run(run_id: str):
    storage = MorpheusStorage()
    try:
        deleted = storage.delete_run(run_id)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
        return {"status": "deleted", "run_id": run_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/runs/{run_id}/mindmap")
def get_mindmap(run_id: str):
    storage = MorpheusStorage()
    try:
        record = storage.get_run(run_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    chapters = json.loads(record.chapters) if record.chapters else []

    nodes = []
    edges = []
    for i, ch in enumerate(chapters):
        title = ch.get("title", f"Chapter {i + 1}")
        func_name = title.split(": ")[-1].rstrip("()") if ": " in title else "unknown"
        nodes.append({
            "id": f"func_{i}",
            "label": func_name,
            "title": title,
            "event_count": ch.get("event_count", 0),
        })
        if i > 0:
            edges.append({
                "source": f"func_{i - 1}",
                "target": f"func_{i}",
                "label": "calls",
            })

    return {"nodes": nodes, "edges": edges}


@app.get("/api/spy")
def spy_scan(file: str):
    if not os.path.isfile(file):
        raise HTTPException(status_code=400, detail=f"File not found: {file}")
    try:
        events = scan_file(file)
        report = format_spy_report(events, file)
        return {"file": file, "events": len(events), "report": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


dist_dir = Path(__file__).resolve().parent.parent.parent / "dashboard" / "dist"
if dist_dir.exists():
    app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="static")

