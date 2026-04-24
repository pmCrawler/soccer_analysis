"""SoccerCV Reflex application — 5 routes."""

import reflex as rx


def dashboard_page() -> rx.Component:
    from app.components.shell import app_shell
    from app.components.dashboard import dashboard_view
    return app_shell(dashboard_view())


def upload_page() -> rx.Component:
    from app.components.shell import app_shell
    from app.components.upload import upload_wizard
    return app_shell(upload_wizard())


def report_page() -> rx.Component:
    from app.components.shell import app_shell
    from app.components.report import report_view
    return app_shell(report_view())


def player_page() -> rx.Component:
    from app.components.shell import app_shell
    from app.components.player import player_view
    return app_shell(player_view())


def settings_page() -> rx.Component:
    from app.components.shell import app_shell
    from app.components.settings import settings_view
    return app_shell(settings_view())


def calibration_page() -> rx.Component:
    from app.components.shell import app_shell
    from app.components.calibration import calibration_view
    return app_shell(calibration_view())


app = rx.App(
    theme=rx.theme(appearance="light"),
    head_components=[
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(rel="preconnect", href="https://fonts.gstatic.com", cross_origin=""),
        rx.el.link(
            href="https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,400;0,14..32,500;0,14..32,600;0,14..32,700;0,14..32,800;1,14..32,400&display=swap",
            rel="stylesheet",
        ),
    ],
)

app.add_page(dashboard_page, route="/")
app.add_page(upload_page, route="/upload")
app.add_page(report_page, route="/report")
app.add_page(player_page, route="/player/[num]")
app.add_page(settings_page, route="/settings")
app.add_page(calibration_page, route="/calibration")
