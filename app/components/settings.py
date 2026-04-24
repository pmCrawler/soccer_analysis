"""Settings view."""

import reflex as rx
from app.states.app_state import AppState
from app.components.primitives import card


def _option_btn(label: str, value: str, current, on_click) -> rx.Component:
    return rx.el.button(
        label,
        class_name=rx.cond(
            current == value,
            "seg-switch__btn seg-switch__btn--active",
            "seg-switch__btn",
        ),
        on_click=on_click,
    )


def _setting_row(title: str, description: str, control: rx.Component) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.p(title, class_name="setting-row__title"),
            rx.el.p(description, class_name="setting-row__desc"),
            class_name="setting-row__text",
        ),
        control,
        class_name="setting-row",
    )


def settings_view() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h1("Settings", class_name="page-title"),
            class_name="page-header",
        ),
        card(
            rx.el.h3("Appearance", class_name="section-title"),
            _setting_row(
                "Visual Style",
                "Colour palette and pitch rendering style.",
                rx.el.div(
                    *[
                        _option_btn(d.title(), d, AppState.direction, AppState.set_direction(d))
                        for d in ["blueprint", "broadcast", "chalkboard"]
                    ],
                    class_name="seg-switch",
                ),
            ),
            _setting_row(
                "Theme",
                "Light or dark colour scheme.",
                rx.el.div(
                    *[
                        _option_btn(t.title(), t, AppState.theme, AppState.set_theme(t))
                        for t in ["dark", "light"]
                    ],
                    class_name="seg-switch",
                ),
            ),
            _setting_row(
                "Contrast",
                "Increase border and text contrast for accessibility.",
                rx.el.div(
                    *[
                        _option_btn(c.title(), c, AppState.contrast, AppState.set_contrast(c))
                        for c in ["normal", "high"]
                    ],
                    class_name="seg-switch",
                ),
            ),
            _setting_row(
                "Density",
                "Control spacing throughout the interface.",
                rx.el.div(
                    *[
                        _option_btn(d.title(), d, AppState.density, AppState.set_density(d))
                        for d in ["comfortable", "compact"]
                    ],
                    class_name="seg-switch",
                ),
            ),
            class_name="settings-card",
        ),
        on_mount=AppState.load_settings,
        class_name="settings-view view",
    )
