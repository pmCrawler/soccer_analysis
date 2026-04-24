"""Async subprocess wrapper for the soccercv CLI."""

import asyncio
import os
import re
from pathlib import Path
from typing import AsyncIterator, Callable, Awaitable

RUNS_DIR = Path(os.environ.get("RUNS_DIR", "/data/runs"))

# Pattern matching e.g. "[detect] Frame 420/1000" or "Frame 420/1000"
_FRAME_RE = re.compile(r"[Ff]rame\s+(\d+)/(\d+)")


def _parse_progress(line: str) -> float | None:
    m = _FRAME_RE.search(line)
    if m:
        current, total = int(m.group(1)), int(m.group(2))
        if total > 0:
            return current / total
    return None


async def run_soccercv(
    args: list[str],
    extra_env: dict[str, str] | None = None,
    cwd: str | None = None,
) -> AsyncIterator[dict]:
    """
    Spawn `soccercv <args>` and yield progress event dicts.

    Each yielded dict has at minimum:
      {"type": "log", "line": str}          — raw stdout line
      {"type": "progress", "pct": float}    — 0.0-1.0 when parseable
      {"type": "done", "returncode": int}   — on exit
    """
    env = {**os.environ}
    if extra_env:
        env.update(extra_env)

    proc = await asyncio.create_subprocess_exec(
        "soccercv",
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        env=env,
        cwd=cwd,
    )

    async for raw in proc.stdout:
        line = raw.decode("utf-8", errors="replace").rstrip()
        yield {"type": "log", "line": line}
        pct = _parse_progress(line)
        if pct is not None:
            yield {"type": "progress", "pct": pct}

    rc = await proc.wait()
    yield {"type": "done", "returncode": rc}


def job_run_dir(job_id: str) -> Path:
    """Canonical run directory for a job."""
    return RUNS_DIR / job_id


def find_clip(run_dir: Path, stem: str) -> Path | None:
    """Return the preprocessed clip path if it exists."""
    candidate = run_dir / f"{stem}_clip.mp4"
    return candidate if candidate.exists() else None
