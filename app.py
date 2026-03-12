import os
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import fastf1

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
st.write("Mini dashboard weekendu F1 zbudowany w Pythonie przy użyciu FastF1 i Streamlit.")


# =========================
# Helpers
# =========================
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


def safe_plain_df(df_like, columns=None) -> pd.DataFrame:
    """
    Zamienia obiekty FastF1/Pandas na zwykły pandas.DataFrame,
    zachowując tylko wskazane kolumny.
    """
    if df_like is None:
        return pd.DataFrame()

    df = df_like.copy()

    if columns is not None:
        existing_cols = [col for col in columns if col in df.columns]
        df = df[existing_cols].copy()

    # Najstabilniejsza konwersja dla obiektów FastF1
    records = df.to_dict(orient="records")
    return pd.DataFrame(records)


def get_event_schedule(year: int) -> pd.DataFrame:
    schedule = fastf1.get_event_schedule(year)
    return pd.DataFrame(schedule).copy()


@st.cache_data(show_spinner=False)
def load_session_results(year: int, round_number: int, session_code: str) -> pd.DataFrame:
    session = fastf1.get_session(year, round_number, session_code)
    session.load()

    wanted_cols = [
        "Position",
        "FullName",
        "Abbreviation",
        "TeamName",
        "Q1",
        "Q2",
        "Q3",
        "GridPosition",
        "Status",
        "Points",
    ]

    results = safe_plain_df(session.results, wanted_cols)
    return results


@st.cache_data(show_spinner=False)
def load_race_laps(year: int, round_number: int) -> pd.DataFrame:
    race = fastf1.get_session(year, round_number, "R")
    race.load()

    wanted_cols = ["Driver", "Stint", "Compound", "LapNumber"]
    laps = safe_plain_df(race.laps, wanted_cols)
    return laps


def prepare_qualifying_top10(quali_results: pd.DataFrame) -> pd.DataFrame:
    if quali_results.empty:
        return pd.DataFrame()

    df = quali_results.copy()

    if "Position" in df.columns:
        df["Position"] = pd.to_numeric(df["Position"], errors="coerce")
        df = df[df["Position"].notna()].copy()
        df = df.sort_values("Position").head(10)

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


def prepare_race_top10(race_results: pd.DataFrame) -> pd.DataFrame:
    if race_results.empty:
        return pd.DataFrame()

    df = race_results.copy()

    if "Position" in df.columns:
        df["Position"] = pd.to_numeric(df["Position"], errors="coerce")
        df = df[df["Position"].notna()].copy()
        df = df.sort_values("Position").head(10)

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


def plot_stints(stints: pd.DataFrame):
    if stints.empty:
        return None

    drivers = list(stints["Driver"].drop_duplicates())

    fig, ax = plt.subplots(figsize=(12, max(6, len(drivers) * 0.45)))

    compound_colors = {
        "SOFT": "#FF3333",
        "MEDIUM": "#FFD12E",
        "HARD": "#FFFFFF",
        "INTERMEDIATE": "#39B54A",
        "WET": "#0067AD",
        "UNKNOWN": "#888888",
    }

    for driver in drivers:
        driver_stints = stints[stints["Driver"] == driver]
        cumulative_start = 1

        for _, row in driver_stints.iterrows():
            compound = str(row["Compound"]).upper()
            length = row["StintLength"]
            color = compound_colors.get(compound, "#999999")

            ax.barh(
                y=driver,
                width=length,
                left=cumulative_start,
                color=color,
                edgecolor="black"
            )

            cumulative_start += length

    ax.set_title("Race stints by driver")
    ax.set_xlabel("Lap")
    ax.set_ylabel("Driver")
    ax.invert_yaxis()

    return fig


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

        st.write("Quali columns:", list(quali_results.columns))
        st.write("Race columns:", list(race_results.columns))
        st.write("Quali preview:")
        st.dataframe(quali_results.head())
        st.write("Race preview:")
        st.dataframe(race_results.head())

        st.subheader(f"{event_name} ({season})")


        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Top 10 kwalifikacji")
            quali_top10 = prepare_qualifying_top10(quali_results)
            if not quali_top10.empty:
                st.dataframe(quali_top10, use_container_width=True, hide_index=True)
            else:
                st.info("Brak danych kwalifikacji do wyświetlenia.")

        with col2:
            st.markdown("### Top 10 wyścigu")
            race_top10 = prepare_race_top10(race_results)
            if not race_top10.empty:
                st.dataframe(race_top10, use_container_width=True, hide_index=True)
            else:
                st.info("Brak danych wyścigu do wyświetlenia.")

        changes = calculate_position_changes(race_results)

        if not changes.empty:
            best_gainers = changes.sort_values("PositionsChanged", ascending=False).head(5)
            biggest_losers = changes.sort_values("PositionsChanged", ascending=True).head(5)

            col3, col4 = st.columns(2)

            with col3:
                st.markdown("### Najwięcej zyskanych pozycji")
                st.dataframe(best_gainers, use_container_width=True, hide_index=True)

            with col4:
                st.markdown("### Najwięcej straconych pozycji")
                st.dataframe(biggest_losers, use_container_width=True, hide_index=True)
        else:
            st.info("Nie udało się obliczyć zmian pozycji.")

        st.markdown("### Wykres stintów na oponach")
        st.caption("Każdy pasek pokazuje długość kolejnych stintów kierowcy podczas wyścigu.")

        stint_data = prepare_stint_data(race_laps)
        fig = plot_stints(stint_data)

        if fig is not None:
            st.pyplot(fig, use_container_width=True)
        else:
            st.info("Brak danych stintów do wyświetlenia.")

    except Exception as e:
        st.error(f"Wystąpił błąd przy ładowaniu danych: {e}")
else:
    st.info("Wybierz sezon i rundę po lewej stronie, a następnie kliknij „Załaduj dashboard”.")