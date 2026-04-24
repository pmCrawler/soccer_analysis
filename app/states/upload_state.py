"""Upload wizard state — 4 steps: Source, Match, Output, Submit."""

import os
import httpx
import reflex as rx
from .app_state import AppState, BACKEND_URL

UPLOAD_ID = "match_video"


class UploadState(AppState):
    # wizard step: 0=source, 1=match, 2=output, 3=submitting
    step: int = 0

    # Match metadata
    home: str = ""
    away: str = ""
    competition: str = ""
    venue: str = ""
    match_date: str = ""
    kickoff: str = ""
    team_id: str = ""

    # Output options
    quality: str = "high"
    include_ai: bool = True
    include_tracking: bool = True
    include_heatmaps: bool = True

    # Submit state
    submitting: bool = False
    error_msg: str = ""
    created_job_id: str = ""

    @rx.var
    def can_proceed_step1(self) -> bool:
        return bool(self.home.strip() and self.away.strip())

    @rx.event
    def next_step(self):
        if self.step < 2:
            self.step += 1

    @rx.event
    def prev_step(self):
        if self.step > 0:
            self.step -= 1

    @rx.event
    def set_home(self, v: str):
        self.home = v

    @rx.event
    def set_away(self, v: str):
        self.away = v

    @rx.event
    def set_competition(self, v: str):
        self.competition = v

    @rx.event
    def set_venue(self, v: str):
        self.venue = v

    @rx.event
    def set_match_date(self, v: str):
        self.match_date = v

    @rx.event
    def set_kickoff(self, v: str):
        self.kickoff = v

    @rx.event
    def set_team_id(self, v: str):
        self.team_id = v

    @rx.event
    def set_quality(self, v: str):
        self.quality = v

    @rx.event
    def toggle_ai(self):
        self.include_ai = not self.include_ai

    @rx.event
    def toggle_tracking(self):
        self.include_tracking = not self.include_tracking

    @rx.event
    def toggle_heatmaps(self):
        self.include_heatmaps = not self.include_heatmaps

    @rx.event
    async def handle_submit(self, files: list[rx.UploadFile]):
        if not files:
            self.error_msg = "No file selected"
            return
        self.submitting = True
        self.error_msg = ""
        self.step = 3

        file = files[0]
        data = await file.read()

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                r = await client.post(
                    f"{BACKEND_URL}/api/jobs",
                    files={"video": (file.filename, data, file.content_type or "video/mp4")},
                    data={
                        "home": self.home,
                        "away": self.away,
                        "competition": self.competition,
                        "venue": self.venue,
                        "match_date": self.match_date,
                        "kickoff": self.kickoff,
                        "quality": self.quality,
                        "include_ai": str(self.include_ai).lower(),
                        "include_tracking": str(self.include_tracking).lower(),
                        "include_heatmaps": str(self.include_heatmaps).lower(),
                        "team_id": self.team_id,
                    },
                )
                if r.status_code == 201:
                    job = r.json()
                    self.created_job_id = job["id"]
                    # Kick off preprocessing
                    await client.post(
                        f"{BACKEND_URL}/api/jobs/{job['id']}/preprocess",
                        timeout=10.0,
                    )
                else:
                    self.error_msg = f"Upload failed: {r.status_code}"
                    self.submitting = False
        except Exception as e:
            self.error_msg = str(e)
            self.submitting = False
            return

        self.submitting = False
        return rx.redirect("/")
