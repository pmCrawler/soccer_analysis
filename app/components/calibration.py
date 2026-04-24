"""Calibration view — shows frame image for reference, collects 4+ click coordinates via inputs."""

import reflex as rx
from app.states.calibration_state import CalibrationState, PITCH_LANDMARKS
from app.components.primitives import card


def calibration_view() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h1("Camera Calibration", class_name="page-title"),
            rx.el.p(
                "Use the image as reference. Enter the pixel coordinates of each pitch landmark and select its real-world position.",
                class_name="page-subtitle",
            ),
            class_name="page-header",
        ),
        rx.el.div(
            card(
                rx.cond(
                    CalibrationState.frame_url != "",
                    rx.image(
                        src=CalibrationState.frame_url,
                        style={"width": "100%", "border_radius": "8px"},
                    ),
                    rx.el.div(
                        rx.icon("image", size=48, color="var(--fg-3)"),
                        rx.el.p("Frame will appear here after preprocessing.", class_name="placeholder-text"),
                        style={"display": "flex", "flex_direction": "column", "align_items": "center", "padding": "var(--d-7)"},
                    ),
                ),
                class_name="calib-frame-card",
            ),
            card(
                rx.el.h3("Calibration Points", class_name="panel-title"),
                rx.el.p(
                    CalibrationState.clicks_count.to_string() + " / 4+ points added",
                    class_name="calib-count",
                ),
                rx.el.div(
                    rx.el.div(
                        rx.el.label(
                            rx.el.span("Pixel X", class_name="form-label"),
                            rx.el.input(
                                type="number",
                                placeholder="e.g. 320",
                                value=CalibrationState.pixel_x_input,
                                on_change=CalibrationState.set_pixel_x,
                                class_name="form-input",
                            ),
                            class_name="form-field",
                        ),
                        rx.el.label(
                            rx.el.span("Pixel Y", class_name="form-label"),
                            rx.el.input(
                                type="number",
                                placeholder="e.g. 240",
                                value=CalibrationState.pixel_y_input,
                                on_change=CalibrationState.set_pixel_y,
                                class_name="form-input",
                            ),
                            class_name="form-field",
                        ),
                        class_name="form-row",
                    ),
                    rx.el.label(
                        rx.el.span("Pitch Landmark", class_name="form-label"),
                        rx.el.select(
                            *[
                                rx.el.option(lm[0], value=str(i))
                                for i, lm in enumerate(PITCH_LANDMARKS)
                            ],
                            value=CalibrationState.selected_landmark.to_string(),
                            on_change=CalibrationState.set_landmark,
                            class_name="form-select",
                        ),
                        class_name="form-field",
                    ),
                    rx.el.button(
                        "Add Point",
                        on_click=CalibrationState.confirm_point,
                        class_name="btn-secondary",
                    ),
                    class_name="calib-confirm",
                ),
                rx.el.div(
                    rx.foreach(
                        CalibrationState.clicks,
                        lambda c: rx.el.div(
                            rx.el.span(
                                "px(", c["pixel_x"].to_string(), ", ", c["pixel_y"].to_string(), ")",
                                class_name="calib-point__pixel",
                            ),
                            rx.el.span("→", class_name="calib-point__arrow"),
                            rx.el.span(
                                "(", c["pitch_x"].to_string(), ", ", c["pitch_y"].to_string(), "m)",
                                class_name="calib-point__pitch",
                            ),
                            class_name="calib-point",
                        ),
                    ),
                    class_name="calib-points-list",
                ),
                rx.cond(
                    CalibrationState.clicks_count > 0,
                    rx.el.button(
                        "Remove Last",
                        on_click=CalibrationState.remove_last_click,
                        class_name="btn-secondary",
                    ),
                    rx.el.div(),
                ),
                rx.cond(
                    CalibrationState.error != "",
                    rx.el.p(CalibrationState.error, class_name="form-error"),
                    rx.el.div(),
                ),
                rx.el.button(
                    "Submit Calibration",
                    on_click=CalibrationState.submit_calibration,
                    disabled=CalibrationState.clicks_count < 4,
                    class_name="btn-primary",
                ),
                class_name="calib-controls",
            ),
            class_name="calib-layout",
        ),
        on_mount=CalibrationState.load_frame,
        class_name="calibration-view view",
    )
