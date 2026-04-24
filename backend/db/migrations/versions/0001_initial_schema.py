"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-04-24
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "teams",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("code", sa.String(3), nullable=False),
        sa.Column("color", sa.String(7), nullable=False, server_default="#7ab8e0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "jobs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("team_id", sa.String(), sa.ForeignKey("teams.id"), nullable=True),
        sa.Column("home", sa.String(), nullable=False),
        sa.Column("away", sa.String(), nullable=False),
        sa.Column("competition", sa.String(), nullable=False, server_default=""),
        sa.Column("venue", sa.String(), nullable=False, server_default=""),
        sa.Column("match_date", sa.Date(), nullable=True),
        sa.Column("kickoff", sa.String(), nullable=False, server_default=""),
        sa.Column("status", sa.String(), nullable=False, server_default="queued"),
        sa.Column("stage", sa.String(), nullable=False, server_default=""),
        sa.Column("progress", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("home_score", sa.Integer(), nullable=True),
        sa.Column("away_score", sa.Integer(), nullable=True),
        sa.Column("quality", sa.String(), nullable=False, server_default="high"),
        sa.Column("include_ai", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("include_tracking", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("include_heatmaps", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("run_dir", sa.String(), nullable=True),
        sa.Column("video_filename", sa.String(), nullable=True),
        sa.Column("clip_filename", sa.String(), nullable=True),
        sa.Column("error_msg", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "tactical_summaries",
        sa.Column("job_id", sa.String(), sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column("possession_a", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("possession_b", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("formation_a", sa.String(), nullable=False, server_default="4-3-3"),
        sa.Column("formation_b", sa.String(), nullable=False, server_default="4-4-2"),
        sa.Column("stability_a", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("stability_b", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ppda_a", sa.Float(), nullable=True),
        sa.Column("ppda_b", sa.Float(), nullable=True),
        sa.Column("momentum_data", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("key_moments", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("zone_pct", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("ball_tracking", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("avg_positions_a", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("avg_positions_b", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("pass_edges", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("press_points", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("shot_data", sa.JSON(), nullable=False, server_default="[]"),
        sa.PrimaryKeyConstraint("job_id"),
    )

    op.create_table(
        "player_stats",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("job_id", sa.String(), sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("position", sa.String(), nullable=False, server_default=""),
        sa.Column("team", sa.String(), nullable=False, server_default="a"),
        sa.Column("passes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pass_accuracy", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("tackles", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("distance", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("touches", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duels", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_x", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("avg_y", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("rating", sa.Float(), nullable=False, server_default="7.0"),
        sa.Column("extra_stats", sa.JSON(), nullable=False, server_default="{}"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "ai_reports",
        sa.Column("job_id", sa.String(), sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column("headline", sa.Text(), nullable=False, server_default=""),
        sa.Column("match_summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("team_tendencies", sa.Text(), nullable=False, server_default=""),
        sa.Column("formation_analysis", sa.Text(), nullable=False, server_default=""),
        sa.Column("pressing_analysis", sa.Text(), nullable=False, server_default=""),
        sa.Column("momentum_analysis", sa.Text(), nullable=False, server_default=""),
        sa.Column("counterfactual", sa.Text(), nullable=True),
        sa.Column("game_plan_compliance", sa.Text(), nullable=True),
        sa.Column("recommendations", sa.Text(), nullable=False, server_default=""),
        sa.Column("generated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("job_id"),
    )

    op.create_table(
        "user_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("direction", sa.String(), nullable=False, server_default="blueprint"),
        sa.Column("theme", sa.String(), nullable=False, server_default="dark"),
        sa.Column("contrast", sa.String(), nullable=False, server_default="normal"),
        sa.Column("density", sa.String(), nullable=False, server_default="comfortable"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("user_settings")
    op.drop_table("ai_reports")
    op.drop_table("player_stats")
    op.drop_table("tactical_summaries")
    op.drop_table("jobs")
    op.drop_table("teams")
