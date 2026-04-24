"""Upload wizard — 4 steps: Source, Match, Output, Submit."""

import reflex as rx
from app.states.upload_state import UploadState, UPLOAD_ID
from app.states.jobs_state import JobsState
from app.components.primitives import card


def _step_indicator(step: int) -> rx.Component:
    labels = ["Source", "Match", "Output", "Submitting"]
    return rx.el.div(
        *[
            rx.el.div(
                rx.el.div(
                    str(i + 1),
                    class_name=rx.cond(
                        UploadState.step > i,
                        "step-dot step-dot--done",
                        rx.cond(UploadState.step == i, "step-dot step-dot--active", "step-dot"),
                    ),
                ),
                rx.el.span(labels[i], class_name="step-label"),
                class_name="step-item",
            )
            for i in range(4)
        ],
        class_name="step-indicator",
    )


def _step_source() -> rx.Component:
    return rx.el.div(
        rx.upload(
            rx.el.div(
                rx.icon("video", size=40, color="var(--accent)"),
                rx.el.h3("Drag & Drop Match Footage", class_name="upload-zone__title"),
                rx.el.p("Supports MP4, AVI, MOV, MKV (max 10GB)", class_name="upload-zone__hint"),
                rx.el.button("Select File", class_name="btn-secondary upload-zone__btn"),
                class_name="upload-zone__inner",
            ),
            id=UPLOAD_ID,
            accept={
                "video/mp4": [".mp4"],
                "video/quicktime": [".mov"],
                "video/x-msvideo": [".avi"],
                "video/x-matroska": [".mkv"],
            },
            max_files=1,
            class_name="upload-zone",
        ),
        rx.el.div(
            rx.foreach(
                rx.selected_files(UPLOAD_ID),
                lambda f: rx.el.div(
                    rx.icon("file-video", size=16),
                    rx.el.span(f, class_name="file-chip__name"),
                    rx.el.button(
                        rx.icon("x", size=14),
                        on_click=rx.clear_selected_files(UPLOAD_ID),
                        class_name="file-chip__remove",
                    ),
                    class_name="file-chip",
                ),
            ),
            class_name="file-list",
        ),
        rx.el.div(
            rx.el.button(
                "Next: Match Info",
                rx.icon("arrow-right", size=16),
                on_click=UploadState.next_step,
                class_name="btn-primary",
            ),
            class_name="wizard-actions",
        ),
        class_name="wizard-step",
    )


def _form_field(label: str, *children) -> rx.Component:
    return rx.el.label(
        rx.el.span(label, class_name="form-label"),
        *children,
        class_name="form-field",
    )


def _step_match() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            _form_field(
                "Home Team *",
                rx.el.input(
                    placeholder="e.g. FCN",
                    value=UploadState.home,
                    on_change=UploadState.set_home,
                    class_name="form-input",
                ),
            ),
            _form_field(
                "Away Team *",
                rx.el.input(
                    placeholder="e.g. LKP",
                    value=UploadState.away,
                    on_change=UploadState.set_away,
                    class_name="form-input",
                ),
            ),
            class_name="form-row",
        ),
        rx.el.div(
            _form_field(
                "Competition",
                rx.el.input(
                    placeholder="e.g. Premier League",
                    value=UploadState.competition,
                    on_change=UploadState.set_competition,
                    class_name="form-input",
                ),
            ),
            _form_field(
                "Venue",
                rx.el.input(
                    placeholder="e.g. Wembley Stadium",
                    value=UploadState.venue,
                    on_change=UploadState.set_venue,
                    class_name="form-input",
                ),
            ),
            class_name="form-row",
        ),
        rx.el.div(
            _form_field(
                "Match Date",
                rx.el.input(
                    type="date",
                    value=UploadState.match_date,
                    on_change=UploadState.set_match_date,
                    class_name="form-input",
                ),
            ),
            _form_field(
                "Kickoff Time",
                rx.el.input(
                    type="time",
                    value=UploadState.kickoff,
                    on_change=UploadState.set_kickoff,
                    class_name="form-input",
                ),
            ),
            class_name="form-row",
        ),
        _form_field(
            "Club / Team",
            rx.el.select(
                rx.el.option("No team assigned", value=""),
                rx.foreach(
                    JobsState.teams,
                    lambda t: rx.el.option(t["name"], value=t["id"]),
                ),
                value=UploadState.team_id,
                on_change=UploadState.set_team_id,
                class_name="form-select",
            ),
        ),
        rx.el.div(
            rx.el.button(
                rx.icon("arrow-left", size=16),
                "Back",
                on_click=UploadState.prev_step,
                class_name="btn-secondary",
            ),
            rx.el.button(
                "Next: Output",
                rx.icon("arrow-right", size=16),
                on_click=UploadState.next_step,
                class_name="btn-primary",
                disabled=~UploadState.can_proceed_step1,
            ),
            class_name="wizard-actions",
        ),
        class_name="wizard-step",
    )


def _toggle(label: str, checked: bool, on_change) -> rx.Component:
    return rx.el.label(
        rx.el.div(
            rx.el.input(type="checkbox", checked=checked, on_change=on_change, class_name="toggle__input"),
            rx.el.div(class_name="toggle__track"),
            class_name="toggle__wrapper",
        ),
        rx.el.span(label, class_name="toggle__label"),
        class_name="toggle",
    )


def _step_output() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.p("Analysis Quality", class_name="form-label"),
            rx.el.div(
                *[
                    rx.el.button(
                        q.title(),
                        class_name=rx.cond(
                            UploadState.quality == q,
                            "seg-switch__btn seg-switch__btn--active",
                            "seg-switch__btn",
                        ),
                        on_click=UploadState.set_quality(q),
                    )
                    for q in ["standard", "high", "max"]
                ],
                class_name="seg-switch",
            ),
            class_name="form-group",
        ),
        _toggle("AI Narrative Report", UploadState.include_ai, UploadState.toggle_ai),
        _toggle("Player Tracking", UploadState.include_tracking, UploadState.toggle_tracking),
        _toggle("Heatmaps", UploadState.include_heatmaps, UploadState.toggle_heatmaps),
        rx.el.div(
            rx.el.button(
                rx.icon("arrow-left", size=16),
                "Back",
                on_click=UploadState.prev_step,
                class_name="btn-secondary",
            ),
            rx.el.button(
                rx.icon("play", size=16),
                "Start Analysis",
                on_click=UploadState.handle_submit(rx.upload_files(upload_id=UPLOAD_ID)),
                class_name="btn-primary",
            ),
            class_name="wizard-actions",
        ),
        class_name="wizard-step",
    )


def _step_submitting() -> rx.Component:
    return rx.el.div(
        rx.cond(
            UploadState.submitting,
            rx.el.div(
                rx.icon("loader-circle", size=32, color="var(--accent)"),
                rx.el.p("Uploading and queuing analysis...", class_name="submit-msg"),
                class_name="submit-state",
            ),
            rx.cond(
                UploadState.error_msg != "",
                rx.el.div(
                    rx.icon("triangle-alert", size=32, color="var(--bad)"),
                    rx.el.p(UploadState.error_msg, class_name="submit-error"),
                    rx.el.button("Try Again", on_click=UploadState.prev_step, class_name="btn-secondary"),
                    class_name="submit-state",
                ),
                rx.el.div(
                    rx.icon("circle-check", size=32, color="var(--good)"),
                    rx.el.p("Job created! Redirecting...", class_name="submit-msg"),
                    class_name="submit-state",
                ),
            ),
        ),
        class_name="wizard-step wizard-step--center",
    )


def upload_wizard() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h1("Upload Match Footage", class_name="page-title"),
            rx.el.p("Analyse tactics, track players and generate AI reports.", class_name="page-subtitle"),
            class_name="page-header",
        ),
        card(
            _step_indicator(UploadState.step),
            rx.match(
                UploadState.step,
                (0, _step_source()),
                (1, _step_match()),
                (2, _step_output()),
                (3, _step_submitting()),
                _step_source(),
            ),
            class_name="upload-card",
        ),
        on_mount=JobsState.load_teams,
        class_name="upload-view view",
    )
