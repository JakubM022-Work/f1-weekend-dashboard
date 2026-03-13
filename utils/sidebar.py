"""Sidebar - ustawienia i wybór rundy/sezonu"""

import pandas as pd
import streamlit as st
from utils.loaders import get_event_schedule


def init_session_state():
    """Inicjuj zmienne stan sesji dla dashboarda"""
    if "dashboard_loaded" not in st.session_state:
        st.session_state.dashboard_loaded = False

    if "selected_season" not in st.session_state:
        st.session_state.selected_season = None

    if "selected_round_number" not in st.session_state:
        st.session_state.selected_round_number = None

    if "selected_event_name" not in st.session_state:
        st.session_state.selected_event_name = None


def render_sidebar(current_year: int = 2026):
    """Renderuj sidebar z opcjami wyboru rundy i sezonu"""
    st.sidebar.header("Ustawienia")

    season = st.sidebar.selectbox(
        "Sezon",
        options=list(range(2018, current_year + 1))[::-1],
        index=0
    )

    try:
        schedule = get_event_schedule(season)

        if "RoundNumber" not in schedule.columns or "EventName" not in schedule.columns:
            st.error("Nie udało się wczytać harmonogramu sezonu.")
            st.stop()

        race_events = schedule[schedule["RoundNumber"].notna()].copy()
        race_events["RoundNumber"] = pd.to_numeric(race_events["RoundNumber"], errors="coerce")
        race_events = race_events[race_events["RoundNumber"].notna()].copy()
        race_events = race_events[race_events["RoundNumber"] > 0].copy()

        race_events["RoundNumber"] = race_events["RoundNumber"].astype(int)
        race_events["label"] = race_events.apply(
            lambda row: f"Runda {row['RoundNumber']} — {row['EventName']}",
            axis=1
        )

        event_labels = race_events["label"].tolist()

        if not event_labels:
            st.error("Brak dostępnych rund dla wybranego sezonu.")
            st.stop()

        selected_label = st.sidebar.selectbox("Grand Prix", options=event_labels)
        selected_event = race_events[race_events["label"] == selected_label].iloc[0]
        round_number = int(selected_event["RoundNumber"])
        event_name = selected_event["EventName"]

        load_clicked = st.sidebar.button("Załaduj dashboard")

        if load_clicked:
            st.session_state.dashboard_loaded = True
            st.session_state.selected_season = season
            st.session_state.selected_round_number = round_number
            st.session_state.selected_event_name = event_name

        return {
            "season": season,
            "round_number": round_number,
            "event_name": event_name,
        }

    except Exception as e:
        st.error(f"Błąd przy ładowaniu harmonogramu: {e}")
        st.stop()
