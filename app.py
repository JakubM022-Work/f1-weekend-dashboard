import os
import pandas as pd
import streamlit as st
import fastf1

# Importy z utils - loaders, analiza, wykresy
from utils.loaders import (
    load_session_results,
    load_race_laps,
    load_race_laps_full,
)
from utils.analysis import (
    prepare_qualifying_top22,
    prepare_race_top22,
    calculate_position_changes,
    prepare_stint_data,
    get_pole_sitter,
    get_race_winner,
    get_biggest_gainer_and_loser,
    get_quick_stats,
    filter_laps_for_degradation,
    summarize_degradation,
    format_seconds_to_laptime,
    get_degradation_insight,
)
from utils.charts import plot_stints, plot_tyre_degradation

# Importy z refactorowanych modułów
from utils.styles import DASHBOARD_STYLES
from utils.components import (
    render_results_cards,
    render_position_change_cards,
    render_hero_card,
    render_metric_card,
    render_tyre_compounds_legend,
)
from utils.sidebar import init_session_state, render_sidebar
from utils.config import (
    CACHE_DIR,
    PAGE_TITLE,
    PAGE_ICON,
    CURRENT_YEAR,
    AVAILABLE_COMPOUNDS,
    MIN_STINT_LENGTH_OPTIONS,
)

# =========================
# Setup
# =========================
os.makedirs(CACHE_DIR, exist_ok=True)
fastf1.Cache.enable_cache(CACHE_DIR)

st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout="wide",
)

st.title(f"{PAGE_ICON} {PAGE_TITLE}")
st.markdown(DASHBOARD_STYLES, unsafe_allow_html=True)

# =========================
# Session State
# =========================
init_session_state()

# =========================
# Sidebar
# =========================
sidebar_data = render_sidebar(CURRENT_YEAR)

# =========================
# Główny Dashboard
# =========================
if st.session_state.dashboard_loaded:
    try:
        active_season = st.session_state.selected_season
        active_round_number = st.session_state.selected_round_number
        active_event_name = st.session_state.selected_event_name

        # Ładowanie danych
        with st.spinner("Ładowanie kwalifikacji, wyścigu i stintów..."):
            quali_results = load_session_results(active_season, active_round_number, "Q")
            race_results = load_session_results(active_season, active_round_number, "R")
            race_laps = load_race_laps(active_season, active_round_number)
            race_laps_full = load_race_laps_full(active_season, active_round_number)

        # Przygotowanie danych
        quali_top22 = prepare_qualifying_top22(quali_results)
        race_top22 = prepare_race_top22(race_results)
        changes = calculate_position_changes(race_results)
        stint_data = prepare_stint_data(race_laps)

        pole_sitter = get_pole_sitter(quali_results)
        race_winner = get_race_winner(race_results)
        biggest_gainer, biggest_loser = get_biggest_gainer_and_loser(changes)
        quick_stats = get_quick_stats(race_results, stint_data, changes)

        # Karta heroiczna
        render_hero_card(active_round_number, active_event_name, active_season, quick_stats)

        # Metryki w 4 kolumnach
        c1, c2, c3, c4 = st.columns(4)

        with c1:
            render_metric_card(
                "Pole position",
                pole_sitter['driver'] if pole_sitter else '—',
                pole_sitter['team'] if pole_sitter else ''
            )

        with c2:
            render_metric_card(
                "Winner",
                race_winner['driver'] if race_winner else '—',
                race_winner['team'] if race_winner else ''
            )

        with c3:
            gainer_value = f"+{int(biggest_gainer['PositionsChanged'])}" if biggest_gainer else ""
            render_metric_card(
                "Biggest gainer",
                biggest_gainer["Driver"] if biggest_gainer else "—",
                gainer_value
            )

        with c4:
            loser_value = str(int(biggest_loser["PositionsChanged"])) if biggest_loser else ""
            render_metric_card(
                "Biggest loser",
                biggest_loser["Driver"] if biggest_loser else "—",
                loser_value
            )

        # Tabs z zawartością
        tab1, tab2, tab3, tab4, tab5 = st.tabs(
            ["Podsumowanie", "Kwalifikacje", "Wyścig", "Stinty", "Degradacja opon"]
        )

        with tab1:
            st.markdown("### Przegląd Weekendu")
            col1, col2 = st.columns(2)

            with col1:
                render_results_cards(quali_top22, "Top kwalifikacji", mode="quali")

            with col2:
                render_results_cards(race_top22, "Top wyścigu", mode="race")

            col3, col4 = st.columns(2)

            with col3:
                if not changes.empty:
                    render_position_change_cards(
                        changes.sort_values("PositionsChanged", ascending=False).head(5),
                        "Najwięcej zyskanych pozycji"
                    )
                else:
                    st.info("Brak danych.")

            with col4:
                if not changes.empty:
                    render_position_change_cards(
                        changes.sort_values("PositionsChanged", ascending=True).head(5),
                        "Najwięcej straconych pozycji"
                    )
                else:
                    st.info("Brak danych.")

        with tab2:
            st.markdown("### Wyniki Kwalifikacji")
            if not quali_top22.empty:
                st.dataframe(quali_top22, use_container_width=True, hide_index=True)
            else:
                st.info("Brak danych kwalifikacji do wyświetlenia.")

        with tab3:
            st.markdown("### Wyniki Wyścigu")
            if not race_top22.empty:
                st.dataframe(race_top22, use_container_width=True, hide_index=True)
            else:
                st.info("Brak danych wyścigu do wyświetlenia.")

            st.markdown("### Zmiany Pozycji")
            if not changes.empty:
                st.dataframe(changes, use_container_width=True, hide_index=True)
            else:
                st.info("Nie udało się obliczyć zmian pozycji.")

        with tab4:
            st.markdown("### Strategie Opon")
            st.caption("Każdy pasek pokazuje długość kolejnych stintów kierowcy podczas wyścigu.")

            render_tyre_compounds_legend()

            fig = plot_stints(stint_data)
            if fig is not None:
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("Brak danych stintów do wyświetlenia.")

        with tab5:
            st.markdown("### Analiza Degradacji Opon")

            available_drivers = sorted(race_laps_full["Driver"].dropna().unique().tolist()) if not race_laps_full.empty else []

            col_a, col_b, col_c = st.columns([2, 1, 1])

            with col_a:
                selected_drivers = st.multiselect(
                    "Wybierz kierowców",
                    options=available_drivers,
                    default=available_drivers[:2] if len(available_drivers) >= 2 else available_drivers,
                    max_selections=3,
                    key="deg_drivers"
                )

            with col_b:
                selected_compound = st.selectbox(
                    "Compound",
                    options=AVAILABLE_COMPOUNDS,
                    index=1,
                    key="deg_compound"
                )

            with col_c:
                min_stint_length = st.selectbox(
                    "Min. długość stintu",
                    options=MIN_STINT_LENGTH_OPTIONS,
                    index=2,
                    key="deg_min_stint"
                )

            degradation_df = filter_laps_for_degradation(
                race_laps_full,
                selected_drivers,
                selected_compound,
                min_stint_length=min_stint_length,
            )

            driver_team_map = (
                race_results[["Abbreviation", "TeamName"]]
                .dropna()
                .drop_duplicates()
                .rename(columns={"Abbreviation": "Driver", "TeamName": "Team"})
            )

            degradation_df = degradation_df.merge(driver_team_map, on="Driver", how="left")

            if degradation_df.empty:
                st.info("Brak danych spełniających wybrane kryteria.")
            else:
                deg_fig = plot_tyre_degradation(degradation_df)
                if deg_fig is not None:
                    st.plotly_chart(deg_fig, use_container_width=True, config={"displayModeBar": False})

                degradation_summary = summarize_degradation(degradation_df)

                if not degradation_summary.empty:
                    display_summary = degradation_summary.copy()
                    display_summary["Avg Pace"] = display_summary["AvgPaceSeconds"].apply(format_seconds_to_laptime)
                    display_summary["First Lap"] = display_summary["FirstLapSeconds"].apply(format_seconds_to_laptime)
                    display_summary["Last Lap"] = display_summary["LastLapSeconds"].apply(format_seconds_to_laptime)
                    display_summary["Deg/Lap (s)"] = display_summary["DegPerLapSeconds"].round(3)

                    display_summary = display_summary[
                        ["Driver", "Stint", "Compound", "Laps", "Avg Pace", "First Lap", "Last Lap", "Deg/Lap (s)"]
                    ]

                    st.markdown("### Podsumowanie Stintów")
                    st.dataframe(display_summary, use_container_width=True, hide_index=True)

                    insight = get_degradation_insight(degradation_summary)
                    st.markdown(
                        f"""
                        <div class="metric-card" style="margin-top: 14px;">
                            <div class="metric-label">Wniosek</div>
                            <div class="metric-subvalue" style="font-size:1rem; color:#F3F4F6;">
                                {insight}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

    except Exception as e:
        st.error(f"Wystąpił błąd przy ładowaniu danych: {e}")

else:
    st.info("Wybierz sezon i runde po lewej stronie, a nastepnie kliknij 'Zaladuj dashboard'.")
