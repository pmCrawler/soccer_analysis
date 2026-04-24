"""Pydantic schemas for Job-related API requests and responses."""

from __future__ import annotations
from datetime import datetime, date
from typing import Any
from pydantic import BaseModel


class TeamOut(BaseModel):
    id: str
    name: str
    code: str
    color: str

    model_config = {"from_attributes": True}


class TeamCreate(BaseModel):
    name: str
    code: str
    color: str = "#7ab8e0"


class JobCreate(BaseModel):
    home: str
    away: str
    competition: str = ""
    venue: str = ""
    match_date: date | None = None
    kickoff: str = ""
    quality: str = "high"
    include_ai: bool = True
    include_tracking: bool = True
    include_heatmaps: bool = True
    team_id: str | None = None


class JobOut(BaseModel):
    id: str
    team_id: str | None
    home: str
    away: str
    competition: str
    venue: str
    match_date: date | None
    kickoff: str
    status: str
    stage: str
    progress: float
    home_score: int | None
    away_score: int | None
    quality: str
    include_ai: bool
    include_tracking: bool
    include_heatmaps: bool
    run_dir: str | None
    video_filename: str | None
    clip_filename: str | None
    error_msg: str | None
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class CalibrationPoint(BaseModel):
    pixel_x: float
    pixel_y: float
    pitch_x: float
    pitch_y: float


class CalibrationSubmit(BaseModel):
    points: list[CalibrationPoint]


class TacticalSummaryOut(BaseModel):
    job_id: str
    possession_a: int
    possession_b: int
    formation_a: str
    formation_b: str
    stability_a: int
    stability_b: int
    ppda_a: float | None
    ppda_b: float | None
    momentum_data: list[Any]
    key_moments: list[Any]
    zone_pct: dict[str, Any]
    ball_tracking: dict[str, Any]
    avg_positions_a: list[Any]
    avg_positions_b: list[Any]
    pass_edges: list[Any]
    press_points: list[Any]
    shot_data: list[Any]

    model_config = {"from_attributes": True}


class PlayerStatOut(BaseModel):
    id: str
    job_id: str
    name: str
    number: int
    position: str
    team: str
    passes: int
    pass_accuracy: float
    tackles: int
    distance: float
    touches: int
    duels: int
    avg_x: float
    avg_y: float
    rating: float
    extra_stats: dict[str, Any]

    model_config = {"from_attributes": True}


class AIReportOut(BaseModel):
    job_id: str
    headline: str
    match_summary: str
    team_tendencies: str
    formation_analysis: str
    pressing_analysis: str
    momentum_analysis: str
    counterfactual: str | None
    game_plan_compliance: str | None
    recommendations: str
    generated_at: datetime

    model_config = {"from_attributes": True}


class ReportRequest(BaseModel):
    team_a_name: str = "Team A"
    team_b_name: str = "Team B"
    score_a: int | None = None
    score_b: int | None = None
    use_ai: bool = False
    coach_notes: str = ""


class UserSettingsOut(BaseModel):
    direction: str
    theme: str
    contrast: str
    density: str

    model_config = {"from_attributes": True}


class UserSettingsUpdate(BaseModel):
    direction: str | None = None
    theme: str | None = None
    contrast: str | None = None
    density: str | None = None
