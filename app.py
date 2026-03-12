import os
import pandas as pd
import streamlit as st
import fastf1

from utils.loaders import get_event_schedule, load_session_results, load_race_laps
from utils.analysis import (
    prepare_qualifying_top10,
    prepare_race_top10,
    calculate_position_changes,
    prepare_stint_data,
)
from utils.charts import plot_stints


# =========================
# Konfiguracja
# =========================
cache_dir = os.path.join(os.path.dirname(__file__), "cache")
os.makedirs(cache_dir, exist_ok=True)
fastf1.Cache.enable_cache(cache_dir)

st.set_page_config(
    page_title="F1 Weekend Dashboard",
    page_icon="🏎️",
    layout="wide",
)

st.title("🏎️ F1 Weekend Dashboard")


# =========================
# Sidebar
# =========================
st.sidebar.header("Ustawienia")

current_year = 2026
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

except Exception as e:
    st.error(f"Błąd przy ładowaniu harmonogramu: {e}")
    st.stop()


# =========================
# Główna akcja
# =========================
if st.sidebar.button("Załaduj dashboard"):
    try:
        with st.spinner("Ładowanie kwalifikacji, wyścigu i stintów..."):
            quali_results = load_session_results(season, round_number, "Q")
            race_results = load_session_results(season, round_number, "R")
            race_laps = load_race_laps(season, round_number)

        st.subheader(f"{event_name} ({season})")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Top 10 kwalifikacji")
            quali_top10 = prepare_qualifying_top10(quali_results)
            if not quali_top10.empty:
                st.dataframe(quali_top10, use_container_width=True, hide_index=True)
            else:
                st.info("Brak danych kwalifikacji do wyświetlenia.")

        with col2:
            st.markdown("### Top 10 wyścigu")
            race_top10 = prepare_race_top10(race_results)
            if not race_top10.empty:
                st.dataframe(race_top10, use_container_width=True, hide_index=True)
            else:
                st.info("Brak danych wyścigu do wyświetlenia.")

        changes = calculate_position_changes(race_results)

        if not changes.empty:
            best_gainers = changes.sort_values("PositionsChanged", ascending=False).head(5)
            biggest_losers = changes.sort_values("PositionsChanged", ascending=True).head(5)

            col3, col4 = st.columns(2)

            with col3:
                st.markdown("### Najwięcej zyskanych pozycji")
                st.dataframe(best_gainers, use_container_width=True, hide_index=True)

            with col4:
                st.markdown("### Najwięcej straconych pozycji")
                st.dataframe(biggest_losers, use_container_width=True, hide_index=True)
        else:
            st.info("Nie udało się obliczyć zmian pozycji.")

        st.markdown("### Wykres stintów na oponach")
        st.caption("Każdy pasek pokazuje długość kolejnych stintów kierowcy podczas wyścigu.")

        stint_data = prepare_stint_data(race_laps)
        fig = plot_stints(stint_data)

        if fig is not None:
            st.pyplot(fig, use_container_width=True)
        else:
            st.info("Brak danych stintów do wyświetlenia.")

    except Exception as e:
        st.error(f"Wystąpił błąd przy ładowaniu danych: {e}")
else:
    st.info("Wybierz sezon i rundę po lewej stronie, a następnie kliknij „Załaduj dashboard”.")