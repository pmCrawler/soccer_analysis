import reflex as rx
import asyncio
from typing import TypedDict


class ReportState(rx.State):
    selected_match_id: str = ""
    report_loaded: bool = False
    active_section: str = "Overview"
    is_generating_report: bool = False
    match_summary: dict[str, str | int] = {
        "home_team": "Arsenal",
        "away_team": "Chelsea",
        "competition": "Premier League",
        "date": "2024-05-10",
        "venue": "Emirates Stadium",
        "score_home": 2,
        "score_away": 1,
        "referee": "Michael Oliver",
        "attendance": "60,230",
    }
    key_moments: list[dict[str, str]] = [
        {
            "minute": "14'",
            "event_type": "Goal",
            "description": "Saka cuts inside and curls into bottom corner",
            "player": "B. Saka",
        },
        {
            "minute": "32'",
            "event_type": "Yellow Card",
            "description": "Late tackle in midfield",
            "player": "E. Fernández",
        },
        {
            "minute": "45'",
            "event_type": "Key Save",
            "description": "Raya tips header over the bar",
            "player": "D. Raya",
        },
        {
            "minute": "67'",
            "event_type": "Goal",
            "description": "Palmer penalty after foul in box",
            "player": "C. Palmer",
        },
        {
            "minute": "84'",
            "event_type": "Goal",
            "description": "Rice rocket from edge of the box",
            "player": "D. Rice",
        },
        {
            "minute": "90+2'",
            "event_type": "Red Card",
            "description": "Second yellow for tactical foul",
            "player": "M. Caicedo",
        },
    ]
    team_comparison: list[dict[str, str | int]] = [
        {"stat": "Possession %", "home": 58, "away": 42},
        {"stat": "Shots", "home": 16, "away": 9},
        {"stat": "Shots on Target", "home": 7, "away": 3},
        {"stat": "Passes", "home": 540, "away": 395},
        {"stat": "Pass Accuracy %", "home": 88, "away": 81},
        {"stat": "Corners", "home": 8, "away": 4},
        {"stat": "Fouls", "home": 11, "away": 14},
    ]
    top_performers: list[dict[str, str]] = [
        {
            "name": "Declan Rice",
            "position": "CDM",
            "rating": "8.9",
            "key_stat_label": "Pass Accuracy",
            "key_stat_value": "94%",
        },
        {
            "name": "Bukayo Saka",
            "position": "RW",
            "rating": "8.5",
            "key_stat_label": "Chances Created",
            "key_stat_value": "4",
        },
        {
            "name": "Cole Palmer",
            "position": "CAM",
            "rating": "8.2",
            "key_stat_label": "Shots on Target",
            "key_stat_value": "2",
        },
    ]
    tactical_insights: list[dict[str, str]] = [
        {
            "title": "High Press Effectiveness",
            "description": "Arsenal's high press forced 12 turnovers in the first half, preventing Chelsea from building from the back.",
        },
        {
            "title": "Counter-Attack Patterns",
            "description": "Chelsea exploited space behind the full-backs, launching 4 dangerous counters down the right flank.",
        },
        {
            "title": "Set Piece Threat",
            "description": "3 of 11 corners resulted in shots on target, utilizing near-post runs effectively.",
        },
    ]
    formation_phases: list[dict[str, str]] = [
        {
            "minute": "0-60 min",
            "formation": "4-3-3",
            "reason": "Starting tactical setup to control midfield.",
        },
        {
            "minute": "60-85 min",
            "formation": "4-2-3-1",
            "reason": "Adapted to Chelsea's midfield overload.",
        },
        {
            "minute": "85-90 min",
            "formation": "5-4-1",
            "reason": "Defensive block to secure the lead.",
        },
    ]

    @rx.event
    def load_report(self, match_id: str):
        self.selected_match_id = match_id
        self.report_loaded = True
        self.active_section = "Overview"
        return rx.redirect("/reports")

    @rx.event
    def clear_report(self):
        self.selected_match_id = ""
        self.report_loaded = False

    @rx.event
    def set_active_section(self, section: str):
        self.active_section = section

    @rx.event
    async def generate_html_report(self):
        self.is_generating_report = True
        yield
        await asyncio.sleep(1.5)
        html_content = f"<html><head><style>body{{font-family:sans-serif;}}</style></head><body><h1>Match Report: {self.match_summary['home_team']} vs {self.match_summary['away_team']}</h1><p>Score: {self.match_summary['score_home']} - {self.match_summary['score_away']}</p></body></html>"
        self.is_generating_report = False
        yield rx.download(
            data=html_content,
            filename=f"SoccerCV_Report_{self.selected_match_id or 'match'}.html",
        )