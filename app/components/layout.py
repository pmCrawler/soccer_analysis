import reflex as rx
from app.components.navigation import sidebar, bottom_nav


def layout(content: rx.Component) -> rx.Component:
    return rx.el.div(
        sidebar(),
        rx.el.main(
            rx.el.div(content, class_name="max-w-7xl mx-auto"),
            class_name="flex-1 p-6 md:ml-64 pb-24 md:pb-6 min-h-screen bg-[#2b3642]",
        ),
        bottom_nav(),
        class_name="font-['Inter'] flex min-h-screen bg-[#2b3642] text-[#e2e8f0]",
    )