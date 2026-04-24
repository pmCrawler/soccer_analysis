"""Shared atomic UI components."""

import reflex as rx


def chip(label: str, active: bool = False, on_click=None) -> rx.Component:
    return rx.el.button(
        label,
        class_name=rx.cond(
            active,
            "chip chip--active",
            "chip",
        ),
        on_click=on_click,
    )


def status_dot(status: str) -> rx.Component:
    color_map = {
        "ready": "var(--good)",
        "failed": "var(--bad)",
        "live": "var(--accent)",
        "queued": "var(--fg-3)",
        "preprocessing": "var(--warn)",
        "calibrating": "var(--warn)",
        "analyzing": "var(--warn)",
        "reporting": "var(--warn)",
    }
    return rx.el.span(
        style={
            "display": "inline-block",
            "width": "8px",
            "height": "8px",
            "border_radius": "50%",
            "background": rx.match(
                status,
                ("ready", "var(--good)"),
                ("failed", "var(--bad)"),
                ("live", "var(--accent)"),
                ("queued", "var(--fg-3)"),
                "var(--warn)",
            ),
            "flex_shrink": "0",
        }
    )


def label(text: str, **props) -> rx.Component:
    return rx.el.span(text, class_name="label", **props)


def eyebrow(text: str) -> rx.Component:
    return rx.el.p(text, class_name="eyebrow")


def card(*children, **props) -> rx.Component:
    cls = props.pop("class_name", "")
    return rx.el.div(*children, class_name=f"card {cls}".strip(), **props)


def seg_switch(options: list[tuple[str, str]], value: str, on_change) -> rx.Component:
    """Segmented switch — options is list of (label, value) tuples."""
    return rx.el.div(
        *[
            rx.el.button(
                opt_label,
                class_name=rx.cond(value == opt_val, "seg-switch__btn seg-switch__btn--active", "seg-switch__btn"),
                on_click=lambda v=opt_val: on_change(v),
            )
            for opt_label, opt_val in options
        ],
        class_name="seg-switch",
    )


def mini_bar(value, max_value: float = 100.0, color: str = "var(--accent)") -> rx.Component:
    pct = rx.cond(max_value > 0, (value.to(float) / max_value) * 100, 0)
    return rx.el.div(
        rx.el.div(
            style={
                "width": pct.to_string() + "%",
                "height": "100%",
                "background": color,
                "border_radius": "2px",
                "transition": "width 0.3s ease",
            }
        ),
        style={
            "width": "100%",
            "height": "6px",
            "background": "var(--border)",
            "border_radius": "2px",
            "overflow": "hidden",
        },
    )


def progress_bar(value) -> rx.Component:
    # value is 0.0–1.0; cast to float before arithmetic to support ObjectItemOperation Vars
    pct = value.to(float) * 100
    return rx.el.div(
        rx.el.div(
            style={
                "width": pct.to_string() + "%",
                "height": "100%",
                "background": "var(--accent)",
                "border_radius": "4px",
                "transition": "width 0.4s ease",
            }
        ),
        style={
            "width": "100%",
            "height": "8px",
            "background": "var(--border)",
            "border_radius": "4px",
            "overflow": "hidden",
        },
    )
