"""Calibration view state."""

import httpx
import reflex as rx
from .app_state import AppState, BACKEND_URL

PITCH_LANDMARKS = [
    ("Center spot", 52.5, 34.0),
    ("Penalty spot A", 11.0, 34.0),
    ("Penalty spot B", 94.0, 34.0),
    ("Top-left corner", 0.0, 0.0),
    ("Top-right corner", 105.0, 0.0),
    ("Bottom-left corner", 0.0, 68.0),
    ("Bottom-right corner", 105.0, 68.0),
    ("Left penalty area TL", 0.0, 13.85),
    ("Left penalty area TR", 16.5, 13.85),
    ("Left penalty area BL", 0.0, 54.15),
    ("Left penalty area BR", 16.5, 54.15),
    ("Right penalty area TL", 88.5, 13.85),
    ("Right penalty area TR", 105.0, 13.85),
    ("Right penalty area BL", 88.5, 54.15),
    ("Right penalty area BR", 105.0, 54.15),
]


class CalibrationState(AppState):
    job_id: str = ""
    frame_url: str = ""
    clicks: list[dict] = []           # [{pixel_x, pixel_y, pitch_x, pitch_y}]
    pending_click: dict = {}          # last pixel click waiting for landmark assignment
    selected_landmark: int = 0
    submitting: bool = False
    error: str = ""
    done: bool = False

    # Manual pixel coordinate entry
    pixel_x_input: str = ""
    pixel_y_input: str = ""

    @rx.var
    def clicks_count(self) -> int:
        return len(self.clicks)

    @rx.event
    async def load_frame(self):
        job_id = self.router.page.params.get("job", "")
        if not job_id:
            return
        self.job_id = job_id
        self.frame_url = f"{BACKEND_URL}/api/jobs/{job_id}/calibration-frame"

    @rx.event
    def set_pixel_x(self, v: float | str):
        self.pixel_x_input = str(v)

    @rx.event
    def set_pixel_y(self, v: float | str):
        self.pixel_y_input = str(v)

    @rx.event
    def set_landmark(self, v: str):
        try:
            self.selected_landmark = int(v)
        except ValueError:
            pass

    @rx.event
    def confirm_point(self):
        try:
            px = float(self.pixel_x_input)
            py = float(self.pixel_y_input)
        except ValueError:
            self.error = "Enter valid pixel X and Y values"
            return
        lm = PITCH_LANDMARKS[self.selected_landmark]
        self.clicks.append({
            "pixel_x": px,
            "pixel_y": py,
            "pitch_x": lm[1],
            "pitch_y": lm[2],
        })
        self.pixel_x_input = ""
        self.pixel_y_input = ""
        self.error = ""

    @rx.event
    def remove_last_click(self):
        if self.clicks:
            self.clicks.pop()

    @rx.event
    async def submit_calibration(self):
        if len(self.clicks) < 4:
            self.error = "At least 4 calibration points required"
            return
        self.submitting = True
        self.error = ""
        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    f"{BACKEND_URL}/api/jobs/{self.job_id}/calibrate",
                    json={"points": self.clicks},
                    timeout=15.0,
                )
                if r.status_code == 200:
                    self.done = True
                    return rx.redirect(f"/report?job={self.job_id}")
                else:
                    self.error = f"Calibration failed: {r.status_code}"
        except Exception as e:
            self.error = str(e)
        self.submitting = False
