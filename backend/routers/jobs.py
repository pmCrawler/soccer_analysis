"""Jobs endpoints — upload, pipeline steps, SSE, data retrieval."""

import asyncio
import json
import os
import shutil
from pathlib import Path
from typing import AsyncIterator

import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.session import get_db
from ..db import queries
from ..schemas.jobs import (
    AIReportOut,
    CalibrationSubmit,
    JobOut,
    PlayerStatOut,
    ReportRequest,
    TacticalSummaryOut,
)
from ..services.pipeline import job_run_dir, run_soccercv

router = APIRouter(tags=["jobs"])

# job_id → asyncio.Queue of SSE event dicts
_sse_queues: dict[str, asyncio.Queue] = {}


def _get_or_create_queue(job_id: str) -> asyncio.Queue:
    if job_id not in _sse_queues:
        _sse_queues[job_id] = asyncio.Queue()
    return _sse_queues[job_id]


# ── List / detail ─────────────────────────────────────────────────────


@router.get("/jobs", response_model=list[JobOut])
async def list_jobs(
    team_id: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await queries.get_jobs(db, team_id=team_id, status_filter=status)


@router.get("/jobs/{job_id}", response_model=JobOut)
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)):
    job = await queries.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.delete("/jobs/{job_id}", status_code=204)
async def delete_job(job_id: str, db: AsyncSession = Depends(get_db)):
    job = await queries.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    run_dir = job_run_dir(job_id)
    if run_dir.exists():
        shutil.rmtree(run_dir, ignore_errors=True)
    await db.delete(job)
    await db.commit()


# ── Create job (video upload) ─────────────────────────────────────────


@router.post("/jobs", response_model=JobOut, status_code=201)
async def create_job(
    video: UploadFile = File(...),
    home: str = Form(...),
    away: str = Form(...),
    competition: str = Form(""),
    venue: str = Form(""),
    match_date: str = Form(None),
    kickoff: str = Form(""),
    quality: str = Form("high"),
    include_ai: bool = Form(True),
    include_tracking: bool = Form(True),
    include_heatmaps: bool = Form(True),
    team_id: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
):
    from datetime import date as date_type

    parsed_date = None
    if match_date:
        try:
            parsed_date = date_type.fromisoformat(match_date)
        except ValueError:
            pass

    job = await queries.create_job(
        db,
        home=home,
        away=away,
        competition=competition,
        venue=venue,
        match_date=parsed_date,
        kickoff=kickoff,
        quality=quality,
        include_ai=include_ai,
        include_tracking=include_tracking,
        include_heatmaps=include_heatmaps,
        team_id=team_id,
        status="queued",
    )

    run_dir = job_run_dir(job.id)
    run_dir.mkdir(parents=True, exist_ok=True)

    dest = run_dir / video.filename
    with open(dest, "wb") as f:
        while chunk := await video.read(1024 * 1024):
            f.write(chunk)

    await queries.update_job(
        db,
        job.id,
        run_dir=str(run_dir),
        video_filename=video.filename,
    )
    await db.refresh(job)
    return job


# ── Pipeline steps ────────────────────────────────────────────────────


async def _run_pipeline_step(
    job_id: str,
    db: AsyncSession,
    status: str,
    stage: str,
    args: list[str],
    extra_env: dict | None = None,
    cwd: str | None = None,
) -> int:
    queue = _get_or_create_queue(job_id)
    await queries.set_job_status(db, job_id, status, stage=stage, progress=0.0)

    rc = 0
    async for event in run_soccercv(args, extra_env=extra_env, cwd=cwd):
        await queue.put(event)
        if event["type"] == "progress":
            await queries.update_job(db, job_id, progress=event["pct"])
        if event["type"] == "done":
            rc = event["returncode"]

    return rc


@router.post("/jobs/{job_id}/preprocess", status_code=202)
async def preprocess(job_id: str, db: AsyncSession = Depends(get_db)):
    job = await queries.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if not job.video_filename or not job.run_dir:
        raise HTTPException(status_code=400, detail="No video uploaded")

    async def _run():
        video_path = Path(job.run_dir) / job.video_filename
        rc = await _run_pipeline_step(
            job_id, db,
            status="preprocessing", stage="preprocess",
            args=["preprocess", str(video_path), "--output-dir", job.run_dir],
            cwd=job.run_dir,
        )
        if rc == 0:
            stem = Path(job.video_filename).stem
            clip_name = f"{stem}_clip.mp4"
            clip_path = Path(job.run_dir) / clip_name
            if clip_path.exists():
                await queries.update_job(db, job_id, clip_filename=clip_name)
            await queries.set_job_status(db, job_id, "calibrating", stage="", progress=1.0)
        else:
            await queries.set_job_status(db, job_id, "failed", stage="preprocess")
            queue = _get_or_create_queue(job_id)
            await queue.put({"type": "error", "message": "Preprocessing failed"})

    asyncio.create_task(_run())
    return {"queued": True}


@router.get("/jobs/{job_id}/calibration-frame")
async def calibration_frame(job_id: str, db: AsyncSession = Depends(get_db)):
    job = await queries.get_job(db, job_id)
    if not job or not job.run_dir:
        raise HTTPException(status_code=404, detail="Job not found")

    clip_path = None
    if job.clip_filename:
        clip_path = Path(job.run_dir) / job.clip_filename
    if not clip_path or not clip_path.exists():
        raise HTTPException(status_code=404, detail="Clip not found — run preprocess first")

    frame_path = Path(job.run_dir) / "calibration_frame.jpg"
    if not frame_path.exists():
        cap = cv2.VideoCapture(str(clip_path))
        ret, frame = cap.read()
        cap.release()
        if not ret:
            raise HTTPException(status_code=500, detail="Could not extract frame")
        cv2.imwrite(str(frame_path), frame)

    return FileResponse(str(frame_path), media_type="image/jpeg")


@router.post("/jobs/{job_id}/calibrate", status_code=200)
async def calibrate(
    job_id: str,
    body: CalibrationSubmit,
    db: AsyncSession = Depends(get_db),
):
    job = await queries.get_job(db, job_id)
    if not job or not job.run_dir:
        raise HTTPException(status_code=404, detail="Job not found")

    if len(body.points) < 4:
        raise HTTPException(status_code=400, detail="At least 4 calibration points required")

    pixel_pts = np.array([[p.pixel_x, p.pixel_y] for p in body.points], dtype=np.float64)
    pitch_pts = np.array([[p.pitch_x, p.pitch_y] for p in body.points], dtype=np.float64)

    H, _ = cv2.findHomography(pixel_pts, pitch_pts)
    if H is None:
        raise HTTPException(status_code=422, detail="Could not compute homography")

    homography_path = Path(job.run_dir) / "homography.npy"
    np.save(str(homography_path), H)

    await queries.set_job_status(db, job_id, "queued", stage="analyze")
    return {"status": "ok", "homography_path": str(homography_path)}


@router.post("/jobs/{job_id}/analyze", status_code=202)
async def analyze(job_id: str, db: AsyncSession = Depends(get_db)):
    job = await queries.get_job(db, job_id)
    if not job or not job.run_dir:
        raise HTTPException(status_code=404, detail="Job not found")

    homography_path = Path(job.run_dir) / "homography.npy"
    if not homography_path.exists():
        raise HTTPException(status_code=400, detail="Calibration not done — homography.npy missing")

    video_path = Path(job.run_dir) / (job.clip_filename or job.video_filename)
    quality_map = {"standard": "--frame-skip 3", "high": "--frame-skip 2", "max": "--frame-skip 1"}
    skip_flag = quality_map.get(job.quality, "--frame-skip 2")

    async def _run():
        args = [
            "analyze", str(video_path),
            "--homography", str(homography_path),
            "--output-dir", job.run_dir,
        ] + skip_flag.split()
        rc = await _run_pipeline_step(
            job_id, db,
            status="analyzing", stage="analyze",
            args=args,
            cwd=job.run_dir,
        )
        if rc == 0:
            await queries.set_job_status(db, job_id, "reporting", stage="report", progress=0.0)
        else:
            await queries.set_job_status(db, job_id, "failed", stage="analyze")
            queue = _get_or_create_queue(job_id)
            await queue.put({"type": "error", "message": "Analysis failed"})

    asyncio.create_task(_run())
    return {"queued": True}


@router.post("/jobs/{job_id}/report", status_code=202)
async def generate_report(
    job_id: str,
    body: ReportRequest,
    db: AsyncSession = Depends(get_db),
):
    job = await queries.get_job(db, job_id)
    if not job or not job.run_dir:
        raise HTTPException(status_code=404, detail="Job not found")

    async def _run():
        args = [
            "report", job.run_dir,
            "--home", body.team_a_name,
            "--away", body.team_b_name,
        ]
        if body.score_a is not None:
            args += ["--score-a", str(body.score_a)]
        if body.score_b is not None:
            args += ["--score-b", str(body.score_b)]
        # AI is handled in-process via pydantic-ai — do not pass --ai to CLI

        rc = await _run_pipeline_step(
            job_id, db,
            status="reporting", stage="report",
            args=args,
            cwd=job.run_dir,
        )
        if rc == 0:
            agg = await _ingest_tactical_report(job_id, db, Path(job.run_dir))
            if body.use_ai and agg is not None:
                try:
                    from ..services.ai_analysis import generate_tactical_brief
                    brief = await generate_tactical_brief(
                        agg=agg,
                        team_a=body.team_a_name,
                        team_b=body.team_b_name,
                        score_a=body.score_a,
                        score_b=body.score_b,
                        coach_notes=body.coach_notes,
                    )
                    await queries.upsert_ai_report(db, job_id, brief.model_dump())
                except Exception as exc:
                    queue = _get_or_create_queue(job_id)
                    await queue.put({"type": "error", "message": f"AI report failed: {exc}"})
            await queries.set_job_status(db, job_id, "ready", stage="", progress=1.0)
            queue = _get_or_create_queue(job_id)
            await queue.put({"type": "done", "status": "ready"})
        else:
            await queries.set_job_status(db, job_id, "failed", stage="report")
            queue = _get_or_create_queue(job_id)
            await queue.put({"type": "error", "message": "Report generation failed"})

    asyncio.create_task(_run())
    return {"queued": True}


async def _ingest_tactical_report(
    job_id: str, db: AsyncSession, run_dir: Path
) -> dict | None:
    """
    Read per-frame tactical_report.json, aggregate into summary stats, and
    upsert TacticalSummary in the DB.  Returns the aggregate dict (including
    the _ai extras needed for AI prompt building) or None on failure.
    """
    report_path = run_dir / "tactical_report.json"
    if not report_path.exists():
        return None
    try:
        frames = json.loads(report_path.read_text())
        if not isinstance(frames, list):
            return None
    except Exception:
        return None

    from ..services.ai_analysis import aggregate_frames

    agg = aggregate_frames(frames)
    db_fields = {k: v for k, v in agg.items() if k != "_ai"}
    await queries.upsert_tactical_summary(db, job_id, **db_fields)
    return agg


# ── SSE stream ────────────────────────────────────────────────────────


@router.get("/jobs/{job_id}/events")
async def job_events(job_id: str, db: AsyncSession = Depends(get_db)):
    job = await queries.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    queue = _get_or_create_queue(job_id)

    async def _stream() -> AsyncIterator[str]:
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
            except asyncio.TimeoutError:
                yield "event: ping\ndata: {}\n\n"
                continue
            payload = json.dumps(event)
            yield f"data: {payload}\n\n"
            if event.get("type") in ("done", "error"):
                break

    return StreamingResponse(
        _stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ── Data endpoints ────────────────────────────────────────────────────


@router.get("/jobs/{job_id}/tactical-summary", response_model=TacticalSummaryOut)
async def tactical_summary(job_id: str, db: AsyncSession = Depends(get_db)):
    s = await queries.get_tactical_summary(db, job_id)
    if not s:
        raise HTTPException(status_code=404, detail="No tactical summary yet")
    return s


@router.get("/jobs/{job_id}/players", response_model=list[PlayerStatOut])
async def player_stats(job_id: str, db: AsyncSession = Depends(get_db)):
    return await queries.get_player_stats(db, job_id)


@router.get("/jobs/{job_id}/ai-report", response_model=AIReportOut)
async def ai_report(job_id: str, db: AsyncSession = Depends(get_db)):
    r = await queries.get_ai_report(db, job_id)
    if not r:
        raise HTTPException(status_code=404, detail="No AI report yet")
    return r


@router.get("/jobs/{job_id}/files/{filename:path}")
async def serve_file(job_id: str, filename: str, db: AsyncSession = Depends(get_db)):
    job = await queries.get_job(db, job_id)
    if not job or not job.run_dir:
        raise HTTPException(status_code=404, detail="Job not found")
    file_path = Path(job.run_dir) / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    # Prevent path traversal
    try:
        file_path.resolve().relative_to(Path(job.run_dir).resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Forbidden")
    return FileResponse(str(file_path))
