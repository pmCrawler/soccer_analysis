"""Player deep-dive state."""

import httpx
import reflex as rx
from .app_state import AppState, BACKEND_URL


class PlayerState(AppState):
    job_id: str = ""
    player_num: int = 0
    player: dict = {}
    active_tab: str = "overview"   # overview | heat | passes | timeline
    loading: bool = False

    @rx.event
    async def load_player(self):
        job_id = self.router.page.params.get("job", "")
        num = self.router.page.params.get("num", "0")
        if not job_id:
            return
        self.job_id = job_id
        self.player_num = int(num) if num.isdigit() else 0
        self.loading = True
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(f"{BACKEND_URL}/api/jobs/{job_id}/players", timeout=10.0)
                if r.status_code == 200:
                    players = r.json()
                    for p in players:
                        if p.get("number") == self.player_num:
                            self.player = p
                            break
        except Exception:
            pass
        self.loading = False

    @rx.event
    def set_tab(self, value: str):
        self.active_tab = value
