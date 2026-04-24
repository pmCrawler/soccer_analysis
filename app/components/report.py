"""Report view — pitch panel, stats, AI brief."""

import reflex as rx
from app.states.report_state import ReportState
from app.components.primitives import card
from app.components.pitch import svg_pitch
from app.components.charts import compare_bar


def _overlay_tab(label: str, value: str) -> rx.Component:
    return rx.el.button(
        label,
        class_name=rx.cond(
            ReportState.active_overlay == value,
            "seg-switch__btn seg-switch__btn--active",
            "seg-switch__btn",
        ),
        on_click=ReportState.set_overlay(value),
    )


def _report_header() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h1(
                ReportState.job["home"], " vs ", ReportState.job["away"],
                class_name="report-title",
            ),
            rx.el.p(ReportState.job["competition"], class_name="report-subtitle"),
            class_name="report-header__text",
        ),
        rx.el.div(
            rx.el.span(ReportState.job["home_score"], class_name="score"),
            rx.el.span("—", class_name="score-sep"),
            rx.el.span(ReportState.job["away_score"], class_name="score"),
            class_name="report-header__score",
        ),
        class_name="report-header",
    )


def _pitch_panel() -> rx.Component:
    return card(
        rx.el.div(
            _overlay_tab("Formation", "formation"),
            _overlay_tab("Passes", "passes"),
            _overlay_tab("Pressing", "press"),
            _overlay_tab("Heatmap", "heatmap"),
            _overlay_tab("Shots", "shots"),
            class_name="seg-switch",
        ),
        svg_pitch(overlay_mode=ReportState.active_overlay),
        class_name="pitch-panel",
    )


def _stats_panel() -> rx.Component:
    return card(
        rx.el.h3("Match Stats", class_name="panel-title"),
        compare_bar(
            ReportState.job.get("home", "Home"),
            ReportState.tactical.get("possession_a", 50),
            ReportState.job.get("away", "Away"),
            ReportState.tactical.get("possession_b", 50),
        ),
        rx.el.div(
            rx.el.div(
                rx.el.span(ReportState.tactical.get("formation_a", "—"), class_name="stat-val"),
                rx.el.span("Formation", class_name="stat-key"),
                rx.el.span(ReportState.tactical.get("formation_b", "—"), class_name="stat-val"),
                class_name="stat-row",
            ),
            rx.el.div(
                rx.el.span(ReportState.tactical.get("ppda_a", "—"), class_name="stat-val"),
                rx.el.span("PPDA", class_name="stat-key"),
                rx.el.span(ReportState.tactical.get("ppda_b", "—"), class_name="stat-val"),
                class_name="stat-row",
            ),
            class_name="stats-list",
        ),
        class_name="stats-panel",
    )


def _ai_brief() -> rx.Component:
    return rx.cond(
        ReportState.ai_report,
        card(
            rx.el.h3(ReportState.ai_report.get("headline", ""), class_name="ai-brief__headline"),
            rx.el.p(ReportState.ai_report.get("match_summary", ""), class_name="ai-brief__body"),
            rx.el.details(
                rx.el.summary("Team Tendencies"),
                rx.el.p(ReportState.ai_report.get("team_tendencies", ""), class_name="ai-brief__section-body"),
            ),
            rx.el.details(
                rx.el.summary("Formation Analysis"),
                rx.el.p(ReportState.ai_report.get("formation_analysis", ""), class_name="ai-brief__section-body"),
            ),
            rx.el.details(
                rx.el.summary("Recommendations"),
                rx.el.p(ReportState.ai_report.get("recommendations", ""), class_name="ai-brief__section-body"),
            ),
            class_name="ai-brief card",
        ),
        rx.el.div(),
    )


def report_view() -> rx.Component:
    return rx.cond(
        ReportState.job,
        rx.el.div(
            _report_header(),
            rx.el.div(
                _pitch_panel(),
                rx.el.div(
                    _stats_panel(),
                    _ai_brief(),
                    class_name="report-sidebar",
                ),
                class_name="report-body",
            ),
            on_mount=ReportState.load_report,
            class_name="report-view view",
        ),
        rx.el.div(
            rx.cond(
                ReportState.loading,
                rx.el.div(
                    rx.icon("loader", size=32, color="var(--accent)"),
                    rx.el.p("Loading report...", class_name="loading-msg"),
                    class_name="loading-state",
                ),
                rx.el.div(
                    rx.el.p("Select a job from the dashboard to view a report.", class_name="empty-state__body"),
                    rx.link(rx.el.button("Go to Dashboard", class_name="btn-primary"), href="/"),
                    class_name="empty-state",
                ),
            ),
            on_mount=ReportState.load_report,
            class_name="report-view view",
        ),
    )
