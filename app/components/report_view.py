import reflex as rx
from app.states.report import ReportState
from app.states.upload import UploadState
from app.states.dashboard import DashboardState


def stat_bar(label: str, home_val: int, away_val: int) -> rx.Component:
    total = home_val + away_val
    total = rx.cond(total == 0, 1, total)
    home_pct = home_val / total * 100
    away_pct = away_val / total * 100
    return rx.el.div(
        rx.el.div(
            rx.el.span(home_val, class_name="text-[#7ab8e0] font-bold w-12 text-right"),
            rx.el.span(label, class_name="text-[#9aa7b8] text-sm text-center flex-1"),
            rx.el.span(away_val, class_name="text-[#f87171] font-bold w-12 text-left"),
            class_name="flex items-center justify-between mb-1",
        ),
        rx.el.div(
            rx.el.div(
                class_name="h-full bg-[#7ab8e0] rounded-l-full",
                style={"width": f"{home_pct}%"},
            ),
            rx.el.div(
                class_name="h-full bg-[#f87171] rounded-r-full",
                style={"width": f"{away_pct}%"},
            ),
            class_name="flex h-2 w-full bg-[#1e2a36] rounded-full overflow-hidden",
        ),
        class_name="mb-4",
    )


def overview_tab() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.h3(
                    "Team Comparison",
                    class_name="text-lg font-bold text-[#e2e8f0] mb-6",
                ),
                rx.foreach(
                    ReportState.team_comparison,
                    lambda stat: stat_bar(
                        stat["stat"], stat["home"].to(int), stat["away"].to(int)
                    ),
                ),
                class_name="bg-[#334155] border border-[#4a5666] rounded-2xl p-6",
            ),
            rx.el.div(
                rx.el.h3(
                    "Top Performers", class_name="text-lg font-bold text-[#e2e8f0] mb-6"
                ),
                rx.el.div(
                    rx.foreach(
                        ReportState.top_performers,
                        lambda p: rx.el.div(
                            rx.image(
                                src=f"https://api.dicebear.com/9.x/initials/svg?seed={p['name']}",
                                class_name="size-12 rounded-full",
                            ),
                            rx.el.div(
                                rx.el.p(
                                    p["name"], class_name="font-bold text-[#e2e8f0]"
                                ),
                                rx.el.p(
                                    p["position"], class_name="text-sm text-[#9aa7b8]"
                                ),
                                class_name="flex-1",
                            ),
                            rx.el.div(
                                rx.el.p(
                                    p["rating"],
                                    class_name="text-lg font-bold text-[#6ee7b7]",
                                ),
                                rx.el.p(
                                    f"{p['key_stat_label']}: {p['key_stat_value']}",
                                    class_name="text-xs text-[#9aa7b8]",
                                ),
                                class_name="text-right",
                            ),
                            class_name="flex items-center gap-4 bg-[#2b3642] p-4 rounded-xl",
                        ),
                    ),
                    class_name="flex flex-col gap-4",
                ),
                class_name="bg-[#334155] border border-[#4a5666] rounded-2xl p-6",
            ),
            class_name="grid grid-cols-1 lg:grid-cols-2 gap-6",
        )
    )


def players_tab() -> rx.Component:
    def player_row(stat: dict) -> rx.Component:
        return rx.el.tr(
            rx.el.td(stat["name"], class_name="p-4 text-[#e2e8f0] font-medium"),
            rx.el.td(stat["position"], class_name="p-4 text-[#9aa7b8]"),
            rx.el.td(stat["passes"], class_name="p-4 text-[#e2e8f0]"),
            rx.el.td(stat["accuracy"], class_name="p-4 text-[#7ab8e0]"),
            rx.el.td(stat["tackles"], class_name="p-4 text-[#e2e8f0]"),
            rx.el.td(stat["distance"], class_name="p-4 text-[#e2e8f0]"),
            rx.el.td(
                rx.el.span(
                    stat["rating"],
                    class_name="px-2.5 py-1 bg-[#064e3b] text-[#6ee7b7] rounded-lg text-sm font-bold",
                ),
                class_name="p-4",
            ),
            class_name="border-b border-[#4a5666] hover:bg-[#3d4f63] transition-colors",
        )

    return rx.el.div(
        rx.el.table(
            rx.el.thead(
                rx.el.tr(
                    rx.el.th(
                        "Player",
                        class_name="text-left p-4 text-xs font-bold text-[#9aa7b8] uppercase tracking-wider",
                    ),
                    rx.el.th(
                        "Pos",
                        class_name="text-left p-4 text-xs font-bold text-[#9aa7b8] uppercase tracking-wider",
                    ),
                    rx.el.th(
                        "Passes",
                        class_name="text-left p-4 text-xs font-bold text-[#9aa7b8] uppercase tracking-wider",
                    ),
                    rx.el.th(
                        "Accuracy",
                        class_name="text-left p-4 text-xs font-bold text-[#9aa7b8] uppercase tracking-wider",
                    ),
                    rx.el.th(
                        "Tackles",
                        class_name="text-left p-4 text-xs font-bold text-[#9aa7b8] uppercase tracking-wider",
                    ),
                    rx.el.th(
                        "Dist (km)",
                        class_name="text-left p-4 text-xs font-bold text-[#9aa7b8] uppercase tracking-wider",
                    ),
                    rx.el.th(
                        "Rating",
                        class_name="text-left p-4 text-xs font-bold text-[#9aa7b8] uppercase tracking-wider",
                    ),
                    class_name="bg-[#2b3642]",
                )
            ),
            rx.el.tbody(rx.foreach(DashboardState.player_stats, player_row)),
            class_name="w-full text-left border-collapse table-auto bg-[#334155] rounded-2xl overflow-hidden",
        )
    )


def tactics_tab() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h3(
                "Formation Phases", class_name="text-lg font-bold text-[#e2e8f0] mb-4"
            ),
            rx.el.div(
                rx.foreach(
                    ReportState.formation_phases,
                    lambda f: rx.el.div(
                        rx.el.span(
                            f["minute"],
                            class_name="text-[#7ab8e0] font-bold block mb-1",
                        ),
                        rx.el.span(
                            f["formation"],
                            class_name="text-[#e2e8f0] font-bold text-xl block mb-2",
                        ),
                        rx.el.p(f["reason"], class_name="text-[#9aa7b8] text-sm"),
                        class_name="bg-[#2b3642] p-4 rounded-xl",
                    ),
                ),
                class_name="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8",
            ),
            class_name="bg-[#334155] border border-[#4a5666] rounded-2xl p-6",
        ),
        rx.el.div(
            rx.el.h3(
                "Tactical Insights",
                class_name="text-lg font-bold text-[#e2e8f0] mt-8 mb-4",
            ),
            rx.el.div(
                rx.foreach(
                    ReportState.tactical_insights,
                    lambda t: rx.el.div(
                        rx.icon("lightbulb", class_name="text-[#fbbf24] h-6 w-6 mb-3"),
                        rx.el.h4(
                            t["title"], class_name="text-[#e2e8f0] font-bold mb-2"
                        ),
                        rx.el.p(t["description"], class_name="text-[#9aa7b8] text-sm"),
                        class_name="bg-[#334155] border border-[#4a5666] p-6 rounded-2xl",
                    ),
                ),
                class_name="grid grid-cols-1 md:grid-cols-3 gap-6",
            ),
        ),
    )


def key_events_tab() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.foreach(
                ReportState.key_moments,
                lambda e: rx.el.div(
                    rx.el.div(
                        rx.el.span(
                            e["minute"],
                            class_name="text-sm font-bold text-[#7ab8e0] w-12",
                        ),
                        rx.el.div(
                            class_name="w-3 h-3 rounded-full bg-[#e2e8f0] mx-4 relative z-10"
                        ),
                        rx.el.div(
                            rx.el.p(
                                e["event_type"], class_name="font-bold text-[#e2e8f0]"
                            ),
                            rx.el.p(
                                f"{e['player']} - {e['description']}",
                                class_name="text-[#9aa7b8] text-sm",
                            ),
                            class_name="bg-[#2b3642] p-4 rounded-xl flex-1",
                        ),
                        class_name="flex items-center",
                    ),
                    class_name="relative mb-4 before:absolute before:inset-0 before:ml-[4.25rem] before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-[#4a5666] before:to-transparent",
                ),
            ),
            class_name="bg-[#334155] border border-[#4a5666] rounded-2xl p-6",
        )
    )


def report_viewer() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.button(
                rx.icon("arrow-left", class_name="h-4 w-4 mr-2"),
                "Back to History",
                on_click=ReportState.clear_report,
                class_name="flex items-center text-[#9aa7b8] hover:text-[#7ab8e0] mb-6",
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.h2(
                        f"{ReportState.match_summary['home_team']} vs {ReportState.match_summary['away_team']}",
                        class_name="text-3xl font-bold text-[#e2e8f0]",
                    ),
                    rx.el.p(
                        f"{ReportState.match_summary['competition']} • {ReportState.match_summary['date']} • {ReportState.match_summary['venue']}",
                        class_name="text-[#9aa7b8] mt-2",
                    ),
                    class_name="flex-1",
                ),
                rx.el.div(
                    rx.el.span(
                        f"{ReportState.match_summary['score_home']} - {ReportState.match_summary['score_away']}",
                        class_name="text-5xl font-black text-[#e2e8f0] px-8 py-4 bg-[#334155] rounded-3xl border border-[#4a5666]",
                    )
                ),
                rx.el.button(
                    rx.cond(
                        ReportState.is_generating_report,
                        rx.icon("loader", class_name="h-5 w-5 animate-spin"),
                        rx.icon("download", class_name="h-5 w-5 mr-2"),
                    ),
                    "Download Report",
                    on_click=ReportState.generate_html_report,
                    class_name="ml-auto bg-[#7ab8e0] text-[#1e2a36] px-6 py-3 rounded-xl font-bold hover:bg-[#93c5e8] transition flex items-center",
                ),
                class_name="flex items-center justify-between mb-8",
            ),
        ),
        rx.el.div(
            rx.el.button(
                "Overview",
                on_click=lambda: ReportState.set_active_section("Overview"),
                class_name=rx.cond(
                    ReportState.active_section == "Overview",
                    "px-6 py-3 border-b-2 border-[#7ab8e0] text-[#7ab8e0] font-bold",
                    "px-6 py-3 text-[#9aa7b8] font-medium hover:text-[#e2e8f0]",
                ),
            ),
            rx.el.button(
                "Players",
                on_click=lambda: ReportState.set_active_section("Players"),
                class_name=rx.cond(
                    ReportState.active_section == "Players",
                    "px-6 py-3 border-b-2 border-[#7ab8e0] text-[#7ab8e0] font-bold",
                    "px-6 py-3 text-[#9aa7b8] font-medium hover:text-[#e2e8f0]",
                ),
            ),
            rx.el.button(
                "Tactics",
                on_click=lambda: ReportState.set_active_section("Tactics"),
                class_name=rx.cond(
                    ReportState.active_section == "Tactics",
                    "px-6 py-3 border-b-2 border-[#7ab8e0] text-[#7ab8e0] font-bold",
                    "px-6 py-3 text-[#9aa7b8] font-medium hover:text-[#e2e8f0]",
                ),
            ),
            rx.el.button(
                "Key Events",
                on_click=lambda: ReportState.set_active_section("Key Events"),
                class_name=rx.cond(
                    ReportState.active_section == "Key Events",
                    "px-6 py-3 border-b-2 border-[#7ab8e0] text-[#7ab8e0] font-bold",
                    "px-6 py-3 text-[#9aa7b8] font-medium hover:text-[#e2e8f0]",
                ),
            ),
            class_name="flex border-b border-[#4a5666] mb-8",
        ),
        rx.match(
            ReportState.active_section,
            ("Overview", overview_tab()),
            ("Players", players_tab()),
            ("Tactics", tactics_tab()),
            ("Key Events", key_events_tab()),
            overview_tab(),
        ),
        class_name="animate-in fade-in duration-500",
    )


def reports_grid() -> rx.Component:
    return rx.el.div(
        rx.el.h2(
            "Analysis Reports", class_name="text-3xl font-bold text-[#e2e8f0] mb-2"
        ),
        rx.el.p(
            "Select a completed match analysis to view the detailed report.",
            class_name="text-[#9aa7b8] mb-8",
        ),
        rx.cond(
            UploadState.jobs.length() > 0,
            rx.el.div(
                rx.foreach(
                    UploadState.jobs,
                    lambda job: rx.cond(
                        job["status"] == "Complete",
                        rx.el.div(
                            rx.el.h3(
                                job["match_name"],
                                class_name="font-bold text-[#e2e8f0] mb-2",
                            ),
                            rx.el.p(
                                f"Analyzed: {job['upload_time']}",
                                class_name="text-[#9aa7b8] text-sm mb-4",
                            ),
                            rx.el.button(
                                "View Report",
                                on_click=lambda: ReportState.load_report(job["id"]),
                                class_name="w-full py-2 bg-[#2b3642] text-[#7ab8e0] border border-[#7ab8e0] rounded-lg font-semibold hover:bg-[#7ab8e0] hover:text-[#1e2a36] transition",
                            ),
                            class_name="bg-[#334155] border border-[#4a5666] p-6 rounded-2xl shadow-sm hover:shadow-md hover:border-[#7ab8e0] transition-all",
                        ),
                        rx.fragment(),
                    ),
                ),
                class_name="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6",
            ),
            rx.el.div(
                rx.icon("file-x-2", class_name="h-12 w-12 text-[#4a5666] mb-4"),
                rx.el.h3(
                    "No reports available",
                    class_name="text-xl font-bold text-[#9aa7b8]",
                ),
                class_name="flex flex-col items-center justify-center p-24 border-2 border-dashed border-[#4a5666] rounded-3xl",
            ),
        ),
        class_name="animate-in fade-in duration-500",
    )


def report_view() -> rx.Component:
    return rx.cond(ReportState.report_loaded, report_viewer(), reports_grid())