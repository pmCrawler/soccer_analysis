# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```shell
# First-time setup: install app deps + editable engine install into this venv
uv sync
uv pip install --no-deps -e soccercv_engine/   # makes `soccercv` CLI available to the backend

# Run the Reflex frontend (hot-reload on localhost:3000)
reflex run

# Run the FastAPI backend (port 8001)
uvicorn backend.main:app --reload --port 8001

# Run database migrations
alembic upgrade head

# Seed initial data (teams + settings row)
python -m backend.db.seed

# Run all services via Podman Compose
podman compose up --build
```

## Architecture

Three-service system: **frontend** (Reflex), **backend** (FastAPI), **db** (PostgreSQL). A `soccercv` CLI engine (already written, not in this repo) is installed inside the backend container and invoked as async subprocesses.

```
frontend (Reflex :3000/:8000)
    ↕ REST + SSE
backend (FastAPI :8001)
    ↕ SQLAlchemy async
db (PostgreSQL :5432)

backend also:
  - spawns `soccercv` CLI subprocesses
  - reads/writes /data/runs shared volume
  - serves output files (video, heatmaps, reports)
```

### Frontend (`app/` — Reflex)

Pages registered in `app/app.py`:
- `/` → `dashboard_page` — jobs table with real-time progress, team stats
- `/upload` → `upload_page` — 4-step wizard (Source / Match / Output / Submit)
- `/report` → `report_page` — SVG pitch overlays, AI brief, player stats
- `/player/[num]` → `player_page` — 4-tab player deep-dive
- `/settings` → `settings_page` — direction/theme/contrast/density
- `/calibration` → `calibration_page` — click-to-calibrate camera frame

State hierarchy (all subclass `AppState`):
- `AppState` — direction, theme, contrast, density, active_team, settings persistence
- `JobsState(AppState)` — jobs list, teams, SSE subscription, filters
- `UploadState(AppState)` — wizard step, form fields, file upload
- `ReportState(AppState)` — loaded job+tactical+players+ai_report
- `PlayerState(AppState)` — single player deep-dive
- `CalibrationState(AppState)` — frame URL, click points, homography submit
- `SettingsState(AppState)` — thin alias

### Design system

CSS token system in `app/styles/tokens.css` — 3 visual directions (`blueprint`, `broadcast`, `chalkboard`) × `dark`/`light` × `normal`/`high` contrast × `comfortable`/`compact` density. Driven by `data-direction`, `data-theme`, `data-contrast`, `data-density` on `<html>`. `app_shell()` in `shell.py` wires these from `AppState`.

CSS files injected via `rxconfig.py` → `ProjectTailwindPlugin`:
- `tokens.css` — CSS custom properties (colors, spacing, typography, radius)
- `views.css` — shell, dashboard, upload, report, player, settings layouts
- `components.css` — buttons, forms, badges, seg-switch, cards, empty states

Class naming: flat with modifier suffix (`rail-item`, `rail-item--active`). No Tailwind `@apply` in the new system.

### Backend (`backend/` — FastAPI)

- `backend/main.py` — FastAPI app, CORS, lifespan (creates tables)
- `backend/routers/jobs.py` — all job endpoints + SSE stream + pipeline steps
- `backend/routers/teams.py` — team CRUD
- `backend/routers/settings.py` — singleton UserSettings
- `backend/db/models.py` — SQLAlchemy 2.x async ORM (Team, Job, TacticalSummary, PlayerStat, AIReport, UserSettings)
- `backend/db/queries.py` — async CRUD helpers
- `backend/db/session.py` — `get_db` dependency
- `backend/services/pipeline.py` — `run_soccercv()` async subprocess wrapper, parses `Frame NNN/TOTAL` for progress
- `backend/db/migrations/` — Alembic, single migration `0001_initial_schema.py`

### Pipeline flow

1. `POST /api/jobs` — upload video, create Job row, save to `/data/runs/{job_id}/`
2. `POST /api/jobs/{id}/preprocess` — spawns `soccercv preprocess`, produces `*_clip.mp4`
3. `GET /api/jobs/{id}/calibration-frame` — OpenCV extracts frame 0, returns JPEG
4. `POST /api/jobs/{id}/calibrate` — receives 4+ `{pixel_x,y,pitch_x,y}` points, calls `cv2.findHomography()`, writes `homography.npy`
5. `POST /api/jobs/{id}/analyze` — spawns `soccercv analyze`, streams progress via `GET /api/jobs/{id}/events` (SSE)
6. `POST /api/jobs/{id}/report` — spawns `soccercv report`, ingests `tactical_report.json` into DB on success

### Key Reflex patterns

- `@rx.event(background=True)` — SSE subscription in `JobsState.subscribe_to_job`; must use `async with self:` before state mutation
- `rx.foreach(list, fn)` — list rendering
- `rx.cond(condition, true, false)` — conditional rendering
- `rx.match(value, (case, component), ..., default)` — multi-branch rendering
- `on_mount=EventHandler` — load data when page renders
