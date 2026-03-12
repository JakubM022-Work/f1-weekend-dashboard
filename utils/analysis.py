import pandas as pd


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