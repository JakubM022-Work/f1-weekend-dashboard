import plotly.graph_objects as go


def plot_stints(stints):
    if stints.empty:
        return None

    compound_colors = {
        "SOFT": "#FF4D4D",
        "MEDIUM": "#FFD54A",
        "HARD": "#F5F5F5",
        "INTERMEDIATE": "#43A047",
        "WET": "#1E88E5",
        "UNKNOWN": "#9CA3AF",
    }

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