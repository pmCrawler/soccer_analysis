"""Async CRUD helpers."""

from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import Job, Team, TacticalSummary, PlayerStat, AIReport, UserSettings


# ── Teams ─────────────────────────────────────────────────────────────

async def get_teams(db: AsyncSession) -> list[Team]:
    result = await db.execute(select(Team).order_by(Team.name))
    return result.scalars().all()


async def get_team(db: AsyncSession, team_id: str) -> Team | None:
    return await db.get(Team, team_id)


async def create_team(db: AsyncSession, name: str, code: str, color: str) -> Team:
    t = Team(name=name, code=code, color=color)
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return t


# ── Jobs ──────────────────────────────────────────────────────────────

async def get_jobs(
    db: AsyncSession,
    team_id: str | None = None,
    status_filter: str | None = None,
) -> list[Job]:
    q = select(Job).order_by(Job.created_at.desc())
    if team_id:
        q = q.where(Job.team_id == team_id)
    if status_filter and status_filter != "all":
        if status_filter == "processing":
            q = q.where(Job.status.in_(["preprocessing", "calibrating", "analyzing", "reporting", "queued", "live"]))
        else:
            q = q.where(Job.status == status_filter)
    result = await db.execute(q)
    return result.scalars().all()


async def get_job(db: AsyncSession, job_id: str) -> Job | None:
    return await db.get(Job, job_id)


async def create_job(db: AsyncSession, **kwargs) -> Job:
    job = Job(**kwargs)
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


async def update_job(db: AsyncSession, job_id: str, **fields) -> None:
    await db.execute(update(Job).where(Job.id == job_id).values(**fields))
    await db.commit()


async def set_job_status(
    db: AsyncSession, job_id: str, status: str, stage: str = "", progress: float | None = None
) -> None:
    values: dict = {"status": status, "stage": stage}
    if progress is not None:
        values["progress"] = progress
    if status in ("ready", "failed"):
        values["completed_at"] = datetime.utcnow()
        values["progress"] = 1.0 if status == "ready" else values.get("progress", 0.0)
    await db.execute(update(Job).where(Job.id == job_id).values(**values))
    await db.commit()


# ── TacticalSummary ───────────────────────────────────────────────────

async def get_tactical_summary(db: AsyncSession, job_id: str) -> TacticalSummary | None:
    return await db.get(TacticalSummary, job_id)


async def upsert_tactical_summary(db: AsyncSession, job_id: str, **fields) -> TacticalSummary:
    existing = await db.get(TacticalSummary, job_id)
    if existing:
        for k, v in fields.items():
            setattr(existing, k, v)
    else:
        existing = TacticalSummary(job_id=job_id, **fields)
        db.add(existing)
    await db.commit()
    await db.refresh(existing)
    return existing


# ── PlayerStats ───────────────────────────────────────────────────────

async def get_player_stats(db: AsyncSession, job_id: str) -> list[PlayerStat]:
    result = await db.execute(
        select(PlayerStat).where(PlayerStat.job_id == job_id).order_by(PlayerStat.team, PlayerStat.number)
    )
    return result.scalars().all()


async def delete_player_stats(db: AsyncSession, job_id: str) -> None:
    from sqlalchemy import delete as sql_delete
    await db.execute(sql_delete(PlayerStat).where(PlayerStat.job_id == job_id))
    await db.commit()


async def bulk_insert_player_stats(db: AsyncSession, records: list[dict]) -> None:
    for rec in records:
        db.add(PlayerStat(**rec))
    await db.commit()


# ── AIReport ──────────────────────────────────────────────────────────

async def get_ai_report(db: AsyncSession, job_id: str) -> AIReport | None:
    return await db.get(AIReport, job_id)


async def upsert_ai_report(db: AsyncSession, job_id: str, sections: dict) -> AIReport:
    existing = await db.get(AIReport, job_id)
    if existing:
        for k, v in sections.items():
            setattr(existing, k, v)
        existing.generated_at = datetime.utcnow()
    else:
        existing = AIReport(job_id=job_id, generated_at=datetime.utcnow(), **sections)
        db.add(existing)
    await db.commit()
    await db.refresh(existing)
    return existing


# ── UserSettings ──────────────────────────────────────────────────────

async def get_settings(db: AsyncSession) -> UserSettings:
    result = await db.get(UserSettings, 1)
    if result is None:
        result = UserSettings(id=1)
        db.add(result)
        await db.commit()
        await db.refresh(result)
    return result


async def update_settings(db: AsyncSession, **fields) -> UserSettings:
    s = await get_settings(db)
    for k, v in fields.items():
        if v is not None:
            setattr(s, k, v)
    await db.commit()
    await db.refresh(s)
    return s
