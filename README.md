# SoccerCV — Match Analysis Platform

A full-stack web application for soccer match video analysis. Upload match footage, track players and events automatically, and view detailed tactical reports.

## Tech Stack

* **[Reflex](https://reflex.dev)** — Python full-stack framework (compiles to React + FastAPI)
* **TailwindCSS v3** — utility-first styling via `@apply` in `app/styles/custom.css`
* **Python 3.12+**

## Getting Started

```Shell
# Install dependencies
uv sync

# Run the development server (localhost:3000)
reflex run
```

First run only:

```Shell
reflex init
```

## Pages

| Route      | Page            | Description                                                  |
| ---------- | --------------- | ------------------------------------------------------------ |
| `/`        | Dashboard       | KPI cards, momentum chart, player performance table          |
| `/upload`  | Analysis Studio | Drag-and-drop video upload + live analysis queue             |
| `/history` | Match Archive   | Browse all processed matches with filter/search              |
| `/reports` | Reports         | Tabbed report viewer: Overview, Players, Tactics, Key Events |

## Project Structure

```
app/
  app.py              # Page definitions and routing
  components/         # UI components (one file per page/view)
  states/             # Reflex state classes (one per feature)
  styles/
    custom.css        # All reusable component styles (@layer components + @apply)
rxconfig.py           # ProjectTailwindPlugin — injects custom.css into PostCSS pipeline
```

## Styling

Use component-based framework (Reflex, React), and the strategy should be Component abstraction — the primary approach

```Markdown
```

python

```
# my_app/styles/theme.py

# ── Colors ────────────────────────────────────────────────
COLORS = {
    "text_primary":   "text-[#e2e8f0]",
    "text_secondary": "text-[#9aa7b8]",
    "text_danger":    "text-[#f87171]",
    "icon_accent":    "text-[#7ab8e0]",
    "bg_surface":     "bg-[#334155]",
    "bg_surface_hover": "bg-[#3d4f63]",
    "border_default": "border-[#4a5666]",
}

# ── Buttons ───────────────────────────────────────────────
BUTTON = {
    "base":      "font-semibold transition-all cursor-pointer",
    "primary":   "btn-primary",          # your @apply class if using it
    "icon_ghost":"text-[#9aa7b8] hover:text-[#f87171]",
}

# ── Upload Zone ───────────────────────────────────────────
UPLOAD = {
    "dropzone": (
        "flex flex-col items-center justify-center "
        "border-2 border-dashed border-[#4a5666] rounded-3xl "
        "p-12 bg-[#334155] hover:bg-[#3d4f63] "
        "transition-all cursor-pointer group"
    ),
    "file_row": (
        "flex items-center justify-between "
        "p-3 bg-[#3d4f63] border border-[#4a5666] rounded-xl mb-2"
    ),
    "file_name":  "text-sm font-medium text-[#e2e8f0] truncate max-w-[200px]",
    "file_list":  "mt-4",
    "submit_btn": "btn-primary w-full mt-4 py-4 rounded-xl shadow-lg flex items-center justify-center gap-2",
    "wrapper":    "w-full max-w-2xl mx-auto",
}

# ── Typography ────────────────────────────────────────────
TEXT = {
    "h3":    "text-lg font-bold text-[#e2e8f0]",
    "muted": "text-sm text-[#9aa7b8] mt-1",
}
```

***

### Step 2 — Break the Component into Sub-Components

Each logical piece of the upload zone becomes its own small function.

python

```
# my_app/components/upload.py

import reflex as rx
from my_app.state.upload_state import UploadState
from my_app.styles.theme import UPLOAD, TEXT, BUTTON

UPLOAD_ID = "video_upload"


def _upload_prompt() -> rx.Component:
    """The icon + text + button shown inside the dropzone."""
    return rx.el.div(
        rx.icon("video", class_name="h-12 w-12 text-[#7ab8e0] mb-4"),
        rx.el.h3(
            "Drag & Drop Match Footage",
            class_name=TEXT["h3"],
        ),
        rx.el.p(
            "Supports MP4, AVI, MOV, MKV (Max 2GB)",
            class_name=TEXT["muted"],
        ),
        rx.el.button(
            "Select Files",
            class_name=f"{BUTTON['primary']} mt-6 px-6 py-2 rounded-lg",
        ),
        class_name="flex flex-col items-center justify-center",
    )


def _file_row(file: str) -> rx.Component:
    """A single selected file row with remove button."""
    return rx.el.div(
        rx.el.div(
            rx.icon("file-video", class_name="h-5 w-5 text-[#9aa7b8]"),
            rx.el.span(file, class_name=UPLOAD["file_name"]),
            class_name="flex items-center gap-2",
        ),
        rx.el.button(
            rx.icon("x", class_name="h-4 w-4"),
            on_click=rx.clear_selected_files(UPLOAD_ID),
            class_name=BUTTON["icon_ghost"],
        ),
        class_name=UPLOAD["file_row"],
    )


def _file_list() -> rx.Component:
    """The list of currently selected files."""
    return rx.el.div(
        rx.foreach(rx.selected_files(UPLOAD_ID), _file_row),
        class_name=UPLOAD["file_list"],
    )


def upload_zone() -> rx.Component:
    """Public-facing component — composed from sub-components."""
    return rx.el.div(
        rx.upload.root(
            rx.el.div(
                _upload_prompt(),
                class_name=UPLOAD["dropzone"],
            ),
            id=UPLOAD_ID,
            accept={
                "video/mp4":       [".mp4"],
                "video/quicktime": [".mov"],
                "video/x-msvideo": [".avi"],
                "video/x-matroska":[".mkv"],
            },
            max_files=5,
            multiple=True,
        ),
        _file_list(),
        rx.el.button(
            "Begin Analysis",
            on_click=UploadState.handle_upload(
                rx.upload_files(upload_id=UPLOAD_ID)
            ),
            class_name=UPLOAD["submit_btn"],
        ),
        class_name=UPLOAD["wrapper"],
    )
```

Notice:

* `_upload_prompt`, `_file_row`, `_file_list` are prefixed with `_` — they're **private** sub-components, not meant to be imported elsewhere
* Only `upload_zone` is public
* `UPLOAD_ID` is defined once, never repeated as a string literal

***

### Step 3 — Export from `__init__.py`

This is what makes imports clean across your whole app.

python

```
# my_app/components/__init__.py

from .upload import upload_zone
from .buttons import primary_button, ghost_button   # as you build more
from .cards import stat_card, info_card
from .typography import heading, muted_text
```

***

### Step 4 — Import Anywhere, Cleanly

python

```
# my_app/pages/dashboard.py

import reflex as rx
from my_app.components import upload_zone, stat_card, heading


def dashboard() -> rx.Component:
    return rx.el.div(
        heading("Upload Match Footage"),
        upload_zone(),
        stat_card(title="Matches Processed", value="142"),
        class_name="p-8 space-y-6",
    )
```

One import line. No class strings in your page files at all.

***

### The Full Picture

```
styles/theme.py          ← raw class strings, design tokens (edit here to restyle globally)
      ↓
components/upload.py     ← consumes theme tokens, builds sub-components privately
      ↓
components/__init__.py   ← re-exports only public components
      ↓
pages/dashboard.py       ← calls upload_zone(), knows nothing about CSS
```

#### The key rules to maintain this:

1. **No raw class strings in page files** — ever. Pages only call components.
2. **No raw hex colors outside** **`theme.py`** — always reference `COLORS["text_primary"]` etc.
3. **Prefix internal helpers with** **`_`** — keeps your component API surface small and clear.
4. **One** **`UPLOAD_ID`** **constant** — never repeat magic strings like `"video_upload"`.

When you want to restyle the entire upload zone — change one dict in `theme.py`. Done.

## Current State

All data is **hardcoded/mocked** — there is no database or real video processing pipeline. The app is an MVP scaffold built for future integration with a real analysis backend.
