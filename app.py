import os
import pandas as pd
import streamlit as st
import fastf1

from utils.loaders import get_event_schedule, load_session_results, load_race_laps
from utils.analysis import (
    prepare_qualifying_top22,
    prepare_race_top22,
    calculate_position_changes,
    prepare_stint_data,
    get_pole_sitter,
    get_race_winner,
    get_biggest_gainer_and_loser,
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
st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1300px;
    }

    .hero-card {
        background: linear-gradient(135deg, #111827 0%, #0f172a 100%);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 24px;
        padding: 28px;
        margin-bottom: 20px;
    }

    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }

    .hero-subtitle {
        color: #9ca3af;
        font-size: 1rem;
        margin-bottom: 0;
    }

    .metric-card {
        background: #111827;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 20px;
        padding: 18px 20px;
        min-height: 120px;
    }

    .metric-label {
        font-size: 0.9rem;
        color: #9ca3af;
        margin-bottom: 10px;
    }

    .metric-value {
        font-size: 1.35rem;
        font-weight: 700;
        line-height: 1.2;
    }

    .metric-subvalue {
        font-size: 0.95rem;
        color: #d1d5db;
        margin-top: 8px;
    }

    .section-card {
        background: #0f172a;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 24px;
        padding: 20px;
        margin-top: 12px;
    }

    .section-title {
        font-size: 1.2rem;
        font-weight: 700;
        margin-bottom: 14px;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 18px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

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

        quali_top22 = prepare_qualifying_top22(quali_results)
        race_top22 = prepare_race_top22(race_results)
        changes = calculate_position_changes(race_results)
        stint_data = prepare_stint_data(race_laps)

        pole_sitter = get_pole_sitter(quali_results)
        race_winner = get_race_winner(race_results)
        biggest_gainer, biggest_loser = get_biggest_gainer_and_loser(changes)

        st.markdown(
            f"""
            <div class="hero-card">
                <div class="hero-title">🏁 {event_name} ({season})</div>
                <p class="hero-subtitle">
                    Weekend dashboard: kwalifikacje, wyścig, zmiany pozycji i stinty opon.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Pole position</div>
                    <div class="metric-value">{pole_sitter['driver'] if pole_sitter else '—'}</div>
                    <div class="metric-subvalue">{pole_sitter['team'] if pole_sitter else ''}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with c2:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Winner</div>
                    <div class="metric-value">{race_winner['driver'] if race_winner else '—'}</div>
                    <div class="metric-subvalue">{race_winner['team'] if race_winner else ''}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with c3:
            gainer_name = biggest_gainer["Driver"] if biggest_gainer else "—"
            gainer_value = f"+{int(biggest_gainer['PositionsChanged'])}" if biggest_gainer else ""

            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Biggest gainer</div>
                    <div class="metric-value">{gainer_name}</div>
                    <div class="metric-subvalue">{gainer_value}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with c4:
            loser_name = biggest_loser["Driver"] if biggest_loser else "—"
            loser_value = str(int(biggest_loser["PositionsChanged"])) if biggest_loser else ""

            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Biggest loser</div>
                    <div class="metric-value">{loser_name}</div>
                    <div class="metric-subvalue">{loser_value}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        tab1, tab2, tab3, tab4 = st.tabs(["Podsumowanie", "Kwalifikacje", "Wyścig", "Stinty"])

        with tab1:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown('<div class="section-title">Top 22 kwalifikacji</div>', unsafe_allow_html=True)
                if not quali_top22.empty:
                    st.dataframe(quali_top22, use_container_width=True, hide_index=True)
                else:
                    st.info("Brak danych kwalifikacji do wyświetlenia.")

            with col2:
                st.markdown('<div class="section-title">Top 22 wyścigu</div>', unsafe_allow_html=True)
                if not race_top22.empty:
                    st.dataframe(race_top22, use_container_width=True, hide_index=True)
                else:
                    st.info("Brak danych wyścigu do wyświetlenia.")

            col3, col4 = st.columns(2)

            with col3:
                st.markdown('<div class="section-title">Najwięcej zyskanych pozycji</div>', unsafe_allow_html=True)
                if not changes.empty:
                    st.dataframe(
                        changes.sort_values("PositionsChanged", ascending=False).head(5),
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("Brak danych.")

            with col4:
                st.markdown('<div class="section-title">Najwięcej straconych pozycji</div>', unsafe_allow_html=True)
                if not changes.empty:
                    st.dataframe(
                        changes.sort_values("PositionsChanged", ascending=True).head(5),
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("Brak danych.")

        with tab2:
            st.markdown('<div class="section-title">Wyniki kwalifikacji</div>', unsafe_allow_html=True)
            if not quali_top22.empty:
                st.dataframe(quali_top22, use_container_width=True, hide_index=True)
            else:
                st.info("Brak danych kwalifikacji do wyświetlenia.")

        with tab3:
            st.markdown('<div class="section-title">Wyniki wyścigu</div>', unsafe_allow_html=True)
            if not race_top22.empty:
                st.dataframe(race_top22, use_container_width=True, hide_index=True)
            else:
                st.info("Brak danych wyścigu do wyświetlenia.")

            st.markdown('<div class="section-title">Zmiany pozycji</div>', unsafe_allow_html=True)
            if not changes.empty:
                st.dataframe(changes, use_container_width=True, hide_index=True)
            else:
                st.info("Nie udało się obliczyć zmian pozycji.")

        with tab4:
            st.markdown('<div class="section-title">Strategie opon</div>', unsafe_allow_html=True)
            st.caption("Każdy pasek pokazuje długość kolejnych stintów kierowcy podczas wyścigu.")

            fig = plot_stints(stint_data)

            if fig is not None:
                st.pyplot(fig, use_container_width=True)
            else:
                st.info("Brak danych stintów do wyświetlenia.")

    except Exception as e:
        st.error(f"Wystąpił błąd przy ładowaniu danych: {e}")
else:
    st.info("Wybierz sezon i rundę po lewej stronie, a następnie kliknij „Załaduj dashboard”.")