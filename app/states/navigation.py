import reflex as rx


class NavigationState(rx.State):
    @rx.var
    def current_page(self) -> str:
        path = self.router.page.path
        if path == "/upload":
            return "upload"
        if path == "/history":
            return "history"
        if path == "/reports":
            return "reports"
        return "dashboard"