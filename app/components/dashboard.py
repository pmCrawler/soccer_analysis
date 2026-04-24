"""Dashboard view — hero card, jobs table."""

import reflex as rx
from app.states.jobs_state import JobsState
from app.components.primitives import card, status_dot, progress_bar, chip


def _job_status_badge(status: str) -> rx.Component:
    return rx.el.span(
        status,
        class_name=rx.match(
            status,
            ("ready", "badge badge--success"),
            ("failed", "badge badge--danger"),
            ("live", "badge badge--accent"),
            "badge badge--warn",
        ),
    )


def _job_row(job: dict) -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            rx.el.div(
                status_dot(job["status"]),
                rx.el.span(
                    job["home"], " vs ", job["away"],
                    class_name="jobs-table__match",
                ),
                class_name="jobs-table__match-cell",
            ),
        ),
        rx.el.td(job["competition"]),
        rx.el.td(_job_status_badge(job["status"])),
        rx.el.td(
            rx.cond(
                job["status"] == "ready",
                rx.el.span("100%"),
                rx.el.div(
                    progress_bar(job["progress"]),
                    rx.el.span(
                        rx.cond(
                            job["progress"].to(float) > 0,
                            (job["progress"].to(float) * 100).to(int).to_string() + "%",
                            "—",
                        ),
                        class_name="jobs-table__pct",
                    ),
                    class_name="jobs-table__progress",
                ),
            )
        ),
        rx.el.td(
            rx.link(
                rx.icon("arrow-right", size=16),
                href="/report?job=" + job["id"].to(str),
                class_name="jobs-table__action",
            ),
        ),
        class_name="jobs-table__row",
    )


def _jobs_table() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h2("Match Jobs", class_name="section-title"),
            rx.el.div(
                *[
                    chip(label, value == JobsState.status_filter,
                         on_click=JobsState.set_status_filter(value))
                    for label, value in [
                        ("All", "all"),
                        ("Processing", "processing"),
                        ("Ready", "ready"),
                        ("Failed", "failed"),
                    ]
                ],
                class_name="chip-group",
            ),
            class_name="section-header",
        ),
        rx.el.table(
            rx.el.thead(
                rx.el.tr(
                    rx.el.th("Match"),
                    rx.el.th("Competition"),
                    rx.el.th("Status"),
                    rx.el.th("Progress"),
                    rx.el.th(""),
                    class_name="jobs-table__head",
                )
            ),
            rx.el.tbody(
                rx.foreach(JobsState.filtered_jobs, _job_row),
            ),
            class_name="jobs-table",
        ),
        class_name="jobs-section",
    )


def _stat_card(value, label: str, icon: str, color: str = "var(--accent)") -> rx.Component:
    return card(
        rx.el.div(
            rx.icon(icon, size=20, color=color),
            class_name="stat-card__icon",
        ),
        rx.el.div(
            rx.el.p(value, class_name="stat-card__value"),
            rx.el.p(label, class_name="stat-card__label"),
            class_name="stat-card__text",
        ),
        class_name="stat-card",
    )


def _onboarding_empty() -> rx.Component:
    return rx.el.div(
        rx.icon("video", size=48, color="var(--fg-3)"),
        rx.el.h2("No matches yet", class_name="empty-state__title"),
        rx.el.p(
            "Upload a match video to get started with AI-powered tactical analysis.",
            class_name="empty-state__body",
        ),
        rx.link(
            rx.el.button("Upload Match Footage", class_name="btn-primary"),
            href="/upload",
        ),
        class_name="empty-state",
    )


def dashboard_view() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            _stat_card(JobsState.ready_count, "Ready", "circle-check", "var(--good)"),
            _stat_card(JobsState.processing_count, "Processing", "loader-circle", "var(--warn)"),
            _stat_card(
                JobsState.teams.length().to_string(),
                "Teams",
                "shield",
            ),
            class_name="stats-row",
        ),
        rx.cond(
            JobsState.jobs,
            _jobs_table(),
            _onboarding_empty(),
        ),
        on_mount=[JobsState.load_jobs, JobsState.load_teams],
        class_name="dashboard-view view",
    )
