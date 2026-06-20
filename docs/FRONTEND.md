# Morpheus Frontend — Dashboard Specification

## Stack

- **Vite 5** — build tool and dev server
- **React 18** — UI framework
- **D3 7** — force-directed graph for mind map visualization
- **FastAPI** — backend API (port 4000)

## Quick Start

```bash
# Terminal 1: Start the API server
cd api
pip install -e ".[api]"
python server.py

# Terminal 2: Start the dev server
cd dashboard
npm install
npm run dev
```

Open http://localhost:5173 in a browser.

## Pages / Components

### 1. RunHistory (`src/RunHistory.jsx`)
- Fetches `GET /api/runs?limit=50`
- Displays a table with columns: File, Mode, Events, Duration, Timestamp, Status
- Each row links to the mind map for that run

### 2. MindMap (`src/MindMap.jsx`)
- Fetches `GET /api/runs/{run_id}/mindmap`
- Renders a D3 force-directed graph
- Node size = event count, edges = call relationships
- Draggable and zoomable

### 3. SpyReport (`src/SpyReport.jsx`)
- Input field for file path
- Scan button calls `POST /api/spy`
- Displays formatted security report

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | Health check |
| GET | `/api/runs` | List recent runs |
| GET | `/api/runs/{id}` | Get run detail |
| DELETE | `/api/runs/{id}` | Delete a run |
| GET | `/api/runs/{id}/mindmap` | Mind map graph data |
| POST | `/api/spy` | Security scan a file |

## Build for Production

```bash
cd dashboard
npm run build
# Output in dashboard/dist/
```

Serve `dist/` with any static file server alongside the API.
