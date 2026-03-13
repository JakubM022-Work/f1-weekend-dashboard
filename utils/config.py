"""Konfiguracja - stałe aplikacji"""

import os

# Ścieżki
CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "cache")

# Streamlit
CURRENT_YEAR = 2026
PAGE_TITLE = "F1 Weekend Dashboard"
PAGE_ICON = "🏎️"

# Stałe dla degradacji opon
AVAILABLE_COMPOUNDS = ["SOFT", "MEDIUM", "HARD"]
MIN_STINT_LENGTH_OPTIONS = [3, 4, 5, 6, 7]
DEFAULT_MIN_STINT_LENGTH = 5

# Kolory zespołów
TEAM_COLORS = {
    "McLaren": "#FF8000",
    "Ferrari": "#DC0000",
    "Mercedes": "#00D2BE",
    "Red Bull Racing": "#1E5BC6",
    "Racing Bulls": "#6692FF",
    "Williams": "#005AFF",
    "Aston Martin": "#229971",
    "Alpine": "#FF87BC",
    "Haas F1 Team": "#B6BABD",
    "Kick Sauber": "#52E252",
    "Sauber": "#52E252",
    "Audi": "#7A7A7A",
    "Cadillac": "#A0A0A0",
}

# Kolory opon
TYRE_COLORS = {
    "SOFT": "#FF4D4D",
    "MEDIUM": "#FFD54A",
    "HARD": "#F5F5F5",
    "INTERMEDIATE": "#43A047",
    "WET": "#1E88E5",
    "UNKNOWN": "#9CA3AF",
}
