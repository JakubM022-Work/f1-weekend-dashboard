import pandas as pd
import streamlit as st
import fastf1


def safe_plain_df(df_like, columns=None) -> pd.DataFrame:
    if df_like is None:
        return pd.DataFrame()

    df = df_like.copy()

    if columns is not None:
        existing_cols = [col for col in columns if col in df.columns]
        df = df[existing_cols].copy()

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