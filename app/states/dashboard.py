import reflex as rx
from typing import TypedDict


class PlayerStat(TypedDict):
    name: str
    position: str
    passes: int
    accuracy: str
    tackles: int
    distance: str
    rating: str


class DashboardState(rx.State):
    selected_match: str = "Arsenal vs Chelsea - Premier League"
    available_matches: list[str] = [
        "Arsenal vs Chelsea - Premier League",
        "Barcelona vs Real Madrid - La Liga",
        "Liverpool vs Man City - PL",
        "Bayern vs Dortmund - Bundesliga",
    ]
    selected_player: str = "All Players"
    available_players: list[str] = [
        "All Players",
        "Saka",
        "Ødegaard",
        "Rice",
        "Saliba",
        "Havertz",
        "Sterling",
        "Palmer",
        "Enzo",
        "Caicedo",
        "Colwill",
    ]
    selected_time_segment: str = "Full Match"
    time_segments: list[str] = [
        "Full Match",
        "1st Half",
        "2nd Half",
        "0-15 min",
        "15-30 min",
        "30-45 min",
        "45-60 min",
        "60-75 min",
        "75-90 min",
    ]
    selected_event_filter: str = "All Events"
    event_filters: list[str] = [
        "All Events",
        "Goals",
        "Assists",
        "Tackles",
        "Passes",
        "Shots",
        "Fouls",
        "Corners",
    ]
    total_passes: int = 847
    total_shots: int = 24
    total_tackles: int = 38
    total_distance_km: float = 112.4
    goals_scored: int = 3
    corners: int = 11
    fouls: int = 18
    offsides: int = 4
    formation_stability: float = 87.3
    defensive_line_avg: float = 34.2

    @rx.var
    def possession_data(self) -> list[dict[str, str | int]]:
        return [
            {"name": "Home", "value": 58, "fill": "#7ab8e0"},
            {"name": "Away", "value": 42, "fill": "#4a5666"},
        ]

    @rx.var
    def passing_accuracy_data(self) -> list[dict[str, str | int]]:
        return [
            {"name": "Saliba", "accuracy": 94, "completed": 88},
            {"name": "Rice", "accuracy": 92, "completed": 75},
            {"name": "Enzo", "accuracy": 89, "completed": 82},
            {"name": "Ødegaard", "accuracy": 86, "completed": 64},
            {"name": "Caicedo", "accuracy": 85, "completed": 71},
            {"name": "Saka", "accuracy": 81, "completed": 45},
        ]

    @rx.var
    def match_momentum_data(self) -> list[dict[str, str | int | float]]:
        return [
            {"minute": 0, "home": 50, "away": 50},
            {"minute": 15, "home": 65, "away": 35},
            {"minute": 30, "home": 45, "away": 55},
            {"minute": 45, "home": 70, "away": 30},
            {"minute": 60, "home": 55, "away": 45},
            {"minute": 75, "home": 40, "away": 60},
            {"minute": 90, "home": 80, "away": 20},
        ]

    @rx.var
    def defensive_actions_data(self) -> list[dict[str, str | int]]:
        return [
            {"action": "Tackles", "home": 18, "away": 20},
            {"action": "Intercept", "home": 12, "away": 15},
            {"action": "Clear", "home": 22, "away": 18},
            {"action": "Blocks", "home": 5, "away": 8},
        ]

    @rx.var
    def attacking_zones_data(self) -> list[dict[str, str | int]]:
        return [
            {"zone": "Left", "home": 35, "away": 25},
            {"zone": "Center", "home": 25, "away": 45},
            {"zone": "Right", "home": 40, "away": 30},
        ]

    @rx.var
    def player_stats(self) -> list[PlayerStat]:
        return [
            {
                "name": "Bukayo Saka",
                "position": "RW",
                "passes": 45,
                "accuracy": "81%",
                "tackles": 2,
                "distance": "10.2",
                "rating": "8.4",
            },
            {
                "name": "Martin Ødegaard",
                "position": "CAM",
                "passes": 64,
                "accuracy": "86%",
                "tackles": 1,
                "distance": "11.5",
                "rating": "8.1",
            },
            {
                "name": "Declan Rice",
                "position": "CDM",
                "passes": 75,
                "accuracy": "92%",
                "tackles": 4,
                "distance": "11.8",
                "rating": "7.9",
            },
            {
                "name": "William Saliba",
                "position": "CB",
                "passes": 88,
                "accuracy": "94%",
                "tackles": 3,
                "distance": "9.8",
                "rating": "7.7",
            },
            {
                "name": "Cole Palmer",
                "position": "CAM",
                "passes": 52,
                "accuracy": "83%",
                "tackles": 1,
                "distance": "10.9",
                "rating": "7.8",
            },
            {
                "name": "Enzo Fernández",
                "position": "CM",
                "passes": 82,
                "accuracy": "89%",
                "tackles": 3,
                "distance": "11.1",
                "rating": "7.5",
            },
            {
                "name": "Moises Caicedo",
                "position": "CDM",
                "passes": 71,
                "accuracy": "85%",
                "tackles": 5,
                "distance": "11.3",
                "rating": "7.6",
            },
        ]

    @rx.event
    def set_selected_match(self, match: str):
        self.selected_match = match
        yield rx.toast(f"Loaded data for {match}")

    @rx.event
    def set_selected_player(self, player: str):
        self.selected_player = player

    @rx.event
    def set_selected_time_segment(self, segment: str):
        self.selected_time_segment = segment

    @rx.event
    def set_selected_event_filter(self, event: str):
        self.selected_event_filter = event