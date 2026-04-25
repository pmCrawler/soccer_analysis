# SoccerCV Platform — Implementation Plan

> Sessions 1-3 completed the full backend + frontend scaffold. See handoff memory for exact status.

## Phase 0 — Scaffold ✅
- [x] FastAPI backend skeleton with CORS, lifespan, dotenv
- [x] SQLAlchemy 2.x async ORM — 6 tables (Team, Job, TacticalSummary, PlayerStat, AIReport, UserSettings)
- [x] Alembic migration (0001_initial_schema)
- [x] Seed script (4 teams + UserSettings row)
- [x] Reflex app — 6 routes

## Phase 1 — Design system + AppShell ✅
- [x] CSS token system (tokens.css, views.css, components.css)
- [x] AppState — direction/theme/contrast/density, HTML data-attribute wiring
- [x] AppShell, TopBar, Rail, BottomTabs, TeamSwitcher
- [x] Primitive components (Card, Chip, SegSwitch, MiniBar, ProgressBar)

## Phase 2 — Dashboard ✅
- [x] GET /api/jobs + GET /api/teams backend endpoints
- [x] JobsState — job list, SSE subscription, filters
- [x] Charts — Sparkline, MomentumChart, StatusDot, CompareBar
- [x] Dashboard — LiveHeroCard, SeasonSideCards, JobsTable, JobRow, filter group

## Phase 3 — Upload wizard ✅
- [x] POST /api/jobs (multipart upload + metadata)
- [x] SSE endpoint GET /api/jobs/{id}/events
- [x] UploadState — 4-step wizard, file upload, backend submission
- [x] UploadWizard component — Source / Match / Output / Submit panels

## Phase 4 — Calibration ✅
- [x] GET /api/jobs/{id}/calibration-frame (OpenCV frame extraction)
- [x] POST /api/jobs/{id}/calibrate (cv2.findHomography, writes homography.npy)
- [x] CalibrationState + CalibrationView component

## Phase 5 — Analysis pipeline + AI ✅
- [x] POST /api/jobs/{id}/preprocess, /analyze, /report pipeline endpoints
- [x] SSE progress parsing from `Frame NNN/TOTAL` stdout
- [x] aggregate_frames() — per-frame tactical_report.json → summary stats
- [x] pydantic-ai agent (TacticalBrief) — structured AI coaching brief
- [x] generate_tactical_brief() wired into POST /api/jobs/{id}/report

## Phase 6 — Report page ✅
- [x] GET /api/jobs/{id}/tactical-summary + /players + /ai-report endpoints
- [x] GET /api/jobs/{id}/files/{filename} — serve output files
- [x] ReportState, ReportView, PitchPanel, StatsPanel, AIBrief
- [x] SVG Pitch with overlay layers (formation/passes/press/heatmap/shots)
- [x] VideoPlayer component

## Phase 7 — Player deep-dive ✅
- [x] PlayerState, PlayerView — 4 tabs (Overview / Heat / Passes / Timeline)

## Phase 8 — Settings ✅
- [x] GET/PUT /api/settings endpoints
- [x] SettingsState, SettingsView, OnboardingView

## Phase 9 — Container setup ✅
- [x] backend/Containerfile (Python 3.11-slim + engine from submodule)
- [x] Containerfile (root — Python 3.12-slim + Reflex)
- [x] compose.yml (3 services, shared /data/runs volume)
- [x] compose.debug.yml (debugpy overlay)
- [x] VS Code launch.json + tasks.json

## Phase 10 — First end-to-end run ⏳
- [ ] Start Scenario A and navigate all 6 pages
- [ ] Upload a real video → full pipeline → report page
- [ ] Verify SSE progress in dashboard
- [ ] Verify AI brief with real ANTHROPIC_API_KEY
- [ ] Fix any runtime errors discovered

## Future / backlog
- [ ] Player stats ingestion from engine output (PlayerStat rows not yet populated)
- [ ] Redis + Traefik/Caddy reverse proxy (placeholder in compose.yml)
- [ ] Reflex prod mode validation (may need `reflex export` + static server)
- [ ] PPDA calculation (ppda_a/ppda_b currently null — engine doesn't output this yet)
