# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```shell
# ── First-time setup ────────────────────────────────────────────────────────
uv sync
uv pip install -e soccercv_engine/ --extra-index-url https://download.pytorch.org/whl/cpu

# ── Scenario A: Local dev (DB in container, services on host) ───────────────
podman compose up db -d                          # start postgres, expose :5432
sleep 5 && alembic upgrade head                  # first time only
python -m backend.db.seed                        # first time only

uvicorn backend.main:app --reload --port 8001    # Terminal 1
reflex run                                       # Terminal 2

# Debug variants
uvicorn backend.main:app --reload --port 8001 --log-level debug
reflex run --log-level debug

podman compose down                              # stop DB (keep data)
podman compose down -v                           # stop DB + delete data

# ── Scenario B: Full container stack ────────────────────────────────────────
git submodule update --init --recursive          # must run before first build
podman compose up --build                        # build + start all 3 services
podman compose exec backend alembic upgrade head # first time only
podman compose exec backend python -m backend.db.seed  # first time only

podman compose up                                # subsequent starts (no rebuild)
podman compose up --build backend                # rebuild one service
podman compose logs -f backend                   # tail logs
podman compose down                              # stop (keep data)
podman compose down -v                           # stop + delete data

# ── Database ─────────────────────────────────────────────────────────────────
alembic upgrade head
alembic revision --autogenerate -m "describe change"
python -m backend.db.seed                        # idempotent

# ── Health checks ────────────────────────────────────────────────────────────
curl http://localhost:8001/api/teams             # backend alive
# open http://localhost:8001/docs                # Swagger UI
# open http://localhost:3000                     # frontend

# ── Verify all components build (run after any component/state change) ───────
python -c "
from app.components.dashboard import dashboard_view
from app.components.upload import upload_wizard
from app.components.report import report_view
from app.components.player import player_view
from app.components.settings import settings_view
from app.components.calibration import calibration_view
from app.components.shell import app_shell
dashboard_view(); upload_wizard(); report_view()
player_view(); settings_view(); calibration_view()
print('ALL COMPONENTS OK')
"
```

## Debugging

`debugpy` is a dev dependency (`uv sync` installs it). All configs are in `.vscode/launch.json`. Run & Debug panel (`Ctrl+Shift+D`) → select config → `F5`.

| Config | What it does |
|--------|-------------|
| `Backend: Launch (debug)` | VS Code starts uvicorn under debugpy — no attach needed |
| `Frontend: Launch (debug)` | VS Code starts `reflex run` under debugpy |
| `Debug: Backend + Frontend` | Compound — launches both at once |
| `Backend: Attach` | Attach to manually-started process on `:5678` |
| `Frontend: Attach` | Attach to manually-started process on `:5679` |
| `Container Backend/Frontend: Attach` | Attach to container processes (path maps `/app` ↔ local) |

**Critical:** `Backend: Launch` omits `--reload` — uvicorn hot-reload forks a child process debugpy cannot follow. Restart the debug session to pick up code changes.

**Breakpoints in Reflex state handlers** fire in the Python uvicorn server on `:8000`. The React UI on `:3000` is compiled JS — use browser DevTools for that.

**Container debug mode:**
```bash
podman compose -f compose.yml -f compose.debug.yml up --build
# Both services pause until debugger attaches (--wait-for-client)
# Then attach with "Debug: Attach both (containers)"
```

**Manual attach pattern (backend):**
```bash
python -m debugpy --listen 5678 -m uvicorn backend.main:app --host 0.0.0.0 --port 8001
# add --wait-for-client to pause until VS Code connects
```

## Architecture

Three-service system: **frontend** (Reflex), **backend** (FastAPI), **db** (PostgreSQL). The `soccercv` analysis engine lives in the `soccercv_engine/` git submodule and is invoked by the backend as async subprocesses.

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

### Submodule: soccercv engine

`soccercv_engine/` is a git submodule pointing to `github.com/pmCrawler/soccercv`. The engine is installed into this venv as an editable package so `soccercv` is on PATH for backend subprocess calls. Container builds COPY the submodule source directly.

To update the engine: `git -C soccercv_engine pull origin main && git add soccercv_engine && git commit -m "bump engine"`.

The engine is installed **with** its deps (torch, ultralytics, opencv, etc.) into the app's `.venv` — not `--no-deps`. Torch/torchvision come from the PyTorch CPU index, so pass `--extra-index-url https://download.pytorch.org/whl/cpu` when installing.

### Frontend (`app/` — Reflex)

Pages in `app/app.py`:
- `/` → `dashboard_page` — jobs table with real-time SSE progress, stat cards
- `/upload` → `upload_page` — 4-step wizard (Source / Match / Output / Submit)
- `/report` → `report_page` — SVG pitch overlays, AI brief, player stats
- `/player/[num]` → `player_page` — 4-tab player deep-dive
- `/settings` → `settings_page` — direction/theme/contrast/density
- `/calibration` → `calibration_page` — pixel coordinate entry for camera calibration

State hierarchy (all subclass `AppState`):
- `AppState` — direction, theme, contrast, density, active_team, settings persistence
- `JobsState(AppState)` — jobs list, teams, SSE subscription, filters
- `UploadState(AppState)` — wizard step, form fields, file upload
- `ReportState(AppState)` — loaded job + tactical + players + ai_report
- `PlayerState(AppState)` — single player deep-dive
- `CalibrationState(AppState)` — frame URL, pixel_x/y inputs, homography submit
- `SettingsState(AppState)` — thin alias

### Design system

CSS token system in `app/styles/tokens.css` — 3 directions (`blueprint`, `broadcast`, `chalkboard`) × `dark`/`light` × `normal`/`high` contrast × `comfortable`/`compact` density. Driven by `data-direction`, `data-theme`, `data-contrast`, `data-density` on `<html>`. `app_shell()` in `shell.py` wires these from `AppState`.

CSS files injected via `rxconfig.py` → `ProjectTailwindPlugin`:
- `tokens.css` — CSS custom properties
- `views.css` — shell, page layout classes
- `components.css` — buttons, forms, badges, seg-switch, cards, empty states

Class naming: flat BEM-lite (`rail-item`, `rail-item--active`). No Tailwind `@apply`.

### Backend (`backend/` — FastAPI)

- `backend/main.py` — app entry, CORS, lifespan (auto-creates tables)
- `backend/routers/jobs.py` — all job endpoints + SSE stream + pipeline triggers
- `backend/routers/teams.py` — team CRUD
- `backend/routers/settings.py` — singleton UserSettings
- `backend/db/models.py` — SQLAlchemy 2.x async ORM (Team, Job, TacticalSummary, PlayerStat, AIReport, UserSettings)
- `backend/db/queries.py` — async CRUD helpers
- `backend/db/session.py` — engine + session factory; builds DB_URL from POSTGRES_* env vars
- `backend/services/pipeline.py` — `run_soccercv()` async subprocess wrapper, parses `Frame NNN/TOTAL` for SSE progress
- `backend/services/ai_analysis.py` — `aggregate_frames()` (per-frame JSON → summary stats), `generate_tactical_brief()` (pydantic-ai agent → structured `TacticalBrief`)

### Pipeline flow

1. `POST /api/jobs` — upload video, create Job row, save to `/data/runs/{job_id}/`
2. `POST /api/jobs/{id}/preprocess` — spawns `soccercv preprocess`, produces `*_clip.mp4`
3. `GET /api/jobs/{id}/calibration-frame` — OpenCV extracts frame 0, returns JPEG
4. `POST /api/jobs/{id}/calibrate` — receives 4+ `{pixel_x,y,pitch_x,y}` points, calls `cv2.findHomography()` directly (no CLI), writes `homography.npy`
5. `POST /api/jobs/{id}/analyze` — spawns `soccercv analyze`, streams progress via SSE
6. `POST /api/jobs/{id}/report` — spawns `soccercv report` (no `--ai` flag); backend then reads `tactical_report.json` (a **per-frame array**), runs `aggregate_frames()` to compute all stats, upserts `TacticalSummary`; if `use_ai=True`, calls `generate_tactical_brief()` which calls Claude via pydantic-ai and upserts `AIReport`

### pydantic-ai integration

`TacticalBrief` in `ai_analysis.py` is the pydantic-ai output type — it maps 1:1 to `AIReport` DB columns. The agent is a lazy singleton (`_get_agent()`) so `ANTHROPIC_API_KEY` is read from environment after dotenv loads. API: `Agent(AnthropicModel("claude-sonnet-4-6"), output_type=TacticalBrief)`, result accessed as `result.output` (NOT `result.data`). Parameter is `output_type=` (NOT `result_type=`).

### Key Reflex patterns

- `@rx.event(background=True)` — SSE subscription in `JobsState.subscribe_to_job`; must use `async with self:` before any state mutation
- `rx.foreach(list, fn)` — list rendering; the callback arg is an untyped `ObjectItemOperation`
- **ObjectItemOperation arithmetic**: cast with `.to(float)` before `*`, `/`, `+`; use multiple children (not `+`) for string display: `rx.el.span(item["a"], " / ", item["b"])`
- **ObjectItemOperation comparison**: cast first: `item["progress"].to(float) > 0`
- `rx.cond(condition, true, false)` — conditional rendering
- `rx.match(value, (case, component), ..., default)` — multi-branch
- `on_mount=EventHandler` — load data when page mounts
- Icon names use kebab-case Lucide names: `circle-check`, `triangle-alert`, `loader-circle` (not `check-circle`, `alert-circle`, `loader`)

## Configuration

`.env` at project root is gitignored and loaded automatically by `python-dotenv` in `backend/main.py`. It provides `POSTGRES_*` for the DB connection and all engine config variables (`YOLO_*`, `BALL_*`, etc.) that get passed to `soccercv` subprocesses. See `.env` for the full variable list.
