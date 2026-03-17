import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
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


def plot_track_map(car_data, metric="Speed", driver_name="Driver", lap_number=0):
    """
    Rysuje mapę toru z ścieżką kierowcy kolorowaną zależnie od metryki.
    
    Parameters:
    -----------
    car_data : DataFrame
        Car data z X, Y, Speed, Throttle, Brake, Gear
    metric : str
        Parametr kolorowania: "Speed", "Throttle", "Brake"
    driver_name : str
        Nazwa kierowcy do wyświetlenia w tytule
    lap_number : int
        Numer okrążenia do wyświetlenia
    
    Returns:
    --------
    fig : plotly.graph_objects.Figure lub None
    """
    if car_data is None or len(car_data) == 0:
        print(f"[PLOT] car_data is None or empty")
        return None
    
    print(f"[PLOT] plot_track_map called")
    print(f"[PLOT] car_data columns: {list(car_data.columns)}")
    print(f"[PLOT] metric: {metric}")
    
    # Konwersja do DataFrame jeśli jest to Series
    if hasattr(car_data, 'to_frame'):
        car_data = car_data.to_frame().T
    
    # Upewnienie się że mamy numeric data
    car_data_clean = car_data.copy()
    
    # Kolumny do sprawdzenia  
    required_cols = ["X", "Y"]
    print(f"[PLOT] Looking for columns: {required_cols}")
    print(f"[PLOT] Has X: {'X' in car_data_clean.columns}, Has Y: {'Y' in car_data_clean.columns}")
    
    if metric not in car_data_clean.columns:
        metric = "Speed" if "Speed" in car_data_clean.columns else None
        print(f"[PLOT] Adjusted metric to: {metric}")
    
    # Jeśli nie ma wymaganych kolumn
    if not all(col in car_data_clean.columns for col in required_cols):
        print(f"[PLOT] Missing required columns X or Y - returning None")
        print(f"[PLOT] Available columns: {list(car_data_clean.columns)}")
        return None
    
    # Czyszczenie danych - usuwanie NaN
    car_data_clean = car_data_clean.dropna(subset=["X", "Y"])
    if len(car_data_clean) < 2:
        return None
    
    fig = go.Figure()
    
    # Track outline (szara linia toru)
    fig.add_trace(
        go.Scatter(
            x=car_data_clean["X"],
            y=car_data_clean["Y"],
            mode="lines+markers",
            name="Track outline",
            line=dict(color="rgba(100, 100, 100, 0.3)", width=1),
            marker=dict(size=2),
            hoverinfo="skip",
            showlegend=False,
        )
    )
    
    # Ścieżka kierowcy z kolorowaniem
    if metric and metric in car_data_clean.columns:
        color_values = car_data_clean[metric].astype(float).tolist()  # Konwersja do listy
        
        # Colorscale zależy od metryki
        if metric == "Speed":
            colorscale = "RdYlGn"  # Red -> Yellow -> Green
            colorbar_title = "Speed (km/h)"
        elif metric == "Throttle":
            colorscale = "Viridis"
            colorbar_title = "Throttle (%)"
        elif metric == "Brake":
            colorscale = "Reds"
            colorbar_title = "Brake (%)"
        else:
            colorscale = "Viridis"
            colorbar_title = metric
        
        fig.add_trace(
            go.Scatter(
                x=car_data_clean["X"],
                y=car_data_clean["Y"],
                mode="lines+markers",
                name=metric,
                line=dict(
                    color="rgba(100, 100, 100, 0.5)",  # Szara linia
                    width=2,
                ),
                marker=dict(
                    size=5, 
                    color=color_values,  # Kolorowanie markerów na podstawie metryki
                    colorscale=colorscale, 
                    showscale=True,
                    colorbar=dict(
                        title=colorbar_title,
                        thickness=15,
                        len=0.7,
                    ),
                    line=dict(width=0.5, color="rgba(255,255,255,0.2)"),
                    opacity=0.8,
                ),
                hovertemplate=(
                    "<b>Track Position</b><br>"
                    f"X: %{{x:.1f}}<br>"
                    f"Y: %{{y:.1f}}<br>"
                    f"{metric}: " + ("%{marker.color:.1f}<extra></extra>" if metric in ["Speed"] else "%{marker.color:.0f}%<extra></extra>")
                ),
                showlegend=True,
            )
        )
    else:
        # Fallback jeśli nie ma metryki
        fig.add_trace(
            go.Scatter(
                x=car_data_clean["X"],
                y=car_data_clean["Y"],
                mode="lines+markers",
                name="Racing line",
                line=dict(color="#3B82F6", width=3),
                marker=dict(size=4),
                hovertemplate="X: %{x:.1f}<br>Y: %{y:.1f}<extra></extra>",
                showlegend=True,
            )
        )
    
    # Start/Meta punkt - ULEPSZONE
    start_point = car_data_clean.iloc[0]
    fig.add_trace(
        go.Scatter(
            x=[start_point["X"]],
            y=[start_point["Y"]],
            mode="markers+text",
            name="Start/Finish",
            marker=dict(
                size=25, 
                color="gold", 
                symbol="star",
                line=dict(color="white", width=3),
                opacity=1,
            ),
            text=["START<br>FINISH"],
            textposition="top center",
            textfont=dict(size=12, color="white", family="Arial Black"),
            hovertemplate="<b>Start/Finish Line</b><extra></extra>",
            showlegend=True,
        )
    )
    
    # Layout
    fig.update_layout(
        title=dict(
            text=f"<b>{driver_name}</b> - Lap {lap_number} Track Map ({metric})",
            font=dict(size=16),
        ),
        height=700,
        width=None,
        margin=dict(l=10, r=10, t=50, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#0b1220",
        font=dict(color="#E5E7EB"),
        xaxis=dict(
            title="X Position",
            gridcolor="rgba(255,255,255,0.08)",
            zeroline=False,
            showgrid=True,
        ),
        yaxis=dict(
            title="Y Position",
            gridcolor="rgba(255,255,255,0.08)",
            zeroline=False,
            showgrid=True,
            scaleanchor="x",
            scaleratio=1,  # Aspect ratio 1:1 dla realnego wyglądu toru
        ),
        hovermode="closest",
        showlegend=True,
        legend=dict(
            x=0.02,
            y=0.98,
            bgcolor="rgba(0,0,0,0.5)",
            bordercolor="white",
            borderwidth=1,
        ),
    )
    
    return fig


def plot_sector_analysis(lap_obj, driver_name="Driver", lap_number=0):
    """
    Rysuje analizę sektorów (S1, S2, S3) z deltami vs osobistego rekordu
    """
    if lap_obj is None:
        return None
    
    try:
        sectors_data = []
        
        # Pobierz czasy sektorów
        sector_times = []
        sector_names = []
        
        for i in range(1, 4):  # S1, S2, S3
            col_name = f"Sector{i}Time"
            if col_name in lap_obj.index:
                sector_time = lap_obj[col_name]
                if sector_time is not None and pd.notna(sector_time):
                    # Konwersja do sekund (Timedelta)
                    try:
                        time_seconds = sector_time.total_seconds()
                        sector_times.append(time_seconds)
                        sector_names.append(f"S{i}")
                    except:
                        pass
        
        if not sector_times:
            return None
        
        # Utworz figure
        fig = go.Figure()
        
        # Bar chart dla czasów sektorów
        colors = ["#FF6B6B", "#4ECDC4", "#45B7D1"]
        
        fig.add_trace(
            go.Bar(
                x=sector_names,
                y=sector_times,
                marker=dict(
                    color=colors[:len(sector_times)],
                    line=dict(color="white", width=1),
                    opacity=0.8,
                ),
                text=[f"{st:.2f}s" for st in sector_times],
                textposition="outside",
                textfont=dict(color="white", size=12),
                hovertemplate="<b>%{x}</b><br>Time: %{y:.2f}s<extra></extra>",
                showlegend=False,
            )
        )
        
        fig.update_layout(
            title=dict(
                text=f"<b>{driver_name}</b> - Lap {lap_number} Sector Times",
                font=dict(size=14),
            ),
            height=350,
            margin=dict(l=10, r=10, t=40, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="#0b1220",
            font=dict(color="#E5E7EB"),
            xaxis=dict(
                gridcolor="rgba(255,255,255,0.08)",
            ),
            yaxis=dict(
                title="Sector Time (s)",
                gridcolor="rgba(255,255,255,0.08)",
                zeroline=False,
            ),
        )
        
        return fig
    except Exception as e:
        print(f"[SECTOR] Error: {e}")
        return None


def plot_comparison_lap_time(lap1_car_data, lap2_car_data, driver_name="Driver", lap1_num=0, lap2_num=0):
    """
    Porównanie Speed profilu dwóch lapów
    """
    if lap1_car_data is None or lap2_car_data is None:
        return None
    
    if len(lap1_car_data) == 0 or len(lap2_car_data) == 0:
        return None
    
    try:
        # Resample do tego samego rozmiaru dla porównania
        lap1_clean = lap1_car_data.reset_index(drop=True)
        lap2_clean = lap2_car_data.reset_index(drop=True)
        
        # Normalizuj do wspólnej długości
        min_len = min(len(lap1_clean), len(lap2_clean))
        lap1_clean = lap1_clean.iloc[:min_len]
        lap2_clean = lap2_clean.iloc[:min_len]
        
        distance = list(range(min_len))
        
        fig = go.Figure()
        
        # Lap 1
        if "Speed" in lap1_clean.columns:
            fig.add_trace(
                go.Scatter(
                    x=distance,
                    y=lap1_clean["Speed"].tolist(),
                    mode="lines",
                    name=f"Lap #{int(lap1_num)}",
                    line=dict(color="#FF6B6B", width=3),
                    hovertemplate="<b>Lap #" + str(int(lap1_num)) + "</b><br>Speed: %{y:.1f} km/h<extra></extra>",
                )
            )
        
        # Lap 2
        if "Speed" in lap2_clean.columns:
            fig.add_trace(
                go.Scatter(
                    x=distance,
                    y=lap2_clean["Speed"].tolist(),
                    mode="lines",
                    name=f"Lap #{int(lap2_num)}",
                    line=dict(color="#4ECDC4", width=3, dash="dash"),
                    hovertemplate="<b>Lap #" + str(int(lap2_num)) + "</b><br>Speed: %{y:.1f} km/h<extra></extra>",
                )
            )
        
        # Delta
        if "Speed" in lap1_clean.columns and "Speed" in lap2_clean.columns:
            delta = (lap1_clean["Speed"] - lap2_clean["Speed"]).tolist()
            fig.add_trace(
                go.Scatter(
                    x=distance,
                    y=delta,
                    mode="lines",
                    name="Delta (L1-L2)",
                    line=dict(color="#FFA500", width=2, dash="dot"),
                    fill="tozeroy",
                    fillcolor="rgba(255,165,0,0.1)",
                    hovertemplate="Delta: %{y:+.1f} km/h<extra></extra>",
                )
            )
        
        fig.update_layout(
            title=dict(
                text=f"<b>{driver_name}</b> - Lap Comparison (Speed Profile)",
                font=dict(size=14),
            ),
            height=400,
            margin=dict(l=10, r=10, t=40, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="#0b1220",
            font=dict(color="#E5E7EB"),
            xaxis=dict(
                title="Distance (data points)",
                gridcolor="rgba(255,255,255,0.08)",
                zeroline=False,
            ),
            yaxis=dict(
                title="Speed (km/h)",
                gridcolor="rgba(255,255,255,0.08)",
                zeroline=False,
            ),
            hovermode="x unified",
            legend=dict(
                x=0.02,
                y=0.98,
                bgcolor="rgba(0,0,0,0.5)",
                bordercolor="white",
                borderwidth=1,
            ),
        )
        
        return fig
    except Exception as e:
        print(f"[COMPARISON] Error: {e}")
        return None