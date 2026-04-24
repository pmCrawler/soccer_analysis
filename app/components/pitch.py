"""SVG Pitch component with 5 overlay modes."""

import reflex as rx

# Pitch dimensions in metres (standard FIFA): 105 × 68
# SVG viewport scaled to 630 × 408 (6× scale factor)
_W = 630
_H = 408
_S = 6.0   # scale factor


def _line(x1, y1, x2, y2, **props) -> rx.Component:
    return rx.el.line(
        x1=str(x1 * _S), y1=str(y1 * _S),
        x2=str(x2 * _S), y2=str(y2 * _S),
        stroke="var(--pitch-line)", stroke_width="1.5", **props
    )


def _rect(x, y, w, h, **props) -> rx.Component:
    return rx.el.rect(
        x=str(x * _S), y=str(y * _S),
        width=str(w * _S), height=str(h * _S),
        fill="none", stroke="var(--pitch-line)", stroke_width="1.5", **props
    )


def _circle(cx, cy, r, **props) -> rx.Component:
    return rx.el.circle(
        cx=str(cx * _S), cy=str(cy * _S), r=str(r * _S),
        fill="none", stroke="var(--pitch-line)", stroke_width="1.5", **props
    )


def pitch_lines() -> rx.Component:
    return rx.el.g(
        # Pitch boundary
        _rect(0, 0, 105, 68),
        # Halfway line
        _line(52.5, 0, 52.5, 68),
        # Centre circle
        _circle(52.5, 34, 9.15),
        # Centre spot
        rx.el.circle(cx=str(52.5 * _S), cy=str(34 * _S), r="2", fill="var(--pitch-line)"),
        # Left penalty area
        _rect(0, 13.85, 16.5, 40.3),
        # Left goal area
        _rect(0, 24.84, 5.5, 18.32),
        # Left penalty spot
        rx.el.circle(cx=str(11 * _S), cy=str(34 * _S), r="2", fill="var(--pitch-line)"),
        # Left arc
        rx.el.path(
            d=f"M {9.15 * _S * 0.9:.1f} {(34 - 9.15) * _S:.1f} A {9.15 * _S:.1f} {9.15 * _S:.1f} 0 0 1 {(11 + 9.15 * 0.9) * _S:.1f} {(34 + 9.15 * 0.5) * _S:.1f}",
            fill="none", stroke="var(--pitch-line)", stroke_width="1.5",
        ),
        # Right penalty area
        _rect(88.5, 13.85, 16.5, 40.3),
        # Right goal area
        _rect(99.5, 24.84, 5.5, 18.32),
        # Right penalty spot
        rx.el.circle(cx=str(94 * _S), cy=str(34 * _S), r="2", fill="var(--pitch-line)"),
        # Left goal
        _rect(-1.5, 29.85, 1.5, 8.3),
        # Right goal
        _rect(105, 29.85, 1.5, 8.3),
        # Grid lines (light)
        *[_line(i * 17.5, 0, i * 17.5, 68, stroke_opacity="0.15") for i in range(1, 6)],
        *[_line(0, j * 17, 105, j * 17, stroke_opacity="0.15") for j in range(1, 4)],
    )


def player_marker(x: float, y: float, label: str, color: str = "var(--accent)") -> rx.Component:
    return rx.el.g(
        rx.el.circle(cx=str(x * _S), cy=str(y * _S), r="8", fill=color, fill_opacity="0.85"),
        rx.el.text(label, x=str(x * _S), y=str(y * _S + 1), text_anchor="middle",
                   dominant_baseline="middle", fill="white", font_size="9", font_weight="bold"),
    )


def pass_line(x1: float, y1: float, x2: float, y2: float, weight: int = 1) -> rx.Component:
    width = max(1, min(weight / 3, 5))
    return rx.el.line(
        x1=str(x1 * _S), y1=str(y1 * _S),
        x2=str(x2 * _S), y2=str(y2 * _S),
        stroke="var(--accent)", stroke_width=str(width), stroke_opacity="0.6",
    )


def shot_marker(x: float, y: float, on_target: bool = True) -> rx.Component:
    return rx.el.circle(
        cx=str(x * _S), cy=str(y * _S), r="6",
        fill=rx.cond(on_target, "var(--good)", "var(--warn)"),
        fill_opacity="0.8",
    )


def svg_pitch(
    overlay_mode: str = "formation",
    avg_positions_a: list = None,
    avg_positions_b: list = None,
    pass_edges: list = None,
    shot_data: list = None,
) -> rx.Component:
    return rx.el.svg(
        rx.el.rect(width=str(_W), height=str(_H), fill="var(--pitch)"),
        pitch_lines(),
        width=str(_W),
        height=str(_H),
        view_box=f"0 0 {_W} {_H}",
        style={"width": "100%", "max_width": f"{_W}px", "height": "auto"},
        class_name="pitch-svg",
    )
