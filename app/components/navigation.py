import reflex as rx
from app.states.navigation import NavigationState


def nav_item(
    label: str, icon: str, page: str, href: str, is_mobile: bool = False
) -> rx.Component:
    active_condition = NavigationState.current_page == page
    base_style = (
        "flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200"
    )
    active_style = "bg-[#2b3642] text-[#7ab8e0] border-l-4 border-[#7ab8e0] shadow-sm"
    inactive_style = "text-[#9aa7b8] hover:text-[#e2e8f0] hover:bg-[#2b3642] border-l-4 border-transparent"
    mobile_style = "flex flex-col items-center gap-1 flex-1 py-2 rounded-lg"
    mobile_active = "text-[#7ab8e0] bg-[#2b3642]"
    mobile_inactive = "text-[#9aa7b8] hover:text-[#e2e8f0]"
    return rx.link(
        rx.cond(
            is_mobile,
            rx.el.div(
                rx.icon(icon, class_name="h-6 w-6"),
                rx.el.span(label, class_name="text-[10px] font-medium"),
                class_name=rx.cond(
                    active_condition,
                    f"{mobile_style} {mobile_active}",
                    f"{mobile_style} {mobile_inactive}",
                ),
            ),
            rx.el.div(
                rx.icon(icon, class_name="h-5 w-5"),
                rx.el.span(label, class_name="font-semibold"),
                class_name=rx.cond(
                    active_condition,
                    f"{base_style} {active_style}",
                    f"{base_style} {inactive_style}",
                ),
            ),
        ),
        href=href,
        class_name="no-underline block w-full",
    )


def sidebar() -> rx.Component:
    return rx.el.aside(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon("dribbble", class_name="h-8 w-8 text-[#7ab8e0]"),
                    rx.el.h1(
                        "SOCCERCV",
                        class_name="text-xl font-bold tracking-widest text-[#e2e8f0] font-mono",
                    ),
                    class_name="flex items-center gap-3 p-6 mb-4",
                ),
                rx.el.nav(
                    nav_item("Dashboard", "layout-dashboard", "dashboard", "/"),
                    nav_item("Upload Video", "cloud_upload", "upload", "/upload"),
                    nav_item("Match History", "history", "history", "/history"),
                    nav_item("Reports", "file-text", "reports", "/reports"),
                    class_name="flex flex-col gap-2 px-4",
                ),
            ),
            rx.el.div(
                rx.el.div(
                    rx.image(
                        src="https://api.dicebear.com/9.x/notionists/svg?seed=ProAnalyst",
                        class_name="size-10 rounded-full bg-[#3d4f63]",
                    ),
                    rx.el.div(
                        rx.el.p(
                            "Pro Analyst", class_name="text-sm font-bold text-[#e2e8f0]"
                        ),
                        rx.el.p("Elite Tier", class_name="text-xs text-[#9aa7b8]"),
                        class_name="flex flex-col",
                    ),
                    class_name="flex items-center gap-3 p-6 border-t border-[#4a5666]",
                )
            ),
            class_name="flex flex-col justify-between h-full w-64 bg-[#1e2a36] border-r border-[#4a5666] hidden md:flex",
        ),
        class_name="fixed left-0 top-0 h-screen z-40",
    )


def bottom_nav() -> rx.Component:
    return rx.el.nav(
        nav_item("Home", "layout-dashboard", "dashboard", "/", is_mobile=True),
        nav_item("Upload", "cloud_upload", "upload", "/upload", is_mobile=True),
        nav_item("History", "history", "history", "/history", is_mobile=True),
        nav_item("Reports", "file-text", "reports", "/reports", is_mobile=True),
        class_name="fixed bottom-0 left-0 right-0 bg-[#1e2a36] border-t border-[#4a5666] flex items-center justify-around px-2 py-1 md:hidden z-50 shadow-[0_-2px_10px_rgba(0,0,0,0.3)]",
    )