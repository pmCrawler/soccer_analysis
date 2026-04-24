"""SQLAlchemy 2.x async ORM models."""

import uuid
from datetime import datetime, date as date_type

from sqlalchemy import (
    String, Integer, Float, Boolean, DateTime, Date,
    ForeignKey, Text, JSON, UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _uuid() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String, nullable=False)
    code: Mapped[str] = mapped_column(String(3), nullable=False)
    color: Mapped[str] = mapped_column(String(7), default="#7ab8e0")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    jobs: Mapped[list["Job"]] = relationship("Job", back_populates="team")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    team_id: Mapped[str | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    home: Mapped[str] = mapped_column(String, nullable=False)
    away: Mapped[str] = mapped_column(String, nullable=False)
    competition: Mapped[str] = mapped_column(String, default="")
    venue: Mapped[str] = mapped_column(String, default="")
    match_date: Mapped[date_type | None] = mapped_column(Date, nullable=True)
    kickoff: Mapped[str] = mapped_column(String, default="")
    # queued | preprocessing | calibrating | analyzing | reporting | ready | failed | live
    status: Mapped[str] = mapped_column(String, default="queued")
    stage: Mapped[str] = mapped_column(String, default="")
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    home_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    away_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quality: Mapped[str] = mapped_column(String, default="high")
    include_ai: Mapped[bool] = mapped_column(Boolean, default=True)
    include_tracking: Mapped[bool] = mapped_column(Boolean, default=True)
    include_heatmaps: Mapped[bool] = mapped_column(Boolean, default=True)
    run_dir: Mapped[str | None] = mapped_column(String, nullable=True)
    video_filename: Mapped[str | None] = mapped_column(String, nullable=True)
    clip_filename: Mapped[str | None] = mapped_column(String, nullable=True)
    error_msg: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    team: Mapped["Team | None"] = relationship("Team", back_populates="jobs")
    tactical_summary: Mapped["TacticalSummary | None"] = relationship(
        "TacticalSummary", back_populates="job", uselist=False
    )
    player_stats: Mapped[list["PlayerStat"]] = relationship(
        "PlayerStat", back_populates="job"
    )
    ai_report: Mapped["AIReport | None"] = relationship(
        "AIReport", back_populates="job", uselist=False
    )


class TacticalSummary(Base):
    __tablename__ = "tactical_summaries"

    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"), primary_key=True)
    possession_a: Mapped[int] = mapped_column(Integer, default=50)
    possession_b: Mapped[int] = mapped_column(Integer, default=50)
    formation_a: Mapped[str] = mapped_column(String, default="4-3-3")
    formation_b: Mapped[str] = mapped_column(String, default="4-4-2")
    stability_a: Mapped[int] = mapped_column(Integer, default=0)
    stability_b: Mapped[int] = mapped_column(Integer, default=0)
    ppda_a: Mapped[float | None] = mapped_column(Float, nullable=True)
    ppda_b: Mapped[float | None] = mapped_column(Float, nullable=True)
    # jsonb cols stored as JSON (asyncpg handles Python dicts transparently)
    momentum_data: Mapped[list] = mapped_column(JSON, default=list)
    key_moments: Mapped[list] = mapped_column(JSON, default=list)
    zone_pct: Mapped[dict] = mapped_column(JSON, default=dict)
    ball_tracking: Mapped[dict] = mapped_column(JSON, default=dict)
    avg_positions_a: Mapped[list] = mapped_column(JSON, default=list)
    avg_positions_b: Mapped[list] = mapped_column(JSON, default=list)
    pass_edges: Mapped[list] = mapped_column(JSON, default=list)
    press_points: Mapped[list] = mapped_column(JSON, default=list)
    shot_data: Mapped[list] = mapped_column(JSON, default=list)

    job: Mapped["Job"] = relationship("Job", back_populates="tactical_summary")


class PlayerStat(Base):
    __tablename__ = "player_stats"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    number: Mapped[int] = mapped_column(Integer, default=0)
    position: Mapped[str] = mapped_column(String, default="")
    team: Mapped[str] = mapped_column(String, default="a")  # "a" | "b"
    passes: Mapped[int] = mapped_column(Integer, default=0)
    pass_accuracy: Mapped[float] = mapped_column(Float, default=0.0)
    tackles: Mapped[int] = mapped_column(Integer, default=0)
    distance: Mapped[float] = mapped_column(Float, default=0.0)
    touches: Mapped[int] = mapped_column(Integer, default=0)
    duels: Mapped[int] = mapped_column(Integer, default=0)
    avg_x: Mapped[float] = mapped_column(Float, default=0.0)
    avg_y: Mapped[float] = mapped_column(Float, default=0.0)
    rating: Mapped[float] = mapped_column(Float, default=7.0)
    extra_stats: Mapped[dict] = mapped_column(JSON, default=dict)

    job: Mapped["Job"] = relationship("Job", back_populates="player_stats")


class AIReport(Base):
    __tablename__ = "ai_reports"

    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"), primary_key=True)
    headline: Mapped[str] = mapped_column(Text, default="")
    match_summary: Mapped[str] = mapped_column(Text, default="")
    team_tendencies: Mapped[str] = mapped_column(Text, default="")
    formation_analysis: Mapped[str] = mapped_column(Text, default="")
    pressing_analysis: Mapped[str] = mapped_column(Text, default="")
    momentum_analysis: Mapped[str] = mapped_column(Text, default="")
    counterfactual: Mapped[str | None] = mapped_column(Text, nullable=True)
    game_plan_compliance: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendations: Mapped[str] = mapped_column(Text, default="")
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job: Mapped["Job"] = relationship("Job", back_populates="ai_report")


class UserSettings(Base):
    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    direction: Mapped[str] = mapped_column(String, default="blueprint")
    theme: Mapped[str] = mapped_column(String, default="dark")
    contrast: Mapped[str] = mapped_column(String, default="normal")
    density: Mapped[str] = mapped_column(String, default="comfortable")
