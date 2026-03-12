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
    get_team_color,
    get_status_color,
    build_position_delta,
    get_quick_stats,
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
        padding-top: 1.8rem;
        padding-bottom: 2.2rem;
        max-width: 1320px;
    }

    .hero-card {
        background:
            radial-gradient(circle at top right, rgba(37, 99, 235, 0.22), transparent 30%),
            linear-gradient(135deg, #111827 0%, #0b1220 55%, #0f1b3d 100%);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 28px;
        padding: 28px 30px 22px 30px;
        margin-bottom: 22px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.22);
    }

    .hero-topline {
        display: flex;
        align-items: center;
        gap: 10px;
        flex-wrap: wrap;
        margin-bottom: 14px;
    }

    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.10);
        color: #E5E7EB;
        border-radius: 999px;
        padding: 7px 12px;
        font-size: 0.85rem;
        font-weight: 700;
    }

    .hero-title {
        font-size: 2.35rem;
        font-weight: 800;
        line-height: 1.1;
        margin-bottom: 8px;
        color: #F9FAFB;
    }

    .hero-subtitle {
        color: #9CA3AF;
        font-size: 1rem;
        margin: 0;
    }

    .quick-stats {
        margin-top: 20px;
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 12px;
    }

    .quick-stat-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 18px;
        padding: 14px 16px;
        backdrop-filter: blur(6px);
    }

    .quick-stat-label {
        color: #9CA3AF;
        font-size: 0.82rem;
        margin-bottom: 6px;
    }

    .quick-stat-value {
        color: #F9FAFB;
        font-size: 1.25rem;
        font-weight: 800;
        line-height: 1.1;
    }

    .metric-card {
        background: linear-gradient(180deg, rgba(17,24,39,0.96) 0%, rgba(11,18,32,0.98) 100%);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 20px;
        padding: 18px 20px;
        min-height: 120px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.12);
    }

    .metric-label {
        font-size: 0.88rem;
        color: #9CA3AF;
        margin-bottom: 10px;
    }

    .metric-value {
        font-size: 1.35rem;
        font-weight: 800;
        line-height: 1.2;
        color: #F9FAFB;
    }

    .metric-subvalue {
        font-size: 0.95rem;
        color: #D1D5DB;
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
        font-size: 1.12rem;
        font-weight: 800;
        margin-bottom: 14px;
        color: #F9FAFB;
    }

    .ranking-list {
        display: flex;
        flex-direction: column;
        gap: 12px;
    }

    .ranking-card {
        background: linear-gradient(180deg, rgba(11,18,32,0.96) 0%, rgba(9,14,26,1) 100%);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 18px;
        padding: 14px 16px;
        transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
        box-shadow: 0 6px 18px rgba(0,0,0,0.10);
    }

    .ranking-card:hover {
        transform: translateY(-1px);
        border-color: rgba(255,255,255,0.14);
        box-shadow: 0 10px 24px rgba(0,0,0,0.18);
    }

    .ranking-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 14px;
    }

    .ranking-left {
        display: flex;
        align-items: center;
        gap: 14px;
        min-width: 0;
    }

    .ranking-pos {
        width: 36px;
        height: 36px;
        border-radius: 999px;
        background: #111827;
        border: 1px solid rgba(255,255,255,0.08);
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        color: #E5E7EB;
        flex-shrink: 0;
    }

    .ranking-driver-block {
        min-width: 0;
    }

    .ranking-driver {
        font-weight: 800;
        font-size: 0.98rem;
        color: #F9FAFB;
        line-height: 1.2;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .ranking-team {
        font-size: 0.86rem;
        color: #9CA3AF;
        margin-top: 4px;
    }

    .team-dot {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 999px;
        margin-right: 8px;
        vertical-align: middle;
        box-shadow: 0 0 10px rgba(255,255,255,0.08);
    }

    .pill {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border-radius: 999px;
        padding: 6px 10px;
        font-size: 0.82rem;
        font-weight: 800;
        border: 1px solid rgba(255,255,255,0.08);
        white-space: nowrap;
    }

    .pill-green {
        background: rgba(22,163,74,0.15);
        color: #4ADE80;
    }

    .pill-red {
        background: rgba(220,38,38,0.15);
        color: #F87171;
    }

    .pill-gray {
        background: rgba(107,114,128,0.18);
        color: #D1D5DB;
    }

    .pill-status {
        padding: 6px 10px;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 800;
        color: white;
        white-space: nowrap;
        border: 1px solid rgba(255,255,255,0.08);
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 18px;
        overflow: hidden;
        box-shadow: 0 8px 24px rgba(0,0,0,0.10);
    }

    div[data-baseweb="tab-list"] {
        gap: 25px;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e1f2a 0%, #202332 100%);
        border-right: 1px solid rgba(255,255,255,0.06);
    }

    section[data-testid="stSidebar"] .block-container {
        padding-top: 1.5rem;
    }

    @media (max-width: 900px) {
        .quick-stats {
            grid-template-columns: 1fr;
        }

        .hero-title {
            font-size: 1.8rem;
        }

        .ranking-row {
            flex-direction: column;
            align-items: flex-start;
        }
    }
</style>
""", unsafe_allow_html=True)


def render_results_cards(df, title, mode="quali"):
    if df.empty:
        st.info("Brak danych do wyświetlenia.")
        return

    html = f'<div class="section-title">{title}</div><div class="ranking-list">'

    for i, (_, row) in enumerate(df.iterrows(), start=1):
        driver = row.get("Driver", "Unknown")
        team = row.get("Team", "Unknown")
        team_color = get_team_color(team)

        if mode == "quali":
            right_value = row.get("Q3") or row.get("Q2") or row.get("Q1") or "—"
            right_html = f'<div class="pill pill-gray">{right_value}</div>'
        else:
            status = row.get("Status", "Unknown")
            points = row.get("Points", "—")
            status_color = get_status_color(status)
            right_html = (
                f'<div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap;">'
                f'<div class="pill pill-gray">{points} pts</div>'
                f'<div class="pill-status" style="background:{status_color};">{status}</div>'
                f'</div>'
            )

        html += (
            f'<div class="ranking-card">'
            f'<div class="ranking-row">'
            f'<div class="ranking-left">'
            f'<div class="ranking-pos">{i}</div>'
            f'<div class="ranking-driver-block">'
            f'<div class="ranking-driver">{driver}</div>'
            f'<div class="ranking-team"><span class="team-dot" style="background:{team_color};"></span>{team}</div>'
            f'</div>'
            f'</div>'
            f'<div>{right_html}</div>'
            f'</div>'
            f'</div>'
        )

    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def render_position_change_cards(df, title):
    if df.empty:
        st.info("Brak danych do wyświetlenia.")
        return

    html = f'<div class="section-title">{title}</div><div class="ranking-list">'

    for i, (_, row) in enumerate(df.iterrows(), start=1):
        driver = row.get("Driver", "Unknown")
        team = row.get("Team", "Unknown")
        team_color = get_team_color(team)
        delta = row.get("PositionsChanged", 0)

        try:
            delta_int = int(delta)
        except Exception:
            delta_int = 0

        pill_class = "pill-green" if delta_int >= 0 else "pill-red"
        delta_text = f"{delta_int:+d}"
        move_text = build_position_delta(row.get("Started"), row.get("Finished"))

        html += (
            f'<div class="ranking-card">'
            f'<div class="ranking-row">'
            f'<div class="ranking-left">'
            f'<div class="ranking-pos">{i}</div>'
            f'<div class="ranking-driver-block">'
            f'<div class="ranking-driver">{driver}</div>'
            f'<div class="ranking-team"><span class="team-dot" style="background:{team_color};"></span>{team}</div>'
            f'</div>'
            f'</div>'
            f'<div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap;">'
            f'<div class="pill pill-gray">{move_text}</div>'
            f'<div class="pill {pill_class}">{delta_text}</div>'
            f'</div>'
            f'</div>'
            f'</div>'
        )

    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


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
        quick_stats = get_quick_stats(race_results, stint_data)

        st.markdown(
            f"""
<div class="hero-card">
    <div class="hero-topline">
        <span class="hero-badge">🏁 Round {round_number}</span>
        <span class="hero-badge">📍 {event_name}</span>
        <span class="hero-badge">📅 {season}</span>
    </div>
    <div class="hero-title">{event_name} Dashboard</div>
    <p class="hero-subtitle">
        Weekend overview: qualifying, race result, position changes and tyre strategies.
    </p>
    <div class="quick-stats">
        <div class="quick-stat-card">
            <div class="quick-stat-label">Drivers</div>
            <div class="quick-stat-value">{quick_stats['drivers_count']}</div>
        </div>
        <div class="quick-stat-card">
            <div class="quick-stat-label">Stints</div>
            <div class="quick-stat-value">{quick_stats['stints_count']}</div>
        </div>
        <div class="quick-stat-card">
            <div class="quick-stat-label">Classified finishers</div>
            <div class="quick-stat-value">{quick_stats['classified_finishers']}</div>
        </div>
    </div>
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

            st.markdown("""
            <div style="display:flex; gap:10px; flex-wrap:wrap; margin-bottom:14px;">
                <span style="background:#FF4D4D; color:#111; padding:6px 10px; border-radius:999px; font-weight:700;">Soft</span>
                <span style="background:#FFD54A; color:#111; padding:6px 10px; border-radius:999px; font-weight:700;">Medium</span>
                <span style="background:#F5F5F5; color:#111; padding:6px 10px; border-radius:999px; font-weight:700;">Hard</span>
                <span style="background:#43A047; color:white; padding:6px 10px; border-radius:999px; font-weight:700;">Intermediate</span>
                <span style="background:#1E88E5; color:white; padding:6px 10px; border-radius:999px; font-weight:700;">Wet</span>
            </div>
            """, unsafe_allow_html=True)

            fig = plot_stints(stint_data)

            if fig is not None:
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("Brak danych stintów do wyświetlenia.")

    except Exception as e:
        st.error(f"Wystąpił błąd przy ładowaniu danych: {e}")
else:
    st.info("Wybierz sezon i rundę po lewej stronie, a następnie kliknij „Załaduj dashboard”.")