"""Report view state."""

import os
import httpx
import reflex as rx
from .app_state import AppState, BACKEND_URL


class ReportState(AppState):
    job_id: str = ""
    job: dict = {}
    tactical: dict = {}
    players: list[dict] = []
    ai_report: dict = {}
    active_overlay: str = "formation"   # formation | passes | press | heatmap | shots
    active_half: str = "full"
    loading: bool = False
    error: str = ""

    @rx.event
    async def load_report(self):
        job_id = self.router.page.params.get("job", "")
        if not job_id:
            return
        self.job_id = job_id
        self.loading = True
        self.error = ""
        try:
            async with httpx.AsyncClient() as client:
                job_r = await client.get(f"{BACKEND_URL}/api/jobs/{job_id}", timeout=10.0)
                if job_r.status_code == 200:
                    self.job = job_r.json()
                tactical_r = await client.get(f"{BACKEND_URL}/api/jobs/{job_id}/tactical-summary", timeout=10.0)
                if tactical_r.status_code == 200:
                    self.tactical = tactical_r.json()
                players_r = await client.get(f"{BACKEND_URL}/api/jobs/{job_id}/players", timeout=10.0)
                if players_r.status_code == 200:
                    self.players = players_r.json()
                ai_r = await client.get(f"{BACKEND_URL}/api/jobs/{job_id}/ai-report", timeout=10.0)
                if ai_r.status_code == 200:
                    self.ai_report = ai_r.json()
        except Exception as e:
            self.error = str(e)
        self.loading = False

    @rx.event
    def set_overlay(self, value: str):
        self.active_overlay = value

    @rx.event
    def set_half(self, value: str):
        self.active_half = value
