"""Player deep-dive view."""

import reflex as rx
from app.states.player_state import PlayerState
from app.components.primitives import card


def _tab(label: str, value: str) -> rx.Component:
    return rx.el.button(
        label,
        class_name=rx.cond(
            PlayerState.active_tab == value,
            "tab tab--active",
            "tab",
        ),
        on_click=PlayerState.set_tab(value),
    )


def _stat_row(label: str, value) -> rx.Component:
    return rx.el.div(
        rx.el.span(label, class_name="stat-key"),
        rx.el.span(value, class_name="stat-val"),
        class_name="stat-row",
    )


def _overview_tab() -> rx.Component:
    return card(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.el.span(PlayerState.player.get("number", ""), class_name="player-jersey"),
                    class_name="player-avatar",
                ),
                rx.el.div(
                    rx.el.h2(PlayerState.player.get("name", ""), class_name="player-name"),
                    rx.el.p(
                        PlayerState.player.get("position", ""), " · ", PlayerState.player.get("team", ""),
                        class_name="player-role",
                    ),
                    class_name="player-info",
                ),
                class_name="player-hero",
            ),
            rx.el.div(
                _stat_row("Rating", PlayerState.player.get("rating", "—")),
                _stat_row("Passes", PlayerState.player.get("passes", "—")),
                _stat_row("Pass Accuracy", PlayerState.player.get("pass_accuracy", 0).to_string() + "%"),
                _stat_row("Tackles", PlayerState.player.get("tackles", "—")),
                _stat_row("Distance (km)", PlayerState.player.get("distance", "—")),
                _stat_row("Touches", PlayerState.player.get("touches", "—")),
                _stat_row("Duels", PlayerState.player.get("duels", "—")),
                class_name="stats-list",
            ),
        ),
    )


def player_view() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h1("Player Profile", class_name="page-title"),
            class_name="page-header",
        ),
        rx.cond(
            PlayerState.player,
            rx.el.div(
                rx.el.div(
                    _tab("Overview", "overview"),
                    _tab("Heatmap", "heat"),
                    _tab("Passes", "passes"),
                    _tab("Timeline", "timeline"),
                    class_name="tab-bar",
                ),
                rx.match(
                    PlayerState.active_tab,
                    ("overview", _overview_tab()),
                    ("heat", card(rx.el.p("Heatmap coming soon", class_name="placeholder-text"))),
                    ("passes", card(rx.el.p("Pass map coming soon", class_name="placeholder-text"))),
                    ("timeline", card(rx.el.p("Timeline coming soon", class_name="placeholder-text"))),
                    _overview_tab(),
                ),
            ),
            rx.el.div(
                rx.cond(
                    PlayerState.loading,
                    rx.el.p("Loading...", class_name="loading-msg"),
                    rx.el.p("No player data. Navigate from a report page.", class_name="empty-state__body"),
                ),
                class_name="empty-state",
            ),
        ),
        on_mount=PlayerState.load_player,
        class_name="player-view view",
    )
