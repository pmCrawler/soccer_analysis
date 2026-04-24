import dataclasses
from pathlib import Path

import reflex as rx
from reflex_base.constants.base import Dirs
from reflex_base.plugins.tailwind_v3 import TailwindV3Plugin

_STYLES_SRC = Path(__file__).parent / "app" / "styles"
_STYLES_DEST = Path(Dirs.STYLES)

_CSS_FILES = ["tokens.css", "views.css", "components.css"]


def _make_save_task(name: str):
    src = _STYLES_SRC / name
    dest = str(_STYLES_DEST / name)

    def _save():
        return dest, src.read_text()

    return _save


def _inject_imports(content: str) -> str:
    imports = [f'@import "./{name}";' for name in _CSS_FILES]
    for line in imports:
        if line not in content:
            marker = "@tailwind components;"
            if marker in content:
                content = content.replace(marker, f"{line}\n\n{marker}", 1)
            else:
                content += f"\n{line}\n"
    return content


@dataclasses.dataclass
class ProjectTailwindPlugin(TailwindV3Plugin):
    def pre_compile(self, **context):
        super().pre_compile(**context)
        for name in _CSS_FILES:
            context["add_save_task"](_make_save_task(name))
        context["add_modify_task"](
            str(_STYLES_DEST / "tailwind.css"),
            _inject_imports,
        )


config = rx.Config(
    app_name="app",
    plugins=[ProjectTailwindPlugin()],
    disable_plugins=[rx.plugins.SitemapPlugin()],
)
