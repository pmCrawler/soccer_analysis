"""Chart components — Sparkline, MomentumChart, CompareBar, StatusDot."""

import reflex as rx


def sparkline(data: list, color: str = "var(--accent)", height: int = 40) -> rx.Component:
    """Simple SVG polyline sparkline."""
    if not data:
        return rx.el.div(style={"height": f"{height}px"})
    return rx.el.svg(
        rx.el.polyline(
            points=" ".join(
                f"{i * 10},{height - (v * height / max(data or [1]))}"
                for i, v in enumerate(data)
            ),
            fill="none",
            stroke=color,
            stroke_width="2",
        ),
        width=str(len(data) * 10),
        height=str(height),
        style={"overflow": "visible"},
    )


def momentum_chart(data: list[dict]) -> rx.Component:
    """Momentum chart rendered as SVG bars."""
    return rx.el.div(
        rx.el.svg(
            rx.foreach(
                data,
                lambda d: rx.el.rect(
                    x=str(d.get("minute", 0) * 6),
                    y=rx.cond(d.get("home", 0) > 0, str(40 - d.get("home", 0) * 4), "40"),
                    width="5",
                    height=rx.cond(
                        d.get("home", 0) > 0,
                        str(d.get("home", 0) * 4),
                        str(abs(d.get("away", 0)) * 4),
                    ),
                    fill=rx.cond(d.get("home", 0) > 0, "var(--accent)", "var(--bad)"),
                    opacity="0.8",
                ),
            ),
            width="540",
            height="80",
            view_box="0 0 540 80",
            style={"width": "100%", "height": "80px"},
        ),
        class_name="momentum-chart",
    )


def compare_bar(label_a, val_a, label_b, val_b) -> rx.Component:
    total = val_a.to(float) + val_b.to(float)
    pct_a = rx.cond(total > 0, (val_a.to(float) / total) * 100, 50)
    return rx.el.div(
        rx.el.div(
            rx.el.span(label_a, class_name="compare-bar__label"),
            rx.el.span(val_a.to_string() + "%", class_name="compare-bar__value"),
            class_name="compare-bar__side compare-bar__side--a",
        ),
        rx.el.div(
            rx.el.div(
                style={
                    "width": pct_a.to_string() + "%",
                    "height": "100%",
                    "background": "var(--accent)",
                    "border_radius": "2px 0 0 2px",
                    "transition": "width 0.4s",
                }
            ),
            style={
                "width": "100%",
                "height": "8px",
                "background": "var(--bad)",
                "border_radius": "2px",
                "overflow": "hidden",
            },
        ),
        rx.el.div(
            rx.el.span(val_b.to_string() + "%", class_name="compare-bar__value"),
            rx.el.span(label_b, class_name="compare-bar__label"),
            class_name="compare-bar__side compare-bar__side--b",
        ),
        class_name="compare-bar",
    )
