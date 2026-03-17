"""
Fallback visualization jeśli track position (X,Y) nie jest dostępna
"""

import plotly.graph_objects as go
import plotly.express as px

def plot_telemetry_vs_distance(car_data, metric="Speed", driver_name="Driver", lap_number=0):
    """
    Rysuje metric vs distance traveled
    Przydatne gdy X,Y nie są dostępne
    """
    if car_data is None or len(car_data) == 0:
        return None
    
    # Jeśli nie ma metric, use Speed
    if metric not in car_data.columns:
        metric = "Speed" if "Speed" in car_data.columns else None
    
    if metric is None:
        return None
    
    # Calculate cumulative distance (przybliżenie na podstawie Speed)
    car_data_clean = car_data.copy()
    
    # Sort by Time jeśli istnieje
    if "Time" in car_data_clean.columns:
        car_data_clean = car_data_clean.sort_values("Time").reset_index(drop=True)
    
    # Estimate distance from speed (jeśli brak real distance)
    if "Distance" not in car_data_clean.columns and "Speed" in car_data_clean.columns:
        # Approximate: distance ≈ speed change over time
        # For now, just use index as distance proxy
        car_data_clean["Distance"] = range(len(car_data_clean))
    
    # Color scheme based on metric
    if metric == "Speed":
        colorscale = "RdYlGn"
        title_metric = "Speed (km/h)"
    elif metric == "Throttle":
        colorscale = "Viridis"
        title_metric = "Throttle (%)"
    elif metric == "Brake":
        colorscale = "Reds"
        title_metric = "Brake (%)"
    else:
        colorscale = "Viridis"
        title_metric = metric
    
    metric_values = car_data_clean[metric].astype(float).tolist()  # Konwersja do listy
    
    # Create figure
    fig = go.Figure()
    
    # Add trace with color gradient
    fig.add_trace(
        go.Scatter(
            x=car_data_clean["Distance"].tolist() if "Distance" in car_data_clean.columns else list(range(len(car_data_clean))),
            y=metric_values,
            mode="lines+markers",
            name=metric,
            line=dict(
                color="rgba(100,100,100,0.4)",  # Szara linia
                width=2,
            ),
            marker=dict(
                size=5, 
                color=metric_values,  # Kolorowanie markerów
                colorscale=colorscale,
                showscale=True,
                colorbar=dict(title=title_metric, thickness=15, len=0.7),
                line=dict(width=0.5, color="rgba(255,255,255,0.1)"),
                opacity=0.8,
            ),
            hovertemplate=(
                f"<b>{metric}</b><br>"
                "Distance: %{x:.0f}<br>"
                f"{metric}: %{{y:.1f}}<extra></extra>"
            ),
            fill="tozeroy",
        )
    )
    
    fig.update_layout(
        title=dict(
            text=f"<b>{driver_name}</b> - Lap {lap_number} {metric} Profile",
            font=dict(size=16),
        ),
        height=500,
        width=None,
        margin=dict(l=10, r=10, t=50, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#0b1220",
        font=dict(color="#E5E7EB"),
        xaxis=dict(
            title="Distance (data points)",
            gridcolor="rgba(255,255,255,0.08)",
            zeroline=False,
        ),
        yaxis=dict(
            title=title_metric,
            gridcolor="rgba(255,255,255,0.08)",
            zeroline=False,
        ),
        hovermode="x unified",
        showlegend=False,
    )
    
    return fig
