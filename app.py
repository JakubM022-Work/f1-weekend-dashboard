import os
import pandas as pd
import streamlit as st
import fastf1

# Importy z utils - loaders, analiza, wykresy
from utils.loaders import (
    load_session_results,
    load_race_laps,
    load_race_laps_full,
    load_car_data_for_lap,
    get_fastest_lap,
    load_drivers_for_session,
    load_session_with_telemetry,
    get_car_data_from_lap,
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
from utils.telemetry_viz import plot_telemetry_vs_distance
from utils.charts import plot_stints, plot_tyre_degradation, plot_track_map, plot_sector_analysis, plot_comparison_lap_time

# Importy z refactorowanych modułów
from utils.styles import DASHBOARD_STYLES
from utils.components import (
    render_results_cards,
    render_position_change_cards,
    render_hero_card,
    render_metric_card,
    render_tyre_compounds_legend,
    render_small_stat_card,
    render_degradation_summary_cards,
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
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
            ["Podsumowanie", "Kwalifikacje", "Wyścig", "Stinty", "Degradacja opon", "📍 Telemetria Toru"]
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

            # Obsługa fallback - jeśli nie ma "Driver" w race_laps_full, użyj race_results
            if not race_laps_full.empty and "Driver" in race_laps_full.columns:
                available_drivers = sorted(race_laps_full["Driver"].dropna().unique().tolist())
            elif not race_results.empty and "Abbreviation" in race_results.columns:
                available_drivers = sorted(race_results["Abbreviation"].dropna().unique().tolist())
            else:
                available_drivers = []
            
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
            st.markdown("</div>", unsafe_allow_html=True)

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
                degradation_summary = summarize_degradation(degradation_df)

                if not degradation_summary.empty:
                    best_avg = degradation_summary.sort_values("AvgPaceSeconds").iloc[0]
                    best_deg = degradation_summary.sort_values("DegPerLapSeconds").iloc[0]
                    longest_stint = degradation_summary.sort_values("Laps", ascending=False).iloc[0]

                    s1, s2, s3 = st.columns(3)

                    with s1:
                        render_small_stat_card(
                            "Best avg pace",
                            str(best_avg["Driver"]),
                            format_seconds_to_laptime(best_avg["AvgPaceSeconds"])
                        )

                    with s2:
                        render_small_stat_card(
                            "Lowest degradation",
                            str(best_deg["Driver"]),
                            f'{best_deg["DegPerLapSeconds"]:.3f} s/lap'
                        )

                    with s3:
                        render_small_stat_card(
                            "Longest stint",
                            str(longest_stint["Driver"]),
                            f'{int(longest_stint["Laps"])} laps'
                        )

                deg_fig = plot_tyre_degradation(degradation_df)
                if deg_fig is not None:
                    st.plotly_chart(deg_fig, use_container_width=True, config={"displayModeBar": False})

                if not degradation_summary.empty:
                    render_degradation_summary_cards(degradation_summary, format_seconds_to_laptime)

                    insight = get_degradation_insight(degradation_summary)
                    st.markdown(
                        f"""
                        <div class="insight-card">
                            <div class="insight-title">Wniosek analityczny</div>
                            <div class="insight-text">{insight}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

        with tab6:
            st.markdown("### 📍 Mapa Toru z Telemetrią")
            st.caption("Wizualizacja ścieżki jazdy kierowcy na torze z kolorowaniem zależnie od wybranej metryki (prędkość, throttle, hamulce).")

            try:
                # Selektor sesji i kierowcy
                col_session, col_driver, col_metric = st.columns(3)

                with col_session:
                    session_type = st.selectbox(
                        "Sesja",
                        options=["Race", "Qualifying"],
                        index=0,
                        key="telemetry_session"
                    )
                    session_code = "R" if session_type == "Race" else "Q"

                with col_driver:
                    available_drivers_telemetry = load_drivers_for_session(active_season, active_round_number, session_code)
                    
                    if not available_drivers_telemetry:
                        st.warning(f"Brak kierowców dla sesji {session_type}")
                        selected_driver = None
                    else:
                        selected_driver = st.selectbox(
                            "Kierowca",
                            options=available_drivers_telemetry,
                            key="telemetry_driver"
                        )

                with col_metric:
                    metric_choice = st.selectbox(
                        "Metryka kolorowania",
                        options=["Speed", "Throttle", "Brake"],
                        index=0,
                        key="telemetry_metric"
                    )

                # Selektor okrążenia
                if selected_driver:
                    st.markdown("---")
                    
                    # Załaduj sesję z telemetrią
                    with st.spinner(f"Ładuję sesję {session_type} z telemetrią..."):
                        session_tel = load_session_with_telemetry(active_season, active_round_number, session_code)
                    
                    print(f"\n[APP] session_tel type: {type(session_tel)}")
                    print(f"[APP] session_tel: {session_tel}")
                    
                    if session_tel is None:
                        st.error("❌ Nie udało się załadować sesji z telemetrią.")
                    else:
                        # Pobranie lapów dla kierowcy
                        try:
                            driver_laps = session_tel.laps.pick_driver(selected_driver)
                            print(f"[APP] driver_laps from pick_driver: {len(driver_laps)} laps")
                        except Exception as e:
                            print(f"[APP] pick_driver failed: {e}, trying fallback")
                            driver_laps = session_tel.laps[session_tel.laps["Driver"] == selected_driver]
                            print(f"[APP] driver_laps from fallback: {len(driver_laps)} laps")
                        
                        if not driver_laps.empty:
                            # Wszystkie lapy kierowcy
                            all_lap_numbers = sorted(driver_laps["LapNumber"].dropna().astype(int).unique().tolist())
                            
                            print(f"[APP] All lap numbers for {selected_driver}: {all_lap_numbers}")
                            st.write(f"Dostępne okrążenia: {len(all_lap_numbers)}")
                            
                            # Najszybszy lap
                            accurate_laps = driver_laps[driver_laps["IsAccurate"] == True] if "IsAccurate" in driver_laps.columns else driver_laps
                            if len(accurate_laps) > 0:
                                fastest = accurate_laps.sort_values("LapTime").iloc[0]
                                fastest_lap_num = int(fastest["LapNumber"])
                                st.markdown(f"**Najszybsze okrążenie: #{fastest_lap_num}**")
                            
                            st.write("Wybierz okrążenie:")
                            selected_lap = st.select_slider(
                                "Numer okrążenia",
                                options=all_lap_numbers,
                                value=all_lap_numbers[-1] if all_lap_numbers else 1,
                                key="telemetry_lap"
                            )
                            
                            # Pobierz dane dla wybranego lapa
                            st.write("---")
                            
                            with st.spinner(f"Ładuję telemetrię dla okrążenia {selected_lap}..."):
                                selected_lap_obj = driver_laps[driver_laps["LapNumber"] == selected_lap]
                                
                                if not selected_lap_obj.empty:
                                    selected_lap_obj = selected_lap_obj.iloc[0]
                                    car_data = get_car_data_from_lap(selected_lap_obj)
                                    
                                    if car_data is not None and len(car_data) > 0:
                                        # DEBUG: Sprawdzenie kolumn
                                        print(f"\n[APP] car_data shape: {car_data.shape}")
                                        print(f"[APP] car_data columns: {list(car_data.columns)}")
                                        print(f"[APP] car_data dtypes:\n{car_data.dtypes}")
                                        print(f"[APP] Has X?Y?: X={('X' in car_data.columns)}, Y={('Y' in car_data.columns)}")
                                        
                                        # Rysowanie track map
                                        track_fig = plot_track_map(car_data, metric=metric_choice, driver_name=selected_driver, lap_number=selected_lap)
                                        
                                        if track_fig is None:
                                            # Fallback: użyj visualization bez track position (X,Y)
                                            print(f"[APP] Track map failed, trying fallback visualization...")
                                            st.info("📈 Wyświetlam profil telemetrii (Track position data niedostępne)")
                                            track_fig = plot_telemetry_vs_distance(car_data, metric=metric_choice, driver_name=selected_driver, lap_number=selected_lap)
                                        
                                        if track_fig is not None:
                                            st.plotly_chart(track_fig, use_container_width=True, config={"displayModeBar": False})
                                        else:
                                            st.error("Nie udało się wygenerować żadnej wizualizacji telemetrii.")
                                        
                                        # Statystyki
                                        if "Speed" in car_data.columns:
                                            col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
                                            
                                            with col_stat1:
                                                max_speed = car_data["Speed"].max()
                                                avg_speed = car_data["Speed"].mean()
                                                st.metric("Max speed", f"{max_speed:.1f} km/h")
                                            
                                            with col_stat2:
                                                st.metric("Avg speed", f"{avg_speed:.1f} km/h")
                                            
                                            with col_stat3:
                                                if "Throttle" in car_data.columns:
                                                    avg_throttle = car_data["Throttle"].mean()
                                                    st.metric("Avg throttle", f"{avg_throttle:.0f}%")
                                                else:
                                                    st.metric("Throttle", "N/A")
                                            
                                            with col_stat4:
                                                if "Brake" in car_data.columns:
                                                    avg_brake = car_data["Brake"].mean()
                                                    st.metric("Avg brake", f"{avg_brake:.0f}%")
                                                else:
                                                    st.metric("Brake", "N/A")
                                        
                                        # Lap time
                                        if "LapTime" in selected_lap_obj.index:
                                            try:
                                                lap_time = selected_lap_obj["LapTime"]
                                                st.markdown(f"**Lap Time:** `{lap_time}`")
                                            except:
                                                pass
                                        
                                        # ULEPSZENIE 1: Sector Analysis
                                        st.markdown("---")
                                        st.markdown("### 📊 Sector Analysis")
                                        sector_fig = plot_sector_analysis(selected_lap_obj, driver_name=selected_driver, lap_number=selected_lap)
                                        if sector_fig is not None:
                                            st.plotly_chart(sector_fig, use_container_width=True, config={"displayModeBar": False})
                                        
                                        # ULEPSZENIE 2: Lap Comparison
                                        st.markdown("---")
                                        st.markdown("### 🏁 Lap Comparison")
                                        
                                        col_compare1, col_compare2 = st.columns(2)
                                        with col_compare1:
                                            st.write("**Porównaj z:**")
                                            compare_lap = st.selectbox(
                                                "Wybierz okrążenie do porównania",
                                                options=[l for l in all_lap_numbers if l != selected_lap],
                                                key="compare_lap"
                                            )
                                        
                                        if compare_lap:
                                            with st.spinner(f"Ładuję dane porównawcze dla okrążenia {compare_lap}..."):
                                                compare_lap_obj = driver_laps[driver_laps["LapNumber"] == compare_lap]
                                                if not compare_lap_obj.empty:
                                                    compare_lap_obj = compare_lap_obj.iloc[0]
                                                    compare_car_data = get_car_data_from_lap(compare_lap_obj)
                                                    
                                                    if compare_car_data is not None and len(compare_car_data) > 0:
                                                        # Porównanie speed profile
                                                        comparison_fig = plot_comparison_lap_time(
                                                            car_data, 
                                                            compare_car_data,
                                                            driver_name=selected_driver,
                                                            lap1_num=selected_lap,
                                                            lap2_num=compare_lap
                                                        )
                                                        if comparison_fig is not None:
                                                            st.plotly_chart(comparison_fig, use_container_width=True, config={"displayModeBar": False})
                                                        
                                                        # Mini delta summary
                                                        col_delta1, col_delta2, col_delta3 = st.columns(3)
                                                        with col_delta1:
                                                            if "Speed" in car_data.columns and "Speed" in compare_car_data.columns:
                                                                delta_speed = (car_data["Speed"].mean() - compare_car_data["Speed"].mean())
                                                                delta_color = "🟢" if delta_speed > 0 else "🔴" if delta_speed < 0 else "⚪"
                                                                st.metric(f"Avg Speed Delta {delta_color}", f"{delta_speed:+.1f} km/h")
                                                        
                                                        with col_delta2:
                                                            if "Throttle" in car_data.columns and "Throttle" in compare_car_data.columns:
                                                                delta_throttle = car_data["Throttle"].mean() - compare_car_data["Throttle"].mean()
                                                                st.metric("Avg Throttle Delta", f"{delta_throttle:+.0f}%")
                                                        
                                                        with col_delta3:
                                                            if "Brake" in car_data.columns and "Brake" in compare_car_data.columns:
                                                                delta_brake = car_data["Brake"].mean() - compare_car_data["Brake"].mean()
                                                                st.metric("Avg Brake Delta", f"{delta_brake:+.0f}%")
                                    else:
                                        # Fallback - szukaj pierwszego lapa z dostępnymi danymi
                                        st.warning(f"Okrążenie {selected_lap} nie ma danych telemetrycznych. Szukam alternatywy...")
                                        
                                        found_data = False
                                        for lap_num in reversed(all_lap_numbers):
                                            if lap_num == selected_lap:
                                                continue
                                            try:
                                                temp_lap = driver_laps[driver_laps["LapNumber"] == lap_num]
                                                if not temp_lap.empty:
                                                    temp_lap = temp_lap.iloc[0]
                                                    temp_data = get_car_data_from_lap(temp_lap)
                                                    if temp_data is not None and len(temp_data) > 0:
                                                        st.info(f"✅ Wyświetlam okrążenie #{lap_num} (ma dostępne dane)")
                                                        car_data = temp_data
                                                        selected_lap = lap_num
                                                        found_data = True
                                                        break
                                            except:
                                                continue
                                        
                                        if found_data and car_data is not None:
                                            # Rysowanie track map
                                            track_fig = plot_track_map(car_data, metric=metric_choice, driver_name=selected_driver, lap_number=selected_lap)
                                            
                                            if track_fig is not None:
                                                st.plotly_chart(track_fig, use_container_width=True, config={"displayModeBar": False})
                                            else:
                                                st.error("Nie udało się wygenerować mapy toru.")
                                            
                                            # Statystyki
                                            if "Speed" in car_data.columns:
                                                col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
                                                
                                                with col_stat1:
                                                    max_speed = car_data["Speed"].max()
                                                    avg_speed = car_data["Speed"].mean()
                                                    st.metric("Max speed", f"{max_speed:.1f} km/h")
                                                
                                                with col_stat2:
                                                    st.metric("Avg speed", f"{avg_speed:.1f} km/h")
                                                
                                                with col_stat3:
                                                    if "Throttle" in car_data.columns:
                                                        avg_throttle = car_data["Throttle"].mean()
                                                        st.metric("Avg throttle", f"{avg_throttle:.0f}%")
                                                    else:
                                                        st.metric("Throttle", "N/A")
                                                
                                                with col_stat4:
                                                    if "Brake" in car_data.columns:
                                                        avg_brake = car_data["Brake"].mean()
                                                        st.metric("Avg brake", f"{avg_brake:.0f}%")
                                                    else:
                                                        st.metric("Brake", "N/A")
                                        else:
                                            st.error(f"❌ Brak danych telemetrycznych dla żadnego okrążenia kierowcy {selected_driver}")
                                else:
                                    st.error(f"Okrążenie {selected_lap} nie zostało znalezione.")
                        else:
                            st.error(f"Brak okrążeń dla kierowcy {selected_driver}")
                else:
                    st.info("Wybierz kierowcę aby wyświetlić telemetrię.")
            
            except Exception as e:
                st.error(f"Błąd w zakładce Telemetria Toru: {str(e)}")
                import traceback
                st.write(traceback.format_exc())

    except Exception as e:
        st.error(f"Wystąpił błąd przy ładowaniu danych: {e}")

else:
    st.info("Wybierz sezon i runde po lewej stronie, a nastepnie kliknij 'Zaladuj dashboard'.")
