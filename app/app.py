import reflex as rx
from app.states.navigation import NavigationState
from app.components.layout import layout
from app.components.upload_view import upload_view
from app.components.history_view import history_view
from app.components.dashboard_view import dashboard_view
from app.components.report_view import report_view


def dashboard_page():
    return layout(dashboard_view())


def reports_page():
    return layout(report_view())


def upload_page() -> rx.Component:
    return layout(upload_view())


def history_page() -> rx.Component:
    return layout(history_view())


app = rx.App(
    theme=rx.theme(appearance="light"),
    head_components=[
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(rel="preconnect", href="https://fonts.gstatic.com", cross_origin=""),
        rx.el.link(
            href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap",
            rel="stylesheet",
        ),
    ],
)
app.add_page(dashboard_page, route="/")
app.add_page(upload_page, route="/upload")
app.add_page(history_page, route="/history")
app.add_page(reports_page, route="/reports")