"""
AI tactical analysis service.

Reads the per-frame tactical_report.json written by `soccercv analyze`,
aggregates it into summary stats, and (optionally) calls Claude via
pydantic-ai to produce a structured coaching brief.

The aggregate_frames() function is also used by _ingest_tactical_report()
in jobs.py to populate the TacticalSummary DB row.
"""

from __future__ import annotations

import os
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

from pydantic import BaseModel


# ── Output type for pydantic-ai ───────────────────────────────────────────────


class TacticalBrief(BaseModel):
    """Maps 1:1 to AIReport DB columns."""

    headline: str
    match_summary: str
    team_tendencies: str
    formation_analysis: str
    pressing_analysis: str
    momentum_analysis: str
    counterfactual: str | None = None
    game_plan_compliance: str | None = None
    recommendations: str


# ── Frame aggregation ─────────────────────────────────────────────────────────


def aggregate_frames(frames: list[dict]) -> dict[str, Any]:
    """
    Aggregate per-frame tactical data into a flat summary dict.

    Returns two sets of keys:
      - DB keys  (possession_a, formation_a, momentum_data, …)
      - _ai dict (comp_a_in, press_a_avg, duration_str, …) — extra stats
        used by the AI prompt builder but not stored in TacticalSummary.
    """
    n = len(frames)
    if n == 0:
        return _empty_aggregate()

    # ── possession ────────────────────────────────────────────
    poss_a = sum(1 for f in frames if f.get("possession") == "TEAM_A")
    poss_b = sum(1 for f in frames if f.get("possession") == "TEAM_B")
    total_ab = poss_a + poss_b or 1
    possession_a = round(100 * poss_a / total_ab)
    possession_b = 100 - possession_a

    # ── ball zones ────────────────────────────────────────────
    zones: Counter = Counter(f.get("ball_zone", "UNKNOWN") for f in frames)
    total_z = sum(zones.values()) or 1
    zone_pct = {k: round(100 * v / total_z) for k, v in zones.most_common()}

    # ── formations ────────────────────────────────────────────
    def _top_formation(team_key: str) -> tuple[str, int]:
        counts: Counter = Counter(
            f.get(team_key, {}).get("formation", {}).get("shape", "?")
            for f in frames
        )
        top = counts.most_common(1)
        return (top[0][0], top[0][1]) if top else ("?", 0)

    form_a, form_a_count = _top_formation("TEAM_A")
    form_b, form_b_count = _top_formation("TEAM_B")
    stability_a = round(100 * form_a_count / n) if n else 0
    stability_b = round(100 * form_b_count / n) if n else 0

    # ── compactness averages (split by possession state) ──────
    def _compactness(team_key: str, in_possession: bool) -> tuple[float, float]:
        poss_val = team_key  # "TEAM_A" or "TEAM_B"
        depths, widths = [], []
        for f in frames:
            has_ball = f.get("possession") == poss_val
            if in_possession and not has_ball:
                continue
            if not in_possession and has_ball:
                continue
            c = f.get(team_key, {}).get("compactness", {})
            if (d := c.get("depth_m")) is not None:
                depths.append(d)
            if (w := c.get("width_m")) is not None:
                widths.append(w)
        return (
            round(statistics.mean(depths), 1) if depths else 0.0,
            round(statistics.mean(widths), 1) if widths else 0.0,
        )

    comp_a_in = _compactness("TEAM_A", True)
    comp_a_out = _compactness("TEAM_A", False)
    comp_b_in = _compactness("TEAM_B", True)
    comp_b_out = _compactness("TEAM_B", False)

    # ── pressing ──────────────────────────────────────────────
    def _press_avg(team_key: str) -> float:
        opp = "TEAM_B" if team_key == "TEAM_A" else "TEAM_A"
        vals = [
            f.get(team_key, {}).get("pressing", 0)
            for f in frames
            if f.get("possession") == opp
        ]
        return round(statistics.mean(vals), 2) if vals else 0.0

    press_a_avg = _press_avg("TEAM_A")
    press_b_avg = _press_avg("TEAM_B")
    high_press_a = round(
        100
        * sum(
            1
            for f in frames
            if f.get("possession") == "TEAM_B"
            and f.get("TEAM_A", {}).get("pressing", 0) >= 3
        )
        / max(poss_b, 1)
    )
    high_press_b = round(
        100
        * sum(
            1
            for f in frames
            if f.get("possession") == "TEAM_A"
            and f.get("TEAM_B", {}).get("pressing", 0) >= 3
        )
        / max(poss_a, 1)
    )

    # ── rolling possession for momentum chart (30-second windows) ─
    fps = 10  # engine outputs at 10fps by default
    step = max(1, fps * 30)
    times: list[float] = []
    momentum_home: list[int] = []
    momentum_away: list[int] = []
    for i in range(0, n, step):
        chunk = frames[i : i + step]
        ca = sum(1 for f in chunk if f.get("possession") == "TEAM_A")
        cb = sum(1 for f in chunk if f.get("possession") == "TEAM_B")
        total = ca + cb or 1
        pct_a = round(100 * ca / total)
        times.append(round(frames[i].get("timestamp_s", i / fps) / 60, 2))
        momentum_home.append(pct_a)
        momentum_away.append(100 - pct_a)

    momentum_data = [
        {"minute": t, "home": h, "away": a}
        for t, h, a in zip(times, momentum_home, momentum_away)
    ]

    # ── ball tracking summary ─────────────────────────────────
    detected = sum(1 for f in frames if f.get("ball_state") == "DETECTED")
    predicted = sum(1 for f in frames if f.get("ball_state") == "PREDICTED")
    lost = sum(1 for f in frames if f.get("ball_state") == "LOST")
    ball_tracking = {"detected": detected, "predicted": predicted, "lost": lost}

    # ── clip duration ─────────────────────────────────────────
    duration_s = frames[-1].get("timestamp_s", n / fps)
    mins, secs = divmod(int(duration_s), 60)
    duration_str = f"{mins}m {secs}s"

    return {
        # ── DB fields (TacticalSummary) ───────────────────────
        "possession_a": possession_a,
        "possession_b": possession_b,
        "formation_a": form_a,
        "formation_b": form_b,
        "stability_a": stability_a,
        "stability_b": stability_b,
        "ppda_a": None,
        "ppda_b": None,
        "momentum_data": momentum_data,
        "key_moments": [],
        "zone_pct": zone_pct,
        "ball_tracking": ball_tracking,
        "avg_positions_a": [],   # stripped from tactical_report.json
        "avg_positions_b": [],
        "pass_edges": [],
        "press_points": [],
        "shot_data": [],
        # ── AI-only fields (not stored in DB) ─────────────────
        "_ai": {
            "duration_str": duration_str,
            "comp_a_in": comp_a_in,
            "comp_a_out": comp_a_out,
            "comp_b_in": comp_b_in,
            "comp_b_out": comp_b_out,
            "press_a_avg": press_a_avg,
            "press_b_avg": press_b_avg,
            "high_press_a": high_press_a,
            "high_press_b": high_press_b,
            "momentum_times": times,
            "momentum_a": momentum_home,
        },
    }


def _empty_aggregate() -> dict[str, Any]:
    return {
        "possession_a": 50, "possession_b": 50,
        "formation_a": "?", "formation_b": "?",
        "stability_a": 0, "stability_b": 0,
        "ppda_a": None, "ppda_b": None,
        "momentum_data": [], "key_moments": [], "zone_pct": {},
        "ball_tracking": {}, "avg_positions_a": [], "avg_positions_b": [],
        "pass_edges": [], "press_points": [], "shot_data": [],
        "_ai": {
            "duration_str": "0m 0s",
            "comp_a_in": (0.0, 0.0), "comp_a_out": (0.0, 0.0),
            "comp_b_in": (0.0, 0.0), "comp_b_out": (0.0, 0.0),
            "press_a_avg": 0.0, "press_b_avg": 0.0,
            "high_press_a": 0, "high_press_b": 0,
            "momentum_times": [], "momentum_a": [],
        },
    }


# ── Prompt builder ────────────────────────────────────────────────────────────


def _momentum_summary(times: list[float], values_a: list[int]) -> str:
    if not times or not values_a:
        return "No momentum data available."
    segments: list[str] = []
    dominant = "A" if values_a[0] >= 50 else "B"
    seg_start = times[0]
    for i, (t, v) in enumerate(zip(times, values_a)):
        curr = "A" if v >= 50 else "B"
        if curr != dominant or i == len(times) - 1:
            segments.append(f"{seg_start:.1f}–{t:.1f}min: Team {dominant} dominant")
            dominant = curr
            seg_start = t
    return " | ".join(segments[:8])


def _build_prompt(
    agg: dict[str, Any],
    team_a: str,
    team_b: str,
    score_a: int | None,
    score_b: int | None,
    coach_notes: str,
    game_plan: list[str],
) -> str:
    ai = agg["_ai"]
    score_str = (
        f"{score_a}–{score_b}"
        if score_a is not None and score_b is not None
        else "not provided"
    )
    game_plan_str = (
        "\n".join(f"  - {i}" for i in game_plan)
        if game_plan
        else "  (no game plan provided)"
    )
    coach_str = coach_notes.strip() or "(none)"
    momentum = _momentum_summary(ai["momentum_times"], ai["momentum_a"])

    zone = agg["zone_pct"]
    zone_def = zone.get("DEF_THIRD_A", zone.get("DEF", 0))
    zone_mid = zone.get("MIDFIELD", zone.get("MID", 0))
    zone_att = zone.get("ATT_THIRD_A", zone.get("ATT", 0))

    comp_ai, comp_ao = ai["comp_a_in"], ai["comp_a_out"]
    comp_bi, comp_bo = ai["comp_b_in"], ai["comp_b_out"]

    return f"""Match: {team_a} vs {team_b}
Final score: {score_str}
Clip duration analysed: {ai["duration_str"]}

POSSESSION
  {team_a}: {agg["possession_a"]}%
  {team_b}: {agg["possession_b"]}%

BALL ZONE DISTRIBUTION (% of frames)
  {team_a} defensive third: {zone_def}%
  Midfield: {zone_mid}%
  {team_a} attacking third: {zone_att}%

MOMENTUM (rolling 30-second windows)
  {momentum}

FORMATIONS
  {team_a}: {agg["formation_a"]}  (held {agg["stability_a"]}% of frames)
  {team_b}: {agg["formation_b"]}  (held {agg["stability_b"]}% of frames)

COMPACTNESS (team shape in metres)
  {team_a} in possession:      depth {comp_ai[0]}m  width {comp_ai[1]}m
  {team_a} out of possession:  depth {comp_ao[0]}m  width {comp_ao[1]}m
  {team_b} in possession:      depth {comp_bi[0]}m  width {comp_bi[1]}m
  {team_b} out of possession:  depth {comp_bo[0]}m  width {comp_bo[1]}m

PRESSING (when opponent has possession)
  {team_a}: avg {ai["press_a_avg"]:.1f} pressers near ball,
           high press (≥3 pressers) in {ai["high_press_a"]}% of defending situations
  {team_b}: avg {ai["press_b_avg"]:.1f} pressers near ball,
           high press (≥3 pressers) in {ai["high_press_b"]}% of defending situations

COACH'S GAME PLAN FOR {team_a}
{game_plan_str}

ADDITIONAL COACH CONTEXT
{coach_str}"""


# ── pydantic-ai agent ─────────────────────────────────────────────────────────

_agent: "Agent[None, TacticalBrief] | None" = None


def _get_agent() -> "Agent[None, TacticalBrief]":
    """Lazy singleton — ensures ANTHROPIC_API_KEY is loaded before first use."""
    global _agent
    if _agent is None:
        from pydantic_ai import Agent
        from pydantic_ai.models.anthropic import AnthropicModel

        _agent = Agent(
            AnthropicModel("claude-sonnet-4-6"),
            output_type=TacticalBrief,
            system_prompt=(
                "You are an expert soccer tactical analyst. "
                "Produce structured tactical coaching reports from match statistics. "
                "Be specific, reference actual numbers, and be actionable. "
                "Set counterfactual to null unless a final score was provided. "
                "Set game_plan_compliance to null unless game plan instructions were given. "
                "headline should be a single compelling sentence summarising the match."
            ),
            model_settings={"max_tokens": 4096},
        )
    return _agent


async def generate_tactical_brief(
    agg: dict[str, Any],
    team_a: str,
    team_b: str,
    score_a: int | None = None,
    score_b: int | None = None,
    coach_notes: str = "",
    game_plan: list[str] | None = None,
) -> TacticalBrief:
    """
    Call Claude via pydantic-ai and return a fully validated TacticalBrief.
    Raises RuntimeError if ANTHROPIC_API_KEY is not set.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set — cannot generate AI report. "
            "Add it to .env and restart the backend."
        )

    prompt = _build_prompt(
        agg=agg,
        team_a=team_a,
        team_b=team_b,
        score_a=score_a,
        score_b=score_b,
        coach_notes=coach_notes,
        game_plan=game_plan or [],
    )

    agent = _get_agent()
    result = await agent.run(prompt)
    return result.output
