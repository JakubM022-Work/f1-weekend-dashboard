"""Komponenty UI - funkcje do renderowania dashboard'u"""

import streamlit as st
from utils.analysis import get_team_color, get_status_color, build_position_delta


def render_results_cards(df, title, mode="quali"):
    """Renderuj karty wyników kwalifikacji lub wyścigu"""
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
    """Renderuj karty zmian pozycji"""
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


def render_hero_card(active_round_number, active_event_name, active_season, quick_stats):
    """Renderuj główną kartę heroiczną z roundem i statystykami"""
    html = f"""
<div class="hero-card">
    <div class="hero-topline">
        <span class="hero-badge">🏁 Round {active_round_number}</span>
        <span class="hero-badge">📍 {active_event_name}</span>
        <span class="hero-badge">📅 {active_season}</span>
    </div>
    <div class="hero-title">{active_event_name} Dashboard</div>
    <p class="hero-subtitle">
        Weekend overview: qualifying, race result, position changes and tyre strategies.
    </p>
    <div class="quick-stats">
        <div class="quick-stat-card">
            <div class="quick-stat-label">Net positions gained</div>
            <div class="quick-stat-value">{quick_stats['net_positions_gained']}</div>
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
    """
    st.markdown(html, unsafe_allow_html=True)


def render_metric_card(label: str, value: str, subvalue: str = ""):
    """Renderuj kartę metryki w sidebaru"""
    subvalue_html = f'<div class="metric-subvalue">{subvalue}</div>' if subvalue else ""
    html = f"""
<div class="metric-card">
    <div class="metric-label">{label}</div>
    <div class="metric-value">{value}</div>
    {subvalue_html}
</div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_tyre_compounds_legend():
    """Renderuj legendę opon"""
    st.markdown("""
    <div style="display:flex; gap:10px; flex-wrap:wrap; margin-bottom:14px;">
        <span style="background:#FF4D4D; color:#111; padding:6px 10px; border-radius:999px; font-weight:700;">Soft</span>
        <span style="background:#FFD54A; color:#111; padding:6px 10px; border-radius:999px; font-weight:700;">Medium</span>
        <span style="background:#F5F5F5; color:#111; padding:6px 10px; border-radius:999px; font-weight:700;">Hard</span>
        <span style="background:#43A047; color:white; padding:6px 10px; border-radius:999px; font-weight:700;">Intermediate</span>
        <span style="background:#1E88E5; color:white; padding:6px 10px; border-radius:999px; font-weight:700;">Wet</span>
    </div>
    """, unsafe_allow_html=True)

def render_small_stat_card(label: str, value: str, subtitle: str = ""):

    st.markdown(
        f"""
        <div class="small-stat-card">
            <div class="small-stat-label">{label}</div>
            <div class="small-stat-value">{value}</div>
            <div class="small-stat-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_degradation_summary_cards(summary_df, format_seconds_to_laptime):

    if summary_df is None or summary_df.empty:
        st.info("Brak danych do wyświetlenia.")
        return

    html = '<div class="section-title">Podsumowanie stintów</div><div class="ranking-list">'

    for _, row in summary_df.iterrows():
        driver = row.get("Driver", "Unknown")
        compound = row.get("Compound", "Unknown")
        stint = int(row.get("Stint", 0))
        laps = int(row.get("Laps", 0))
        avg_pace = format_seconds_to_laptime(row.get("AvgPaceSeconds"))
        first_lap = format_seconds_to_laptime(row.get("FirstLapSeconds"))
        last_lap = format_seconds_to_laptime(row.get("LastLapSeconds"))
        deg_per_lap = row.get("DegPerLapSeconds", 0)

        html += (
            f'<div class="ranking-card">'
            f'<div class="ranking-row">'
            f'<div class="ranking-left">'
            f'<div class="ranking-driver-block">'
            f'<div class="ranking-driver">{driver} • {compound} • Stint {stint}</div>'
            f'<div class="ranking-team">{laps} laps</div>'
            f'</div>'
            f'</div>'
            f'<div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap;">'
            f'<div class="pill pill-gray">Avg {avg_pace}</div>'
            f'<div class="pill pill-gray">First {first_lap}</div>'
            f'<div class="pill pill-gray">Last {last_lap}</div>'
            f'<div class="pill {"pill-green" if deg_per_lap <= 0 else "pill-red"}">{deg_per_lap:.3f}s/lap</div>'
            f'</div>'
            f'</div>'
            f'</div>'
        )

    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)
