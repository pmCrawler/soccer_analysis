import reflex as rx
from app.states.dashboard import DashboardState


def filter_select(
    options: list[str], value: str, on_change: rx.event.EventType, icon: str
) -> rx.Component:
    return rx.el.div(
        rx.icon(
            icon,
            class_name="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#9aa7b8] pointer-events-none",
        ),
        rx.el.select(
            rx.foreach(options, lambda opt: rx.el.option(opt, value=opt)),
            value=value,
            on_change=on_change,
            class_name="w-full pl-10 pr-8 py-2.5 bg-[#334155] border border-[#4a5666] rounded-xl text-sm text-[#e2e8f0] appearance-none focus:outline-none focus:border-[#7ab8e0] focus:ring-1 focus:ring-[#7ab8e0] cursor-pointer",
        ),
        rx.icon(
            "chevron-down",
            class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#9aa7b8] pointer-events-none",
        ),
        class_name="relative w-full md:flex-1",
    )


def filter_bar() -> rx.Component:
    return rx.el.div(
        filter_select(
            DashboardState.available_matches,
            DashboardState.selected_match,
            DashboardState.set_selected_match,
            "trophy",
        ),
        filter_select(
            DashboardState.available_players,
            DashboardState.selected_player,
            DashboardState.set_selected_player,
            "user",
        ),
        filter_select(
            DashboardState.time_segments,
            DashboardState.selected_time_segment,
            DashboardState.set_selected_time_segment,
            "clock",
        ),
        filter_select(
            DashboardState.event_filters,
            DashboardState.selected_event_filter,
            DashboardState.set_selected_event_filter,
            "filter",
        ),
        class_name="flex flex-col md:flex-row gap-4 mb-8",
    )


def kpi_card(title: str, value: str, icon: str, border_color: str) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    title,
                    class_name="text-xs uppercase font-bold text-[#9aa7b8] tracking-wider",
                ),
                rx.el.h3(value, class_name="text-2xl font-bold text-[#e2e8f0] mt-1"),
                class_name="flex flex-col",
            ),
            rx.el.div(
                rx.icon(icon, class_name="h-6 w-6 text-[#9aa7b8] opacity-70"),
                class_name="p-3 bg-[#2b3642] rounded-xl",
            ),
            class_name="flex items-center justify-between",
        ),
        class_name=f"bg-[#334155] border border-[#4a5666] border-l-4 {border_color} rounded-2xl p-5 shadow-sm",
    )


def kpi_grid() -> rx.Component:
    return rx.el.div(
        kpi_card(
            "Total Passes",
            DashboardState.total_passes.to_string(),
            "arrow-right-left",
            "border-l-[#7ab8e0]",
        ),
        kpi_card(
            "Total Shots",
            DashboardState.total_shots.to_string(),
            "target",
            "border-l-[#f87171]",
        ),
        kpi_card(
            "Tackles Won",
            DashboardState.total_tackles.to_string(),
            "shield",
            "border-l-[#6ee7b7]",
        ),
        kpi_card(
            "Distance (km)",
            DashboardState.total_distance_km.to_string(),
            "activity",
            "border-l-[#fbbf24]",
        ),
        kpi_card(
            "Goals Scored",
            DashboardState.goals_scored.to_string(),
            "goal",
            "border-l-[#a78bfa]",
        ),
        kpi_card(
            "Total Corners",
            DashboardState.corners.to_string(),
            "flag",
            "border-l-[#f472b6]",
        ),
        class_name="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 mb-8",
    )


def chart_container(
    title: str, content: rx.Component, class_name: str = ""
) -> rx.Component:
    return rx.el.div(
        rx.el.h3(title, class_name="text-base font-bold text-[#e2e8f0] mb-6"),
        content,
        class_name=f"bg-[#334155] border border-[#4a5666] rounded-2xl p-6 {class_name}",
    )


def charts_section() -> rx.Component:
    return rx.el.div(
        chart_container(
            "Possession Breakdown",
            rx.el.div(
                rx.recharts.pie_chart(
                    rx.recharts.pie(
                        data=DashboardState.possession_data,
                        data_key="value",
                        name_key="name",
                        cx="50%",
                        cy="50%",
                        inner_radius=60,
                        outer_radius=80,
                        stroke="#334155",
                        stroke_width=2,
                    ),
                    rx.recharts.tooltip(
                        content_style={
                            "backgroundColor": "#1e2a36",
                            "borderColor": "#4a5666",
                            "color": "#e2e8f0",
                        },
                        item_style={"color": "#e2e8f0"},
                    ),
                    height=250,
                    width="100%",
                ),
                rx.el.div(
                    rx.el.div(
                        rx.el.div(class_name="w-3 h-3 rounded-full bg-[#7ab8e0]"),
                        rx.el.span("Home", class_name="text-sm text-[#9aa7b8]"),
                        class_name="flex items-center gap-2",
                    ),
                    rx.el.div(
                        rx.el.div(class_name="w-3 h-3 rounded-full bg-[#4a5666]"),
                        rx.el.span("Away", class_name="text-sm text-[#9aa7b8]"),
                        class_name="flex items-center gap-2",
                    ),
                    class_name="flex justify-center gap-6 mt-4",
                ),
                class_name="flex flex-col",
            ),
        ),
        chart_container(
            "Passing Accuracy (%)",
            rx.recharts.bar_chart(
                rx.recharts.cartesian_grid(
                    stroke_dasharray="3 3", stroke="#4a5666", horizontal=False
                ),
                rx.recharts.x_axis(
                    type_="number",
                    domain=[0, 100],
                    stroke="#9aa7b8",
                    tick_line=False,
                    axis_line=False,
                ),
                rx.recharts.y_axis(
                    data_key="name",
                    type_="category",
                    width=80,
                    stroke="#9aa7b8",
                    tick_line=False,
                    axis_line=False,
                ),
                rx.recharts.tooltip(
                    content_style={
                        "backgroundColor": "#1e2a36",
                        "borderColor": "#4a5666",
                        "color": "#e2e8f0",
                    },
                    cursor={"fill": "#3d4f63"},
                ),
                rx.recharts.bar(
                    data_key="accuracy",
                    fill="#7ab8e0",
                    radius=[0, 4, 4, 0],
                    bar_size=20,
                ),
                data=DashboardState.passing_accuracy_data,
                layout="vertical",
                height=300,
                width="100%",
                margin={"left": 0, "right": 20, "top": 0, "bottom": 0},
            ),
        ),
        chart_container(
            "Match Momentum Timeline",
            rx.recharts.line_chart(
                rx.recharts.cartesian_grid(
                    stroke_dasharray="3 3", stroke="#4a5666", vertical=False
                ),
                rx.recharts.x_axis(
                    data_key="minute",
                    stroke="#9aa7b8",
                    tick_line=False,
                    axis_line=False,
                ),
                rx.recharts.y_axis(
                    domain=[0, 100], stroke="#9aa7b8", tick_line=False, axis_line=False
                ),
                rx.recharts.tooltip(
                    content_style={
                        "backgroundColor": "#1e2a36",
                        "borderColor": "#4a5666",
                        "color": "#e2e8f0",
                    }
                ),
                rx.recharts.line(
                    data_key="home",
                    stroke="#7ab8e0",
                    type_="monotone",
                    stroke_width=3,
                    dot=False,
                ),
                rx.recharts.line(
                    data_key="away",
                    stroke="#f87171",
                    type_="monotone",
                    stroke_width=3,
                    dot=False,
                ),
                data=DashboardState.match_momentum_data,
                height=300,
                width="100%",
                margin={"left": -20, "right": 10, "top": 10, "bottom": 0},
            ),
            class_name="lg:col-span-2",
        ),
        chart_container(
            "Defensive Actions",
            rx.recharts.bar_chart(
                rx.recharts.cartesian_grid(
                    stroke_dasharray="3 3", stroke="#4a5666", vertical=False
                ),
                rx.recharts.x_axis(
                    data_key="action",
                    stroke="#9aa7b8",
                    tick_line=False,
                    axis_line=False,
                ),
                rx.recharts.y_axis(stroke="#9aa7b8", tick_line=False, axis_line=False),
                rx.recharts.tooltip(
                    content_style={
                        "backgroundColor": "#1e2a36",
                        "borderColor": "#4a5666",
                        "color": "#e2e8f0",
                    },
                    cursor={"fill": "#3d4f63"},
                ),
                rx.recharts.bar(data_key="home", fill="#7ab8e0", radius=[4, 4, 0, 0]),
                rx.recharts.bar(data_key="away", fill="#f87171", radius=[4, 4, 0, 0]),
                data=DashboardState.defensive_actions_data,
                height=300,
                width="100%",
                margin={"left": -20, "right": 10, "top": 10, "bottom": 0},
            ),
        ),
        chart_container(
            "Attacking Zones Distribution",
            rx.recharts.bar_chart(
                rx.recharts.cartesian_grid(
                    stroke_dasharray="3 3", stroke="#4a5666", horizontal=False
                ),
                rx.recharts.x_axis(
                    type_="number",
                    domain=[0, 100],
                    stroke="#9aa7b8",
                    tick_line=False,
                    axis_line=False,
                ),
                rx.recharts.y_axis(
                    data_key="zone",
                    type_="category",
                    stroke="#9aa7b8",
                    tick_line=False,
                    axis_line=False,
                ),
                rx.recharts.tooltip(
                    content_style={
                        "backgroundColor": "#1e2a36",
                        "borderColor": "#4a5666",
                        "color": "#e2e8f0",
                    },
                    cursor={"fill": "#3d4f63"},
                ),
                rx.recharts.bar(data_key="home", stack_id="a", fill="#7ab8e0"),
                rx.recharts.bar(
                    data_key="away", stack_id="a", fill="#f87171", radius=[0, 4, 4, 0]
                ),
                data=DashboardState.attacking_zones_data,
                layout="vertical",
                height=300,
                width="100%",
                margin={"left": 0, "right": 20, "top": 10, "bottom": 0},
            ),
        ),
        class_name="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8",
    )


def dynamics_card() -> rx.Component:
    return rx.el.div(
        rx.el.h3(
            "Match Dynamics", class_name="text-base font-bold text-[#e2e8f0] mb-6"
        ),
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Formation Strategy",
                    class_name="text-xs uppercase text-[#9aa7b8] font-bold",
                ),
                rx.el.p(
                    "4-3-3 vs 3-4-3", class_name="text-xl font-bold text-[#7ab8e0] mt-1"
                ),
                rx.el.div(
                    rx.el.span("Stability:", class_name="text-sm text-[#9aa7b8] mr-2"),
                    rx.el.span(
                        f"{DashboardState.formation_stability}%",
                        class_name="text-sm font-semibold text-[#e2e8f0]",
                    ),
                    class_name="mt-2",
                ),
                class_name="p-4 bg-[#2b3642] rounded-xl",
            ),
            rx.el.div(
                rx.el.span(
                    "Defensive Line",
                    class_name="text-xs uppercase text-[#9aa7b8] font-bold",
                ),
                rx.el.p(
                    f"{DashboardState.defensive_line_avg}m",
                    class_name="text-xl font-bold text-[#6ee7b7] mt-1",
                ),
                rx.el.div(
                    rx.el.span(
                        "Average from goal", class_name="text-sm text-[#9aa7b8]"
                    ),
                    class_name="mt-2",
                ),
                class_name="p-4 bg-[#2b3642] rounded-xl",
            ),
            rx.el.div(
                rx.el.span(
                    "Possession Dominance",
                    class_name="text-xs uppercase text-[#9aa7b8] font-bold",
                ),
                rx.el.div(
                    rx.el.div(class_name="h-full bg-[#7ab8e0] w-[60%]"),
                    rx.el.div(class_name="h-full bg-[#f87171] w-[40%]"),
                    class_name="h-4 w-full rounded-full overflow-hidden flex mt-3",
                ),
                rx.el.div(
                    rx.el.span("Home", class_name="text-xs text-[#7ab8e0]"),
                    rx.el.span("Away", class_name="text-xs text-[#f87171]"),
                    class_name="flex justify-between mt-2",
                ),
                class_name="p-4 bg-[#2b3642] rounded-xl",
            ),
            class_name="grid grid-cols-1 md:grid-cols-3 gap-4",
        ),
        class_name="bg-[#334155] border border-[#4a5666] rounded-2xl p-6 mb-8",
    )


def player_table_row(stat: dict) -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            rx.el.div(
                rx.image(
                    src=f"https://api.dicebear.com/9.x/initials/svg?seed={stat['name']}",
                    class_name="size-8 rounded-full bg-[#4a5666]",
                ),
                rx.el.span(stat["name"], class_name="font-semibold text-[#e2e8f0]"),
                class_name="flex items-center gap-3",
            ),
            class_name="p-4 whitespace-nowrap",
        ),
        rx.el.td(stat["position"], class_name="p-4 whitespace-nowrap text-[#9aa7b8]"),
        rx.el.td(
            stat["passes"].to_string(), class_name="p-4 whitespace-nowrap font-medium"
        ),
        rx.el.td(
            stat["accuracy"],
            class_name="p-4 whitespace-nowrap font-medium text-[#7ab8e0]",
        ),
        rx.el.td(
            stat["tackles"].to_string(), class_name="p-4 whitespace-nowrap font-medium"
        ),
        rx.el.td(stat["distance"], class_name="p-4 whitespace-nowrap font-medium"),
        rx.el.td(
            rx.el.span(
                stat["rating"],
                class_name="px-2.5 py-1 bg-[#064e3b] text-[#6ee7b7] rounded-lg text-sm font-bold",
            ),
            class_name="p-4 whitespace-nowrap",
        ),
        class_name="border-b border-[#4a5666] hover:bg-[#3d4f63] transition-colors",
    )


def player_performance_table() -> rx.Component:
    return rx.el.div(
        rx.el.h3(
            "Player Performance",
            class_name="text-base font-bold text-[#e2e8f0] mb-6 px-6 pt-6",
        ),
        rx.el.div(
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
                        class_name="bg-[#2b3642] border-y border-[#4a5666]",
                    )
                ),
                rx.el.tbody(rx.foreach(DashboardState.player_stats, player_table_row)),
                class_name="w-full text-left border-collapse table-auto",
            ),
            class_name="overflow-x-auto pb-4",
        ),
        class_name="bg-[#334155] border border-[#4a5666] rounded-2xl shadow-sm overflow-hidden",
    )


def dashboard_view() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h1(
                "Match Dashboard", class_name="text-3xl font-bold text-[#e2e8f0] mb-2"
            ),
            rx.el.p(
                "Comprehensive tactical analysis and player performance metrics",
                class_name="text-[#9aa7b8] mb-8",
            ),
            class_name="mb-6",
        ),
        filter_bar(),
        kpi_grid(),
        charts_section(),
        dynamics_card(),
        player_performance_table(),
        class_name="animate-in fade-in duration-700 w-full",
    )