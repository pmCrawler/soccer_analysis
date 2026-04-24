"""Jobs list state — loads from backend, tracks SSE progress."""

import asyncio
import json
import os
import httpx
import reflex as rx

from .app_state import AppState, BACKEND_URL


class JobsState(AppState):
    jobs: list[dict] = []
    teams: list[dict] = []
    status_filter: str = "all"
    _loading: bool = False

    @rx.var
    def filtered_jobs(self) -> list[dict]:
        if self.status_filter == "all":
            return self.jobs
        if self.status_filter == "processing":
            processing = {"preprocessing", "calibrating", "analyzing", "reporting", "queued", "live"}
            return [j for j in self.jobs if j.get("status") in processing]
        return [j for j in self.jobs if j.get("status") == self.status_filter]

    @rx.var
    def ready_count(self) -> int:
        return sum(1 for j in self.jobs if j.get("status") == "ready")

    @rx.var
    def processing_count(self) -> int:
        processing = {"preprocessing", "calibrating", "analyzing", "reporting", "queued", "live"}
        return sum(1 for j in self.jobs if j.get("status") in processing)

    @rx.event
    async def load_jobs(self):
        self._loading = True
        try:
            async with httpx.AsyncClient() as client:
                params = {}
                if self.active_team_id:
                    params["team_id"] = self.active_team_id
                r = await client.get(f"{BACKEND_URL}/api/jobs", params=params, timeout=10.0)
                if r.status_code == 200:
                    self.jobs = r.json()
        except Exception:
            pass
        self._loading = False

    @rx.event
    async def load_teams(self):
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(f"{BACKEND_URL}/api/teams", timeout=5.0)
                if r.status_code == 200:
                    self.teams = r.json()
        except Exception:
            pass

    @rx.event
    def set_status_filter(self, value: str):
        self.status_filter = value

    @rx.event(background=True)
    async def subscribe_to_job(self, job_id: str):
        url = f"{BACKEND_URL}/api/jobs/{job_id}/events"
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("GET", url) as response:
                    async for line in response.aiter_lines():
                        if not line.startswith("data:"):
                            continue
                        raw = line[5:].strip()
                        if not raw:
                            continue
                        try:
                            event = json.loads(raw)
                        except Exception:
                            continue
                        async with self:
                            self._apply_progress_event(job_id, event)
                        if event.get("type") in ("done", "error"):
                            break
        except Exception:
            pass

    def _apply_progress_event(self, job_id: str, event: dict):
        for i, job in enumerate(self.jobs):
            if job.get("id") == job_id:
                if event.get("type") == "progress":
                    self.jobs[i] = {**job, "progress": event.get("pct", job.get("progress", 0))}
                elif event.get("type") == "done":
                    self.jobs[i] = {**job, "status": event.get("status", "ready"), "progress": 1.0}
                elif event.get("type") == "error":
                    self.jobs[i] = {**job, "status": "failed"}
                break
