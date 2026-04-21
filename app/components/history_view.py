import reflex as rx
from app.states.upload import UploadState
from app.states.report import ReportState


def status_badge(status: str) -> rx.Component:
    colors = rx.match(
        status,
        ("Complete", "bg-[#064e3b] text-[#6ee7b7]"),
        ("Processing", "bg-[#1e3a8a] text-[#7ab8e0]"),
        ("Queued", "bg-[#78350f] text-[#fbbf24]"),
        ("Failed", "bg-[#7f1d1d] text-[#f87171]"),
        "bg-[#3d4f63] text-[#9aa7b8]",
    )
    return rx.el.span(
        status,
        class_name=f"px-3 py-1 rounded-lg text-xs font-bold uppercase tracking-tight {colors} w-fit",
    )


def match_card(job: dict) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon(
                    "play",
                    class_name="h-10 w-10 text-white opacity-0 group-hover:opacity-100 transition-opacity",
                ),
                class_name="absolute inset-0 flex items-center justify-center bg-black/20 group-hover:bg-black/40 transition-all",
            ),
            rx.image(
                src="/placeholder.svg", class_name="w-full h-40 object-cover opacity-80"
            ),
            class_name="relative overflow-hidden",
        ),
        rx.el.div(
            rx.el.div(
                status_badge(job["status"]),
                rx.el.span(
                    job["duration"],
                    class_name="text-xs font-mono text-[#9aa7b8] bg-[#2b3642] px-2 py-1 rounded",
                ),
                class_name="flex items-center justify-between mb-3",
            ),
            rx.el.h3(
                job["match_name"],
                class_name="font-bold text-[#e2e8f0] mb-1 group-hover:text-[#7ab8e0] transition-colors",
            ),
            rx.el.p(
                f"Analyzed on {job['upload_time']}",
                class_name="text-xs text-[#9aa7b8] mb-4",
            ),
            rx.cond(
                job["status"] == "Complete",
                rx.el.div(
                    rx.el.div(
                        rx.el.span(
                            job["players_tracked"].to_string(),
                            class_name="text-sm font-bold text-[#e2e8f0]",
                        ),
                        rx.el.span(
                            "Players",
                            class_name="text-[10px] text-[#9aa7b8] uppercase font-bold",
                        ),
                        class_name="flex flex-col items-center",
                    ),
                    rx.el.div(class_name="w-[1px] h-8 bg-[#4a5666]"),
                    rx.el.div(
                        rx.el.span(
                            job["events_detected"].to_string(),
                            class_name="text-sm font-bold text-[#e2e8f0]",
                        ),
                        rx.el.span(
                            "Events",
                            class_name="text-[10px] text-[#9aa7b8] uppercase font-bold",
                        ),
                        class_name="flex flex-col items-center",
                    ),
                    rx.el.div(class_name="w-[1px] h-8 bg-[#4a5666]"),
                    rx.el.div(
                        rx.icon("chevron-right", class_name="h-5 w-5 text-[#7ab8e0]"),
                        class_name="flex items-center",
                    ),
                    class_name="flex items-center justify-between pt-4 border-t border-[#4a5666]",
                ),
                rx.el.div(
                    rx.el.p(
                        "Analysis in progress...",
                        class_name="text-xs italic text-[#9aa7b8]",
                    ),
                    class_name="pt-4 border-t border-[#4a5666]",
                ),
            ),
            class_name="p-5",
        ),
        on_click=rx.cond(
            job["status"] == "Complete", ReportState.load_report(job["id"]), rx.noop()
        ),
        class_name="group flex flex-col bg-[#334155] border border-[#4a5666] rounded-3xl overflow-hidden shadow-sm hover:shadow-xl hover:border-[#7ab8e0] hover:-translate-y-1 transition-all cursor-pointer",
    )


def filter_tab(label: str) -> rx.Component:
    is_active = UploadState.filter_status == label
    return rx.el.button(
        label,
        on_click=lambda: UploadState.set_filter_status(label),
        class_name=rx.cond(
            is_active,
            "px-6 py-2 bg-[#7ab8e0] text-[#1e2a36] rounded-full text-sm font-bold shadow-lg shadow-[#7ab8e0]/20",
            "px-6 py-2 bg-[#334155] text-[#9aa7b8] hover:bg-[#3d4f63] hover:text-[#e2e8f0] rounded-full text-sm font-bold",
        ),
    )


def history_view() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.h2(
                    "Match Archive", class_name="text-3xl font-bold text-[#e2e8f0]"
                ),
                rx.el.p(
                    "Browse and access your processed match analysis reports",
                    class_name="text-[#9aa7b8]",
                ),
                class_name="mb-8",
            ),
            rx.el.div(
                rx.el.div(
                    filter_tab("All"),
                    filter_tab("Processing"),
                    filter_tab("Complete"),
                    filter_tab("Failed"),
                    class_name="flex flex-wrap gap-2",
                ),
                rx.el.div(
                    rx.el.div(
                        rx.icon(
                            "search",
                            class_name="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#9aa7b8]",
                        ),
                        rx.el.input(
                            placeholder="Search matches...",
                            on_change=UploadState.set_search_query.debounce(300),
                            class_name="pl-10 pr-4 py-2 bg-[#3d4f63] text-[#e2e8f0] placeholder-[#9aa7b8] border-none rounded-xl text-sm focus:ring-2 focus:ring-[#7ab8e0] w-full md:w-64",
                        ),
                        class_name="relative w-full md:w-auto",
                    ),
                    class_name="flex items-center gap-4 w-full md:w-auto",
                ),
                class_name="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-8",
            ),
            rx.cond(
                UploadState.filtered_jobs.length() > 0,
                rx.el.div(
                    rx.foreach(UploadState.filtered_jobs, match_card),
                    class_name="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6",
                ),
                rx.el.div(
                    rx.icon("database", class_name="h-16 w-16 text-[#4a5666] mb-4"),
                    rx.el.h3(
                        "No matching records",
                        class_name="text-xl font-bold text-[#9aa7b8]",
                    ),
                    rx.el.p(
                        "Try adjusting your filters or search terms",
                        class_name="text-[#9aa7b8] mt-2",
                    ),
                    class_name="flex flex-col items-center justify-center py-32 border-2 border-dashed border-[#4a5666] rounded-3xl",
                ),
            ),
            class_name="w-full",
        ),
        class_name="animate-in slide-in-from-bottom-4 duration-700",
    )