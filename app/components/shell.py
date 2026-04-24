"""AppShell — TopBar, Rail (desktop), BottomTabs (mobile), TeamSwitcher, TweaksPanel."""

import reflex as rx
from app.states.app_state import AppState
from app.states.jobs_state import JobsState


_NAV_ITEMS = [
    ("grid-2x2", "Dashboard", "/"),
    ("upload", "Upload", "/upload"),
    ("file-bar-chart", "Report", "/report"),
    ("user-round", "Player", "/player/0"),
    ("settings", "Settings", "/settings"),
]


def _rail_item(icon: str, label: str, href: str) -> rx.Component:
    return rx.link(
        rx.icon(icon, size=18),
        rx.el.span(label, class_name="rail__label"),
        class_name="rail__item",
        href=href,
    )


def _bottom_tab(icon: str, label: str, href: str) -> rx.Component:
    return rx.link(
        rx.icon(icon, size=22),
        rx.el.span(label, class_name="bottom-tab__label"),
        class_name="bottom-tab__item",
        href=href,
    )


def _team_switcher() -> rx.Component:
    return rx.el.div(
        rx.el.button(
            rx.icon("shield", size=14),
            rx.el.span(AppState.active_team_name, class_name="team-switcher__name"),
            rx.icon("chevron-down", size=12),
            class_name="team-switcher__trigger",
            type="button",
        ),
        rx.el.div(
            rx.el.button(
                "All Teams",
                class_name="team-switcher__option",
                on_click=AppState.set_active_team("", "All Teams"),
                type="button",
            ),
            rx.foreach(
                JobsState.teams,
                lambda t: rx.el.button(
                    t["name"],
                    class_name="team-switcher__option",
                    on_click=AppState.set_active_team(t["id"], t["name"]),
                    type="button",
                ),
            ),
            class_name="team-switcher__menu",
        ),
        class_name="team-switcher",
    )


def _tweaks_panel() -> rx.Component:
    return rx.el.div(
        rx.el.p("Visual Style", class_name="tweaks__section-label"),
        rx.el.div(
            *[
                rx.el.button(
                    d.title(),
                    class_name=rx.cond(
                        AppState.direction == d,
                        "tweaks__option tweaks__option--active",
                        "tweaks__option",
                    ),
                    on_click=AppState.set_direction(d),
                    type="button",
                )
                for d in ["blueprint", "broadcast", "chalkboard"]
            ],
            class_name="tweaks__row",
        ),
        rx.el.p("Theme", class_name="tweaks__section-label"),
        rx.el.div(
            *[
                rx.el.button(
                    t.title(),
                    class_name=rx.cond(
                        AppState.theme == t,
                        "tweaks__option tweaks__option--active",
                        "tweaks__option",
                    ),
                    on_click=AppState.set_theme(t),
                    type="button",
                )
                for t in ["dark", "light"]
            ],
            class_name="tweaks__row",
        ),
        rx.el.p("Density", class_name="tweaks__section-label"),
        rx.el.div(
            *[
                rx.el.button(
                    d.title(),
                    class_name=rx.cond(
                        AppState.density == d,
                        "tweaks__option tweaks__option--active",
                        "tweaks__option",
                    ),
                    on_click=AppState.set_density(d),
                    type="button",
                )
                for d in ["comfortable", "compact"]
            ],
            class_name="tweaks__row",
        ),
        class_name="tweaks-panel card",
    )


def _top_bar() -> rx.Component:
    return rx.el.header(
        rx.el.div(
            rx.icon("activity", size=20, color="var(--accent)"),
            rx.el.span("SoccerCV", class_name="topbar__brand"),
            class_name="topbar__logo",
        ),
        _team_switcher(),
        rx.el.div(
            _tweaks_panel(),
            class_name="topbar__right",
        ),
        class_name="topbar",
    )


def _rail() -> rx.Component:
    return rx.el.nav(
        *[_rail_item(icon, lbl, href) for icon, lbl, href in _NAV_ITEMS],
        class_name="rail",
    )


def _bottom_tabs() -> rx.Component:
    return rx.el.nav(
        *[_bottom_tab(icon, lbl, href) for icon, lbl, href in _NAV_ITEMS],
        class_name="bottom-tabs",
    )


def app_shell(*children) -> rx.Component:
    return rx.el.html(
        rx.el.body(
            _top_bar(),
            rx.el.div(
                _rail(),
                rx.el.main(
                    *children,
                    class_name="viewport",
                ),
                class_name="shell-body",
            ),
            _bottom_tabs(),
            on_mount=AppState.load_settings,
        ),
        data_direction=AppState.direction,
        data_theme=AppState.theme,
        data_contrast=AppState.contrast,
        data_density=AppState.density,
        lang="en",
        class_name="shell",
    )
