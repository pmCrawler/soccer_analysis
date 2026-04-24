"""Global application state — theme, direction, active team."""

import os
import httpx
import reflex as rx

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8001")


class AppState(rx.State):
    direction: str = "blueprint"   # blueprint | broadcast | chalkboard
    theme: str = "dark"            # dark | light | auto
    contrast: str = "normal"       # normal | high
    density: str = "comfortable"   # comfortable | compact

    active_team_id: str = ""
    active_team_name: str = "All Teams"

    _settings_loaded: bool = False

    @rx.event
    async def load_settings(self):
        if self._settings_loaded:
            return
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(f"{BACKEND_URL}/api/settings", timeout=5.0)
                if r.status_code == 200:
                    data = r.json()
                    self.direction = data.get("direction", self.direction)
                    self.theme = data.get("theme", self.theme)
                    self.contrast = data.get("contrast", self.contrast)
                    self.density = data.get("density", self.density)
        except Exception:
            pass
        self._settings_loaded = True

    @rx.event
    async def set_direction(self, value: str):
        self.direction = value
        await self._persist_settings()

    @rx.event
    async def set_theme(self, value: str):
        self.theme = value
        await self._persist_settings()

    @rx.event
    async def set_contrast(self, value: str):
        self.contrast = value
        await self._persist_settings()

    @rx.event
    async def set_density(self, value: str):
        self.density = value
        await self._persist_settings()

    @rx.event
    def set_active_team(self, team_id: str, team_name: str):
        self.active_team_id = team_id
        self.active_team_name = team_name

    async def _persist_settings(self):
        try:
            async with httpx.AsyncClient() as client:
                await client.put(
                    f"{BACKEND_URL}/api/settings",
                    json={
                        "direction": self.direction,
                        "theme": self.theme,
                        "contrast": self.contrast,
                        "density": self.density,
                    },
                    timeout=5.0,
                )
        except Exception:
            pass
