# SoccerCV — Match Analysis Platform

Full-stack web application for soccer match video analysis. Upload match footage, run the AI analysis pipeline, and view tactical reports with SVG pitch overlays, player stats, heatmaps, and AI-generated tactical briefs.

***

## Table of Contents

1. [Repositories](#repositories)
2. [Architecture Overview](#architecture-overview)
3. [Development Environment](#development-environment)
   * [Prerequisites](#prerequisites)
   * [First-Time Setup](#first-time-setup)
   * [Scenario A — Local dev (recommended)](#scenario-a--local-dev-recommended)
   * [Scenario B — Full container stack](#scenario-b--full-container-stack)
   * [Which scenario to use](#which-scenario-to-use)
   * [Health checks](#health-checks)
   * [Updating the Engine](#updating-the-engine)
   * [VS Code Workspace](#vs-code-workspace)
4. [Debugging](#debugging)
   * [Backend breakpoints](#backend-breakpoints)
   * [Frontend state breakpoints](#frontend-state-breakpoints)
   * [Container debugging](#container-debugging)
5. [Configuration](#configuration)
6. [Database](#database)
7. [Container Deployment](#container-deployment)
8. [Project Structure](#project-structure)
9. [Pages and Routes](#pages-and-routes)
10. [API Reference](#api-reference)
11. [Pipeline Flow](#pipeline-flow)
12. [Design System](#design-system)

***

## Repositories

| Repo                                   | Purpose                                                    | Access          |
| -------------------------------------- | ---------------------------------------------------------- | --------------- |
| `github.com/pmCrawler/soccer_analysis` | Web app — frontend (Reflex) + backend API (FastAPI)        | Broader team    |
| `github.com/pmCrawler/soccercv`        | Analysis engine — CV pipeline, YOLO, tactics, AI reporting | Restricted (IP) |

The engine is embedded as a **git submodule** at `soccercv_engine/`. Cloning with `--recurse-submodules` pulls both repos in one step. Anyone without access to the engine repo gets an empty `soccercv_engine/` directory — they can still work on the frontend and API code but cannot run the analysis pipeline locally.

***

## Architecture Overview

```
┌─────────────────────────────────────────────┐
│  Browser                                    │
└───────────────────┬─────────────────────────┘
                    │ HTTP / WebSocket
┌───────────────────▼─────────────────────────┐
│  frontend  (Reflex :3000)                   │
│  Python → compiled React UI                 │
│  WebSocket state sync on :8000              │
└───────────────────┬─────────────────────────┘
                    │ REST + SSE
┌───────────────────▼─────────────────────────┐
│  backend  (FastAPI :8001)                   │
│  • Job lifecycle (create / status / cancel) │
│  • Spawns soccercv CLI as subprocesses      │
│  • Streams stdout progress via SSE          │
│  • Serves output files (video, heatmaps)    │
└────────┬──────────────────────┬─────────────┘
         │ SQLAlchemy async     │ subprocess
┌────────▼──────────┐  ┌────────▼───────────────┐
│  db               │  │  soccercv engine        │
│  PostgreSQL :5432 │  │  reads/writes           │
└───────────────────┘  │  /data/runs volume      │
                       └────────────────────────┘
```

**Key design decisions:**

* Frontend has no direct DB access — all data flows through the backend API
* Engine is invoked as a subprocess (not imported as a library) so the backend can stream stdout progress over SSE in real time
* Model weights (`yolov8n.pt`, `soccer_ball.pt`) are volume-mounted from `soccercv_engine/models/` — not baked into the image — so they update without a rebuild

***

## Development Environment

### Prerequisites

* Python 3.11+ (backend / engine) and 3.12+ (frontend)
* `uv` — fast Python package manager: `pip install uv`
* Podman — for the database container (`podman compose up db -d`)
* `ffmpeg` on PATH (used by the engine's preprocess step)

No local Postgres installation is needed — the database always runs in a container.

### First-Time Setup

```Shell
# 1. Clone app repo — --recurse-submodules also clones soccercv into soccercv_engine/
git clone --recurse-submodules https://github.com/pmCrawler/soccer_analysis.git
cd soccer_analysis

# 2. Install app Python dependencies (creates .venv automatically)
uv sync

# 3. Install the engine + its ML deps (torch, ultralytics, opencv) into the same venv
#    --extra-index-url needed because torch/torchvision come from the PyTorch CPU index
uv pip install -e soccercv_engine/ --extra-index-url https://download.pytorch.org/whl/cpu

# 4. Copy .env and fill in secrets
cp soccercv_engine/.env.example .env
# Edit .env: verify POSTGRES_* values, set ANTHROPIC_API_KEY

# 5. Start the database container and initialise schema
podman compose up db -d
sleep 5   # wait for postgres to be ready
alembic upgrade head
python -m backend.db.seed
```

### Scenario A — Local dev (recommended)

DB runs in a container (port 5432 exposed to localhost). Backend and frontend run directly on the host with hot-reload. Use this for all day-to-day development.

**Every session — two terminals:**

```Shell
# Terminal 1
uvicorn backend.main:app --reload --port 8001

# Terminal 2
reflex run
```

Open `http://localhost:3000`.

**With debug logging:**

```Shell
# Terminal 1 — verbose request logs + SQL (also flip echo=True in backend/db/session.py)
uvicorn backend.main:app --reload --port 8001 --log-level debug

# Terminal 2 — verbose Reflex compiler output
reflex run --log-level debug
```

**Stop the DB when done:**

```Shell
podman compose down          # stop, keep data
podman compose down -v       # stop and delete all data (pgdata volume)
```

### Scenario B — Full container stack

All three services run in containers. Use this to validate the compose setup, test the production container images, or demo the app without any host processes.

**First build and start:**

```Shell
# Submodule must be populated — backend image COPYs from soccercv_engine/
git submodule update --init --recursive

podman compose up --build

# In a second terminal — first time only
podman compose exec backend alembic upgrade head
podman compose exec backend python -m backend.db.seed
```

Open `http://localhost:3000`.

**Subsequent starts (images already built):**

```Shell
podman compose up
```

**Rebuild one service after code changes:**

```Shell
podman compose up --build backend    # rebuild + restart backend only
podman compose up --build frontend   # rebuild + restart frontend only
```

**View logs:**

```Shell
podman compose logs -f               # all services
podman compose logs -f backend       # backend only
```

**Stop:**

```Shell
podman compose down          # stop, keep data
podman compose down -v       # stop and delete all data
```

### Which scenario to use

| Situation                                       | Scenario                             |
| ----------------------------------------------- | ------------------------------------ |
| Writing code, iterating on UI or API            | **A** — hot-reload, instant feedback |
| Testing the container build                     | **B**                                |
| Validating compose.yml or Containerfile changes | **B**                                |
| Demoing the running app                         | **B**                                |

### Health checks

Once running (either scenario), verify each layer:

```Shell
curl http://localhost:8001/api/teams   # backend API responding
open http://localhost:8001/docs        # interactive API docs (Swagger UI)
open http://localhost:3000             # frontend
```

### Updating the Engine

```Shell
git -C soccercv_engine pull origin main
uv pip install -e soccercv_engine/ --extra-index-url https://download.pytorch.org/whl/cpu
git add soccercv_engine
git commit -m "bump engine to latest"
```

### VS Code Workspace

Open `soccercv-platform.code-workspace` for a two-folder workspace where each folder uses its own `.venv` interpreter:

```
File → Open Workspace from File → soccercv-platform.code-workspace
```

VS Code will prompt to install recommended extensions (Pylance, Ruff, Even Better TOML, OpenAPI editor).

***

## Debugging

All debug configurations live in `.vscode/launch.json`. Open the Run & Debug panel (`Ctrl+Shift+D` / `⌘⇧D`) to select and launch them. `debugpy` is a dev dependency — install it with `uv sync`.

### Backend breakpoints

**Easiest — VS Code launches the process:**

1. Select **"Backend: Launch (debug)"** in the Run & Debug panel and press `F5`.
2. VS Code starts uvicorn under debugpy automatically. Set breakpoints anywhere in `backend/`.

> `--reload` is disabled in this config. Uvicorn's hot-reload forks a child process that debugpy cannot follow. To pick up code changes, stop and re-launch the debug session.

**Manual start (then attach):**

```Shell
# Starts immediately, debugger can attach any time
python -m debugpy --listen 5678 -m uvicorn backend.main:app --host 0.0.0.0 --port 8001

# Or pause on startup until the debugger connects
python -m debugpy --listen 5678 --wait-for-client -m uvicorn backend.main:app --host 0.0.0.0 --port 8001
```

Then select **"Backend: Attach"** in VS Code and press `F5`.

### Frontend state breakpoints

Reflex runs a Python uvicorn server on `:8000` that handles WebSocket state sync and event handlers. Breakpoints in `app/states/` fire here.

> The React UI on `:3000` is compiled JavaScript — debug that with browser DevTools (`F12`), not debugpy.

**VS Code launch:**

Select **"Frontend: Launch (debug)"** and press `F5`. Set breakpoints in any state event handler.

**Manual start:**

```Shell
python -m debugpy --listen 5679 -m reflex run
# Then: "Frontend: Attach" in VS Code
```

**Compound launch — debug both at once:**

Select **"Debug: Backend + Frontend"** to start both services under debugpy in a single `F5`.

### Container debugging

Uses `compose.debug.yml` as an override on top of `compose.yml`. Both services start with `--wait-for-client` — they pause until a debugger attaches.

```Shell
# Start containers in debug mode
podman compose -f compose.yml -f compose.debug.yml up --build
```

Exposed ports: `5678` (backend debugpy), `5679` (frontend debugpy).

Then in VS Code, select **"Debug: Attach both (containers)"** and press `F5`. Path mappings in `launch.json` translate `/app` (container) ↔ `${workspaceFolder}` (local) so breakpoints resolve correctly.

***

## Configuration

All configuration lives in `.env` at the project root. This file is **gitignored** — never commit it. The backend loads it automatically via `python-dotenv` on startup. In containers, `env_file: .env` in `compose.yml` injects variables before the process starts.

```Properties&#x20;files
# Database — must match what you created in Postgres
POSTGRES_DB=soccercv_db
POSTGRES_USER=soccercv_user
POSTGRES_PASSWORD=<your-password>
POSTGRES_HOST=localhost        # use "db" inside containers
POSTGRES_PORT=5432

# API keys
ANTHROPIC_API_KEY=             # required for AI brief generation (backend reads this directly)
ROBOFLOW_API_KEY=              # required for soccercv download-ball-model

# Engine tuning (passed as env to soccercv subprocesses)
YOLO_MODEL=models/yolov8n.pt
YOLO_IMGSZ=320
FRAME_SKIP=3
PITCH_WIDTH=105
PITCH_HEIGHT=68
```

Full variable list with documentation is in `.env` itself.

***

## Database

Schema is managed by **Alembic**. Migration commands pick up Postgres credentials from `.env` automatically.

```Shell
alembic upgrade head                                   # apply all pending migrations
alembic upgrade head --sql                             # preview DDL without executing
alembic revision --autogenerate -m "describe change"   # generate from model diff
alembic downgrade -1                                   # roll back one migration
python -m backend.db.seed                              # seed teams + settings (idempotent)
```

**Tables:** `teams`, `jobs`, `tactical_summaries`, `player_stats`, `ai_reports`, `user_settings`

***

## Container Deployment

See [Scenario B](#scenario-b--full-container-stack) above for the full run sequence. This section covers the compose architecture and production notes.

### Services

| Service    | Image                   | Ports      | Notes                                                     |
| ---------- | ----------------------- | ---------- | --------------------------------------------------------- |
| `db`       | `postgres:16-alpine`    | 5432       | Healthcheck: `pg_isready`; backend waits on healthy       |
| `backend`  | `backend/Containerfile` | 8001       | Python 3.11-slim + ffmpeg; installs engine from submodule |
| `frontend` | `Containerfile` (root)  | 3000, 8000 | Python 3.12-slim + Node; Reflex prod mode                 |

### Volumes

| Volume / Bind                         | Container path             | Purpose                                     |
| ------------------------------------- | -------------------------- | ------------------------------------------- |
| `pgdata` (named)                      | `/var/lib/postgresql/data` | Postgres data persistence                   |
| `runs` (named)                        | `/data/runs`               | Analysis output — videos, heatmaps, reports |
| `./soccercv_engine/models` (bind, ro) | `/app/models`              | YOLO + ball detection weights               |

### Environment variables in containers

`compose.yml` uses `${VAR}` substitution sourced from `.env` (Podman Compose auto-loads `.env` for variable substitution). The backend service additionally carries `env_file: .env` so every engine config variable (`YOLO_*`, `BALL_*`, `ANTHROPIC_API_KEY`, etc.) is in the subprocess environment when `soccercv` runs. The explicit `DB_URL` in `compose.yml` overrides `POSTGRES_HOST` from `.env`, so keeping `POSTGRES_HOST=localhost` in `.env` works correctly for both local dev and containers.

### Backend image build notes

The `backend/Containerfile` installs the soccercv engine in a dedicated layer before backend deps — this keeps torch/torchvision cached across incremental rebuilds. The engine source is copied from `soccercv_engine/` (the submodule), so the submodule must be populated before building:

```Shell
git submodule update --init --recursive
podman compose build backend
```

***

## Project Structure

```
soccer_analysis/
├── app/                          # Reflex frontend
│   ├── app.py                    # Route definitions (6 pages)
│   ├── components/
│   │   ├── shell.py              # AppShell, TopBar, Rail, BottomTabs
│   │   ├── dashboard.py          # Jobs table, stat cards, empty state
│   │   ├── upload.py             # 4-step upload wizard
│   │   ├── report.py             # Pitch overlays, stats panel, AI brief
│   │   ├── player.py             # Player deep-dive (4 tabs)
│   │   ├── calibration.py        # Camera calibration coordinate entry
│   │   ├── settings.py           # Direction / theme / contrast / density
│   │   ├── charts.py             # Sparkline, MomentumChart, CompareBar
│   │   ├── primitives.py         # Card, Chip, SegSwitch, MiniBar, ProgressBar
│   │   └── pitch.py              # SVG pitch + overlay layers
│   ├── states/
│   │   ├── app_state.py          # Global: theme, direction, active team
│   │   ├── jobs_state.py         # Jobs list, SSE subscription, filters
│   │   ├── upload_state.py       # Wizard steps, file upload, submission
│   │   ├── report_state.py       # Selected job, tactical data, players
│   │   ├── player_state.py       # Single player tab state
│   │   ├── calibration_state.py  # Frame URL, coordinate inputs, homography
│   │   └── settings_state.py     # Thin alias of AppState
│   └── styles/
│       ├── tokens.css            # CSS custom properties (directions × themes)
│       ├── views.css             # Shell + page layout classes
│       └── components.css        # Buttons, forms, badges, cards
├── backend/
│   ├── main.py                   # FastAPI entry point, CORS, lifespan
│   ├── routers/
│   │   ├── jobs.py               # Job endpoints + SSE + pipeline triggers
│   │   ├── teams.py              # Team CRUD
│   │   └── settings.py           # Singleton UserSettings
│   ├── db/
│   │   ├── models.py             # SQLAlchemy 2.x async ORM
│   │   ├── queries.py            # Async CRUD helpers
│   │   ├── session.py            # Engine + session factory (reads POSTGRES_* from env)
│   │   ├── seed.py               # Teams + settings seed
│   │   └── migrations/           # Alembic (single migration: 0001_initial_schema)
│   └── services/
│       ├── pipeline.py           # soccercv subprocess wrapper + progress parser
│       └── ai_analysis.py        # pydantic-ai agent, aggregate_frames(), prompt builder
├── soccercv_engine/              # git submodule → github.com/pmCrawler/soccercv
├── soccercv-platform.code-workspace
├── compose.yml                   # Podman Compose — 3 services
├── Containerfile                 # Frontend image (Python 3.12-slim + Node)
├── backend/Containerfile         # Backend image (Python 3.11-slim + ffmpeg + engine)
├── rxconfig.py                   # Reflex config + CSS file injection
├── alembic.ini
├── pyproject.toml
└── .env                          # Local secrets — gitignored
```

***

## Pages and Routes

| Route                   | State              | Description                                                |
| ----------------------- | ------------------ | ---------------------------------------------------------- |
| `/`                     | `JobsState`        | Dashboard — stat cards, jobs table with live SSE progress  |
| `/upload`               | `UploadState`      | 4-step wizard: Source → Match → Output → Submit            |
| `/report?job=<id>`      | `ReportState`      | Pitch overlays, video player, AI brief, player stats table |
| `/player/[num]`         | `PlayerState`      | Player deep-dive: Overview / Heatmap / Passes / Timeline   |
| `/calibration?job=<id>` | `CalibrationState` | Enter pixel coords for 4+ pitch landmarks → homography     |
| `/settings`             | `AppState`         | Visual direction, theme, contrast, density                 |

***

## API Reference

```
# Jobs
POST   /api/jobs                         Upload video + metadata → create job
GET    /api/jobs                         List jobs (?status=, ?team_id=)
GET    /api/jobs/{id}                    Job detail + file manifest
DELETE /api/jobs/{id}                    Cancel + cleanup
GET    /api/jobs/{id}/events             SSE stream — progress + log lines

# Pipeline steps (idempotent — safe to re-trigger)
POST   /api/jobs/{id}/preprocess         Run soccercv preprocess
GET    /api/jobs/{id}/calibration-frame  Return JPEG for calibration UI
POST   /api/jobs/{id}/calibrate          [{pixel_x,y,pitch_x,y}×4+] → homography.npy
POST   /api/jobs/{id}/analyze            Run soccercv analyze (streams via /events)
POST   /api/jobs/{id}/report             Run soccercv report; generate AI brief in-process

# Data
GET    /api/jobs/{id}/tactical-summary   Parsed JSON for frontend charts
GET    /api/jobs/{id}/players            All PlayerStat rows for the job
GET    /api/jobs/{id}/ai-report          AIReport row for the job
GET    /api/jobs/{id}/files/{filename}   Serve output file (video, PNG, HTML)

# Teams
GET    /api/teams                        List teams
POST   /api/teams                        Create team

# Settings
GET    /api/settings                     Read UserSettings singleton
PUT    /api/settings                     Update UserSettings singleton
```

SSE event format (`GET /api/jobs/{id}/events`):

```JSON
{ "type": "progress", "pct": 42, "stage": "analyze", "line": "[detect] Frame 420/1000" }
{ "type": "done",     "status": "ready" }
{ "type": "error",    "message": "ffmpeg failed" }
```

***

## Pipeline Flow

```
1. POST /api/jobs            video uploaded → Job row created (status: queued)
2. POST …/preprocess         soccercv preprocess → *_clip.mp4 (status: preprocessing)
3. GET  …/calibration-frame  OpenCV extracts frame 0 → returns JPEG to UI
   POST …/calibrate          user submits 4+ pixel↔pitch coordinate pairs
                             → cv2.findHomography() called server-side
                             → homography.npy written (status: calibrating)
4. POST …/analyze            soccercv analyze → annotated video + tactical_report.json
                             progress streamed via SSE (status: analyzing)
5. POST …/report             soccercv report → HTML report written to run dir
                             backend reads tactical_report.json (per-frame array),
                             calls aggregate_frames() to compute possession/formations/
                             pressing/momentum stats, upserts TacticalSummary in DB.
                             If use_ai=True: aggregate is passed to generate_tactical_brief()
                             which calls Claude via pydantic-ai → structured TacticalBrief
                             → upserted to AIReport table.  (status: ready)
```

Calibration bypasses the engine's interactive CLI: the backend calls `cv2.findHomography()` directly with coordinates submitted from the UI form.

**AI brief generation** is handled entirely in the backend process — the `soccercv report` subprocess never receives `--ai`. This keeps API key handling, retry logic, and structured output validation inside the backend where they can be tested and monitored independently of the engine.

***

## Design System

Three visual directions, each with dark/light variants and normal/high contrast:

| Direction    | Feel                                                 |
| ------------ | ---------------------------------------------------- |
| `blueprint`  | Dark technical — navy background, cyan accent        |
| `broadcast`  | Broadcast sports — dark, high contrast, amber accent |
| `chalkboard` | Classic tactics board — dark green, chalk white      |

CSS tokens in `app/styles/tokens.css` are defined as custom properties on `[data-direction][data-theme]` selectors. The root `<html>` carries `data-direction`, `data-theme`, `data-contrast`, and `data-density` driven by `AppState`. Toggling direction or theme updates the attribute; every CSS variable re-resolves instantly with no page reload.

Class naming: flat BEM-lite (`rail-item`, `rail-item--active`, `compare-bar__label`). No Tailwind `@apply`.
