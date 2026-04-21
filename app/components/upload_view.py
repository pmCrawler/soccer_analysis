import reflex as rx
from app.states.upload import UploadState
from app.states.report import ReportState


def upload_zone() -> rx.Component:
    return rx.el.div(
        rx.upload.root(
            rx.el.div(
                rx.icon("video", class_name="h-12 w-12 text-[#7ab8e0] mb-4"),
                rx.el.h3(
                    "Drag & Drop Match Footage",
                    class_name="text-lg font-bold text-[#e2e8f0]",
                ),
                rx.el.p(
                    "Supports MP4, AVI, MOV, MKV (Max 2GB)",
                    class_name="text-sm text-[#9aa7b8] mt-1",
                ),
                rx.el.button(
                    "Select Files",
                    class_name="mt-6 px-6 py-2 bg-[#7ab8e0] text-white rounded-lg font-semibold hover:bg-[#93c5e8] transition-colors",
                ),
                class_name="flex flex-col items-center justify-center border-2 border-dashed border-[#4a5666] rounded-3xl p-12 bg-[#334155] hover:bg-[#3d4f63] transition-all cursor-pointer group",
            ),
            id="video_upload",
            accept={
                "video/mp4": [".mp4"],
                "video/quicktime": [".mov"],
                "video/x-msvideo": [".avi"],
                "video/x-matroska": [".mkv"],
            },
            max_files=5,
            multiple=True,
        ),
        rx.el.div(
            rx.foreach(
                rx.selected_files("video_upload"),
                lambda file: rx.el.div(
                    rx.el.div(
                        rx.icon("file-video", class_name="h-5 w-5 text-[#9aa7b8]"),
                        rx.el.span(
                            file,
                            class_name="text-sm font-medium text-[#e2e8f0] truncate max-w-[200px]",
                        ),
                        class_name="flex items-center gap-2",
                    ),
                    rx.el.button(
                        rx.icon("x", class_name="h-4 w-4"),
                        on_click=rx.clear_selected_files("video_upload"),
                        class_name="text-[#9aa7b8] hover:text-[#f87171]",
                    ),
                    class_name="flex items-center justify-between p-3 bg-[#3d4f63] border border-[#4a5666] rounded-xl mb-2",
                ),
            ),
            class_name="mt-4",
        ),
        rx.el.button(
            "Begin Analysis",
            on_click=UploadState.handle_upload(
                rx.upload_files(upload_id="video_upload")
            ),
            class_name="w-full mt-4 py-4 bg-[#7ab8e0] text-white rounded-xl font-bold hover:bg-[#93c5e8] transition-all shadow-lg flex items-center justify-center gap-2",
        ),
        class_name="w-full max-w-2xl mx-auto",
    )


def queue_card(job: dict) -> rx.Component:
    status_colors = rx.match(
        job["status"],
        ("Complete", "bg-[#064e3b] text-[#6ee7b7]"),
        ("Processing", "bg-[#1e3a8a] text-[#7ab8e0] animate-pulse"),
        ("Queued", "bg-[#78350f] text-[#fbbf24]"),
        ("Failed", "bg-[#7f1d1d] text-[#f87171]"),
        "bg-[#3d4f63] text-[#9aa7b8]",
    )
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.h4(
                    job["match_name"], class_name="font-bold text-[#e2e8f0] truncate"
                ),
                rx.el.p(
                    f"{job['filename']} • {job['file_size']}",
                    class_name="text-xs text-[#9aa7b8]",
                ),
                class_name="flex flex-col",
            ),
            rx.el.span(
                job["status"],
                class_name=f"px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider {status_colors}",
            ),
            class_name="flex justify-between items-start mb-3",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    class_name="h-full bg-[#7ab8e0] rounded-full transition-all duration-500",
                    style={"width": f"{job['progress']}%"},
                ),
                class_name="h-1.5 w-full bg-[#1e2a36] rounded-full overflow-hidden",
            ),
            rx.el.span(
                f"{job['progress']}%", class_name="text-[10px] font-bold text-[#9aa7b8]"
            ),
            class_name="flex items-center gap-3 mb-2",
        ),
        rx.cond(
            job["status"] == "Complete",
            rx.el.button(
                "View Report",
                on_click=ReportState.load_report(job["id"]),
                class_name="w-full py-1.5 bg-[#2b3642] text-[#7ab8e0] border border-[#7ab8e0] rounded-lg text-xs font-bold hover:bg-[#7ab8e0] hover:text-[#1e2a36] transition-colors mt-1",
            ),
            rx.cond(
                job["status"] == "Failed",
                rx.el.button(
                    "Retry",
                    on_click=UploadState.retry_job(job["id"]),
                    class_name="w-full py-1.5 bg-[#7f1d1d] text-[#fca5a5] rounded-lg text-xs font-bold hover:bg-[#991b1b] transition-colors mt-1",
                ),
                rx.fragment(),
            ),
        ),
        class_name="p-4 bg-[#334155] border border-[#4a5666] rounded-2xl shadow-sm hover:border-[#7ab8e0] transition-all",
    )


def upload_view() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h2(
                "Analysis Studio", class_name="text-3xl font-bold text-[#e2e8f0] mb-2"
            ),
            rx.el.p(
                "Upload match footage to begin deep neural analysis",
                class_name="text-[#9aa7b8] mb-8",
            ),
            class_name="mb-4",
        ),
        rx.el.div(
            rx.el.div(upload_zone(), class_name="lg:col-span-2"),
            rx.el.div(
                rx.el.div(
                    rx.el.div(
                        rx.el.h3("Active Queue", class_name="font-bold text-[#e2e8f0]"),
                        rx.el.button(
                            "Clear Done",
                            on_click=UploadState.clear_completed,
                            class_name="text-xs text-[#7ab8e0] font-semibold hover:underline",
                        ),
                        class_name="flex items-center justify-between mb-4",
                    ),
                    rx.el.div(
                        rx.foreach(UploadState.jobs, queue_card),
                        class_name="flex flex-col gap-3",
                    ),
                    class_name="bg-[#334155] p-6 rounded-3xl border border-[#4a5666] shadow-sm sticky top-6",
                ),
                class_name="lg:col-span-1",
            ),
            class_name="grid grid-cols-1 lg:grid-cols-3 gap-8",
        ),
        class_name="animate-in fade-in duration-700",
    )