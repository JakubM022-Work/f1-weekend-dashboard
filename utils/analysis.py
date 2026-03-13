import pandas as pd
from utils.config import TEAM_COLORS


def format_timedelta(value):
    if value is None or pd.isna(value):
        return ""
    if isinstance(value, pd.Timedelta):
        total_ms = int(value.total_seconds() * 1000)
        minutes = total_ms // 60000
        seconds = (total_ms % 60000) // 1000
        milliseconds = total_ms % 1000
        return f"{minutes}:{seconds:02d}.{milliseconds:03d}"
    return str(value)


def prepare_qualifying_top22(quali_results: pd.DataFrame) -> pd.DataFrame:
    if quali_results.empty:
        return pd.DataFrame()

    df = quali_results.copy()

    if "Position" in df.columns:
        df["Position"] = pd.to_numeric(df["Position"], errors="coerce")
        df = df[df["Position"].notna()].copy()
        df = df.sort_values("Position").head(22)

    for col in ["Q1", "Q2", "Q3"]:
        if col in df.columns:
            df[col] = df[col].apply(format_timedelta)

    rename_map = {
        "Position": "Pos",
        "FullName": "Driver",
        "Abbreviation": "Code",
        "TeamName": "Team",
    }
    df = df.rename(columns=rename_map)

    preferred_order = [col for col in ["Pos", "Driver", "Code", "Team", "Q1", "Q2", "Q3"] if col in df.columns]
    return df[preferred_order].reset_index(drop=True)


def prepare_race_top22(race_results: pd.DataFrame) -> pd.DataFrame:
    if race_results.empty:
        return pd.DataFrame()

    df = race_results.copy()

    if "Position" in df.columns:
        df["Position"] = pd.to_numeric(df["Position"], errors="coerce")
        df = df[df["Position"].notna()].copy()
        df = df.sort_values("Position").head(22)

    if "GridPosition" in df.columns:
        df["GridPosition"] = pd.to_numeric(df["GridPosition"], errors="coerce")

    if "Points" in df.columns:
        df["Points"] = pd.to_numeric(df["Points"], errors="coerce")

    rename_map = {
        "Position": "Pos",
        "FullName": "Driver",
        "Abbreviation": "Code",
        "TeamName": "Team",
        "GridPosition": "Grid",
    }
    df = df.rename(columns=rename_map)

    preferred_order = [col for col in ["Pos", "Driver", "Code", "Team", "Grid", "Points", "Status"] if col in df.columns]
    return df[preferred_order].reset_index(drop=True)


def calculate_position_changes(race_results: pd.DataFrame) -> pd.DataFrame:
    if race_results.empty:
        return pd.DataFrame()

    df = race_results.copy()

    required_cols = {"Position", "GridPosition", "FullName", "Abbreviation", "TeamName"}
    missing = required_cols - set(df.columns)
    if missing:
        return pd.DataFrame()

    df["Position"] = pd.to_numeric(df["Position"], errors="coerce")
    df["GridPosition"] = pd.to_numeric(df["GridPosition"], errors="coerce")
    df = df[df["Position"].notna() & df["GridPosition"].notna()].copy()

    if df.empty:
        return pd.DataFrame()

    df["PositionsChanged"] = df["GridPosition"] - df["Position"]

    df = df.rename(
        columns={
            "FullName": "Driver",
            "Abbreviation": "Code",
            "TeamName": "Team",
            "GridPosition": "Started",
            "Position": "Finished",
        }
    )

    result = df[["Driver", "Code", "Team", "Started", "Finished", "PositionsChanged"]].copy()
    result = result.sort_values("PositionsChanged", ascending=False)

    return result.reset_index(drop=True)


def prepare_stint_data(laps: pd.DataFrame) -> pd.DataFrame:
    if laps.empty:
        return pd.DataFrame()

    cols_needed = ["Driver", "Stint", "Compound", "LapNumber"]
    existing = [c for c in cols_needed if c in laps.columns]

    if len(existing) < 4:
        return pd.DataFrame()

    df = laps[existing].copy()
    df = df[
        df["Driver"].notna()
        & df["Stint"].notna()
        & df["Compound"].notna()
        & df["LapNumber"].notna()
    ].copy()

    df["LapNumber"] = pd.to_numeric(df["LapNumber"], errors="coerce")
    df["Stint"] = pd.to_numeric(df["Stint"], errors="coerce")
    df = df[df["LapNumber"].notna() & df["Stint"].notna()].copy()

    if df.empty:
        return pd.DataFrame()

    stints = (
        df.groupby(["Driver", "Stint", "Compound"], as_index=False)
        .agg(
            StintLength=("LapNumber", "count"),
            FirstLap=("LapNumber", "min"),
        )
        .sort_values(["Driver", "Stint"])
    )

    return stints.reset_index(drop=True)

def get_pole_sitter(quali_results: pd.DataFrame):
    if quali_results.empty or "Position" not in quali_results.columns:
        return None

    df = quali_results.copy()
    df["Position"] = pd.to_numeric(df["Position"], errors="coerce")
    df = df[df["Position"] == 1]

    if df.empty:
        return None

    row = df.iloc[0]
    return {
        "driver": row.get("FullName", "Unknown"),
        "team": row.get("TeamName", "Unknown"),
    }


def get_race_winner(race_results: pd.DataFrame):
    if race_results.empty or "Position" not in race_results.columns:
        return None

    df = race_results.copy()
    df["Position"] = pd.to_numeric(df["Position"], errors="coerce")
    df = df[df["Position"] == 1]

    if df.empty:
        return None

    row = df.iloc[0]
    return {
        "driver": row.get("FullName", "Unknown"),
        "team": row.get("TeamName", "Unknown"),
        "points": row.get("Points", None),
    }


def get_biggest_gainer_and_loser(position_changes: pd.DataFrame):
    if position_changes.empty:
        return None, None

    sorted_df = position_changes.sort_values("PositionsChanged", ascending=False).reset_index(drop=True)
    gainer = sorted_df.iloc[0].to_dict()
    loser = sorted_df.iloc[-1].to_dict()

    return gainer, loser

def get_team_color(team_name: str) -> str:
    return TEAM_COLORS.get(team_name, "#6B7280")


def get_status_color(status: str) -> str:
    status = str(status).lower()

    if "finished" in status:
        return "#16A34A"
    if "lapped" in status:
        return "#F59E0B"
    if "retired" in status:
        return "#DC2626"
    if "did not start" in status:
        return "#6B7280"
    return "#374151"


def build_position_delta(started, finished):
    if pd.isna(started) or pd.isna(finished):
        return "—"

    try:
        return f"P{int(started)} → P{int(finished)}"
    except Exception:
        return "—"

def get_quick_stats(race_results: pd.DataFrame, stint_data: pd.DataFrame, changes: pd.DataFrame):
    net_positions_gained = 0
    stints_count = 0
    classified_finishers = 0

    if race_results is not None and not race_results.empty:
        if "Status" in race_results.columns:
            status_series = race_results["Status"].astype(str).str.lower()
            classified_finishers = status_series.str.contains("finished|lapped").sum()

    if stint_data is not None and not stint_data.empty:
        stints_count = len(stint_data)

    if changes is not None and not changes.empty and "PositionsChanged" in changes.columns:
        positive_changes = pd.to_numeric(changes["PositionsChanged"], errors="coerce")
        positive_changes = positive_changes[positive_changes > 0]
        net_positions_gained = int(positive_changes.sum()) if not positive_changes.empty else 0

    return {
        "net_positions_gained": int(net_positions_gained),
        "stints_count": int(stints_count),
        "classified_finishers": int(classified_finishers),
    }

def estimate_overtakes_from_laps(laps: pd.DataFrame) -> int:
    if laps is None or laps.empty:
        return 0

    needed_cols = {"Driver", "LapNumber", "Position"}
    if not needed_cols.issubset(laps.columns):
        return 0

    df = laps[list(needed_cols)].copy()
    df["LapNumber"] = pd.to_numeric(df["LapNumber"], errors="coerce")
    df["Position"] = pd.to_numeric(df["Position"], errors="coerce")
    df = df.dropna(subset=["Driver", "LapNumber", "Position"]).copy()

    if df.empty:
        return 0

    df = df.sort_values(["Driver", "LapNumber"])

    # zmiana pozycji kierowcy między okrążeniami
    df["PrevPosition"] = df.groupby("Driver")["Position"].shift(1)
    df["PosDelta"] = df["PrevPosition"] - df["Position"]

    # tylko awanse o min. 1 pozycję
    gains = df[df["PosDelta"] > 0]["PosDelta"].sum()

    if pd.isna(gains):
        return 0

    return int(gains)

def lap_time_to_seconds(value):
    if value is None or pd.isna(value):
        return None
    if isinstance(value, pd.Timedelta):
        return value.total_seconds()
    return None


def filter_laps_for_degradation(
    laps: pd.DataFrame,
    selected_drivers: list[str],
    selected_compound: str,
    min_stint_length: int = 5,
) -> pd.DataFrame:
    if laps is None or laps.empty:
        return pd.DataFrame()

    df = laps.copy()

    needed_cols = [
        "Driver", "LapNumber", "LapTime", "Compound", "TyreLife",
        "Stint", "IsAccurate", "TrackStatus", "PitInTime", "PitOutTime"
    ]
    existing_cols = [c for c in needed_cols if c in df.columns]
    df = df[existing_cols].copy()

    if "Driver" in df.columns:
        df = df[df["Driver"].isin(selected_drivers)]

    if "Compound" in df.columns:
        df = df[df["Compound"].astype(str).str.upper() == selected_compound.upper()]

    if "IsAccurate" in df.columns:
        df = df[df["IsAccurate"] == True]

    if "LapTime" in df.columns:
        df = df[df["LapTime"].notna()]

    if "PitInTime" in df.columns:
        df = df[df["PitInTime"].isna()]

    if "PitOutTime" in df.columns:
        df = df[df["PitOutTime"].isna()]

    if "TrackStatus" in df.columns:
        # zostawiamy głównie normal green flag laps
        df = df[df["TrackStatus"].astype(str).isin(["1", ""])] if not df.empty else df

    if df.empty:
        return pd.DataFrame()

    df["LapTimeSeconds"] = df["LapTime"].apply(lap_time_to_seconds)
    df = df[df["LapTimeSeconds"].notna()].copy()

    df["LapNumber"] = pd.to_numeric(df["LapNumber"], errors="coerce")
    df["Stint"] = pd.to_numeric(df["Stint"], errors="coerce")
    df["TyreLife"] = pd.to_numeric(df["TyreLife"], errors="coerce")
    df = df.dropna(subset=["LapNumber", "Stint"]).copy()

    # zostaw tylko stinty o sensownej długości
    stint_sizes = (
        df.groupby(["Driver", "Stint"])
        .size()
        .reset_index(name="StintSize")
    )

    df = df.merge(stint_sizes, on=["Driver", "Stint"], how="left")
    df = df[df["StintSize"] >= min_stint_length].copy()

    if df.empty:
        return pd.DataFrame()

    # numer okrążenia w obrębie stintu
    df = df.sort_values(["Driver", "Stint", "LapNumber"]).copy()
    df["LapInStint"] = df.groupby(["Driver", "Stint"]).cumcount() + 1

    return df


def summarize_degradation(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    summary_rows = []

    for (driver, stint), group in df.groupby(["Driver", "Stint"]):
        group = group.sort_values("LapInStint").copy()

        if len(group) < 2:
            continue

        avg_pace = group["LapTimeSeconds"].mean()
        first_lap = group["LapTimeSeconds"].iloc[0]
        last_lap = group["LapTimeSeconds"].iloc[-1]
        degradation_total = last_lap - first_lap
        degradation_per_lap = degradation_total / max(len(group) - 1, 1)

        compound = group["Compound"].iloc[0] if "Compound" in group.columns else "UNKNOWN"

        summary_rows.append({
            "Driver": driver,
            "Stint": int(stint),
            "Compound": compound,
            "Laps": len(group),
            "AvgPaceSeconds": avg_pace,
            "FirstLapSeconds": first_lap,
            "LastLapSeconds": last_lap,
            "DegTotalSeconds": degradation_total,
            "DegPerLapSeconds": degradation_per_lap,
        })

    return pd.DataFrame(summary_rows)


def format_seconds_to_laptime(seconds):
    if seconds is None or pd.isna(seconds):
        return "—"

    minutes = int(seconds // 60)
    rem = seconds - minutes * 60
    return f"{minutes}:{rem:06.3f}"


def get_degradation_insight(summary_df: pd.DataFrame) -> str:
    if summary_df is None or summary_df.empty:
        return "Brak wystarczających danych do oceny degradacji opon."

    best_deg = summary_df.sort_values("DegPerLapSeconds", ascending=True).iloc[0]
    best_avg = summary_df.sort_values("AvgPaceSeconds", ascending=True).iloc[0]

    if best_deg["Driver"] == best_avg["Driver"]:
        return (
            f"Najlepiej oponami zarządzał {best_deg['Driver']} — miał zarówno "
            f"najniższą degradację ({best_deg['DegPerLapSeconds']:.3f}s/okr.), "
            f"jak i najlepsze średnie tempo."
        )

    return (
        f"Najmniejszą degradację miał {best_deg['Driver']} "
        f"({best_deg['DegPerLapSeconds']:.3f}s/okr.), "
        f"a najszybsze średnie tempo uzyskał {best_avg['Driver']} "
        f"({format_seconds_to_laptime(best_avg['AvgPaceSeconds'])})."
    )