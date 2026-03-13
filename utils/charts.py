import plotly.graph_objects as go
import plotly.express as px
from utils.config import TYRE_COLORS, TEAM_COLORS


def plot_stints(stints):
    if stints.empty:
        return None

    compound_colors = TYRE_COLORS

    drivers = list(stints["Driver"].drop_duplicates())
    fig = go.Figure()

    for driver in drivers:
        driver_stints = stints[stints["Driver"] == driver]
        cumulative_start = 0

        for _, row in driver_stints.iterrows():
            compound = str(row["Compound"]).upper()
            length = row["StintLength"]
            color = compound_colors.get(compound, "#9CA3AF")

            fig.add_trace(
                go.Bar(
                    x=[length],
                    y=[driver],
                    orientation="h",
                    base=cumulative_start,
                    marker=dict(
                        color=color,
                        line=dict(color="rgba(255,255,255,0.15)", width=1)
                    ),
                    name=compound,
                    hovertemplate=(
                        f"<b>{driver}</b><br>"
                        f"Compound: {compound}<br>"
                        f"Stint: {int(row['Stint'])}<br>"
                        f"Laps: {int(length)}<extra></extra>"
                    ),
                    showlegend=False,
                )
            )

            cumulative_start += length

    fig.update_layout(
        barmode="stack",
        height=max(500, len(drivers) * 28),
        margin=dict(l=10, r=10, t=20, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#0b1220",
        font=dict(color="#E5E7EB"),
        xaxis=dict(
            title="Lap",
            gridcolor="rgba(255,255,255,0.08)",
            zeroline=False,
        ),
        yaxis=dict(
            title="Driver",
            autorange="reversed",
            gridcolor="rgba(255,255,255,0.04)",
        ),
    )

    return fig

def plot_tyre_degradation(df):
    if df is None or df.empty:
        return None

    driver_color_map = {}
    if "Driver" in df.columns and "Team" in df.columns:
        unique_driver_teams = df[["Driver", "Team"]].dropna().drop_duplicates()
        for _, row in unique_driver_teams.iterrows():
            driver_color_map[row["Driver"]] = TEAM_COLORS.get(row["Team"], "#9CA3AF")

    fig = px.line(
        df,
        x="LapInStint",
        y="LapTimeSeconds",
        color="Driver",
        line_dash="Stint",
        markers=True,
        hover_data=["Driver", "Team", "Compound", "Stint", "LapNumber", "TyreLife"],
        color_discrete_map=driver_color_map if driver_color_map else None,
    )

    seen_drivers = set()
    for trace in fig.data:
        driver_name = str(trace.name).split(",")[0].strip()
        trace.name = driver_name
        trace.legendgroup = driver_name

        if driver_name in seen_drivers:
            trace.showlegend = False
        else:
            trace.showlegend = True
            seen_drivers.add(driver_name)

    fig.update_layout(
        height=520,
        margin=dict(l=10, r=10, t=20, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#0b1220",
        font=dict(color="#E5E7EB"),
        xaxis=dict(
            title="Lap in stint",
            gridcolor="rgba(255,255,255,0.08)",
            zeroline=False,
        ),
        yaxis=dict(
            title="Lap time (s)",
            gridcolor="rgba(255,255,255,0.08)",
            zeroline=False,
        ),
        legend_title="Driver",
    )

    return fig
    if df is None or df.empty:
        return None

    # mapa kierowca -> kolor teamu
    driver_color_map = {}
    if "Driver" in df.columns and "Team" in df.columns:
        unique_driver_teams = df[["Driver", "Team"]].dropna().drop_duplicates()
        for _, row in unique_driver_teams.iterrows():
            team = row["Team"]
            driver = row["Driver"]
            driver_color_map[driver] = team and __import__("utils.config", fromlist=["TEAM_COLORS"]).TEAM_COLORS.get(team, "#9CA3AF")

    fig = px.line(
        df,
        x="LapInStint",
        y="LapTimeSeconds",
        color="Driver",
        line_dash="Stint",
        markers=True,
        hover_data=["Driver", "Team", "Compound", "Stint", "LapNumber", "TyreLife"],
        color_discrete_map=driver_color_map if driver_color_map else None,
    )

    # poprawa legendy: usuń ", 1.0" itd.
    seen_drivers = set()
    for trace in fig.data:
        driver_name = str(trace.name).split(",")[0].strip()
        trace.name = driver_name
        trace.legendgroup = driver_name

        # pokaż legendę tylko raz na kierowcę
        if driver_name in seen_drivers:
            trace.showlegend = False
        else:
            trace.showlegend = True
            seen_drivers.add(driver_name)

    fig.update_layout(
        height=520,
        margin=dict(l=10, r=10, t=20, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#0b1220",
        font=dict(color="#E5E7EB"),
        xaxis=dict(
            title="Lap in stint",
            gridcolor="rgba(255,255,255,0.08)",
            zeroline=False,
        ),
        yaxis=dict(
            title="Lap time (s)",
            gridcolor="rgba(255,255,255,0.08)",
            zeroline=False,
        ),
        legend_title="Driver",
    )

    return fig