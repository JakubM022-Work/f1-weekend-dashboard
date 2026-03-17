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
    result = pd.DataFrame(records)
    
    # Reset index aby upewnić się że data jest dostępna
    result = result.reset_index(drop=True)
    return result


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
    
    # Fallback: jeśli nie ma "Driver", spróbuj "Abbreviation"
    if "Driver" not in laps.columns and "Abbreviation" in race.laps.columns:
        laps["Driver"] = race.laps["Abbreviation"].copy()
    
    return laps

@st.cache_data(show_spinner=False)
def load_race_laps_full(year: int, round_number: int) -> pd.DataFrame:
    race = fastf1.get_session(year, round_number, "R")
    race.load()

    wanted_cols = [
        "Driver",
        "LapNumber",
        "LapTime",
        "Compound",
        "TyreLife",
        "Stint",
        "IsAccurate",
        "TrackStatus",
        "PitInTime",
        "PitOutTime",
        "FreshTyre",
        "Position",
    ]

    laps = safe_plain_df(race.laps, wanted_cols)
    
    # Fallback: jeśli nie ma "Driver", spróbuj "Abbreviation"
    if "Driver" not in laps.columns and "Abbreviation" in race.laps.columns:
        laps["Driver"] = race.laps["Abbreviation"].copy()
    
    return laps


@st.cache_data(show_spinner=False)
def load_car_data_for_lap(year: int, round_number: int, session_code: str, driver: str, lap_number: int):
    """
    Ładuje car_data (telemetrię) dla konkretnego kierowcy i okrążenia.
    Zawiera: X, Y, Speed, Throttle, Brake, Gear, RPM itp.
    Zwraca: pandas DataFrame
    """
    try:
        session = fastf1.get_session(year, round_number, session_code)
        session.load(telemetry=True, weather=False)
        
        # Pobranie lapów dla kierowcy - spróbuj z abbreviation najpierw
        try:
            laps = session.laps.pick_driver(driver)
        except:
            # Fallback: spróbuj z imieniem/nazwiskiem
            try:
                laps = session.laps[session.laps["Driver"] == driver]
            except:
                return None
        
        if len(laps) == 0:
            return None
        
        # Wybór konkretnego lapa
        lap = laps[laps["LapNumber"] == lap_number]
        
        if len(lap) == 0:
            # Fallback: spróbuj znaleźć najbliższe okrążenie z danymi
            laps_with_data = laps.dropna(subset=["LapTime"])
            if len(laps_with_data) == 0:
                return None
            # Pobierz okrążenie najbliższe podanemu numeru
            lap = laps_with_data.iloc[(laps_with_data["LapNumber"] - lap_number).abs().argmin():].head(1)
        
        if len(lap) == 0:
            return None
        
        lap = lap.iloc[0]
        
        # Pobranie car_data dla tego lapa
        car_data = lap.get_car_data()
        
        # Konwersja na DataFrame
        if car_data is not None:
            try:
                car_data_df = car_data.to_pandas()
                if len(car_data_df) > 0:
                    return car_data_df
            except:
                pass
        
        return None
    except Exception as e:
        print(f"Błąd podczas ładowania car_data: {e}")
        return None


@st.cache_data(show_spinner=False)
def get_fastest_lap(year: int, round_number: int, session_code: str, driver: str):
    """
    Pobiera informacje o najszybszym lapie dla kierowcy w danej sesji.
    """
    try:
        session = fastf1.get_session(year, round_number, session_code)
        session.load()
        
        laps = session.laps.pick_driver(driver)
        if len(laps) == 0:
            return None
        
        # Filtruje tylko kompletne, dokładne lapy
        accurate_laps = laps[laps["IsAccurate"] == True]
        
        if len(accurate_laps) == 0:
            accurate_laps = laps
        
        fastest = accurate_laps.sort_values("LapTime").iloc[0]
        return fastest
    except Exception as e:
        print(f"Błąd podczas pobrania najszybszego lapa: {e}")
        return None


@st.cache_data(show_spinner=False)
def load_drivers_for_session(year: int, round_number: int, session_code: str) -> list:
    """
    Pobiera listę wszystkich kierowców w danej sesji.
    """
    try:
        session = fastf1.get_session(year, round_number, session_code)
        session.load()
        
        drivers = []
        
        # Metoda 1: Spróbuj pobrać z results
        if hasattr(session, 'results') and session.results is not None and len(session.results) > 0:
            if "Abbreviation" in session.results.columns:
                drivers = session.results["Abbreviation"].dropna().unique().tolist()
        
        # Metoda 2: Fallback z laps
        if not drivers and hasattr(session, 'laps') and session.laps is not None:
            if "Driver" in session.laps.columns:
                drivers = session.laps["Driver"].dropna().unique().tolist()
        
        return sorted(drivers) if drivers else []

    except Exception as e:
        print(f"Błąd podczas pobrania kierowców: {e}")
        return []


@st.cache_data(show_spinner=False)
def load_session_with_telemetry(year: int, round_number: int, session_code: str):
    """
    Załaduj sesję z telemetrią RAZ dla całej sesji.
    Po załadowaniu, każdy lap będzie miał dostępne car_data.
    """
    try:
        print(f"\n[DEBUG] load_session_with_telemetry: {year} Round {round_number} Session {session_code}")
        session = fastf1.get_session(year, round_number, session_code)
        print(f"[DEBUG] Session object created, type: {type(session)}")
        print(f"[DEBUG] Session: {session}")
        
        # KEY: Załaduj Z telemetry=True, to załaduje car_data automatically
        session.load(telemetry=True)
        print(f"[DEBUG] Session loaded with telemetry=True")
        print(f"[DEBUG] Total laps: {len(session.laps)}")
        
        # Sprawdzenie czy wciąż mamy laps
        if len(session.laps) > 0:
            test_lap = session.laps.iloc[0]
            print(f"[DEBUG] First lap: {test_lap['Driver']} - Lap #{test_lap['LapNumber']}")
            print(f"[DEBUG] First lap has get_car_data method: {hasattr(test_lap, 'get_car_data')}")
        
        return session
    except Exception as e:
        print(f"\n[ERROR] Błąd przy ładowaniu sesji z telemetrią: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_car_data_from_lap(lap_obj):
    """
    Pobiera car_data z lap object.
    Zakłada że sesja była już załadowana z telemetry=True
    """
    try:
        if lap_obj is None:
            print(f"[DEBUG] get_car_data_from_lap: lap_obj is None")
            return None
        
        print(f"\n[DEBUG] get_car_data_from_lap: {lap_obj.get('Driver', '?')} - Lap #{lap_obj.get('LapNumber', '?')}")
        print(f"[DEBUG] lap_obj type: {type(lap_obj)}")
        print(f"[DEBUG] lap_obj has get_car_data: {hasattr(lap_obj, 'get_car_data')}")
        
        try:
            car_data = lap_obj.get_car_data()
        except Exception as get_car_error:
            print(f"[ERROR] get_car_data() failed: {get_car_error}")
            print(f"[DEBUG] Session: {lap_obj.session}")
            print(f"[DEBUG] Session has _car_data: {hasattr(lap_obj.session, '_car_data')}")
            raise
        
        print(f"[DEBUG] car_data type: {type(car_data)}")
        print(f"[DEBUG] car_data is None: {car_data is None}")
        
        if car_data is not None:
            print(f"[DEBUG] car_data length: {len(car_data)}")
            
            if len(car_data) > 0:
                # Konwersja Telemetry object do DataFrame
                # FastF1 3.8.1: Telemetry object można konwertować przez DataFrame constructor
                car_data_df = pd.DataFrame(car_data)
                print(f"[DEBUG] car_data_df shape: {car_data_df.shape}")
                print(f"[DEBUG] car_data_df columns: {list(car_data_df.columns)}")
                
                # Teraz pobierz position_data aby mieć X, Y
                print(f"[DEBUG] Pobieranie position_data...")
                try:
                    position_data = lap_obj.get_pos_data()
                    if position_data is not None:
                        pos_data_df = pd.DataFrame(position_data)
                        print(f"[DEBUG] position_data_df shape: {pos_data_df.shape}")
                        print(f"[DEBUG] position_data_df columns: {list(pos_data_df.columns)}")
                        
                        # Merge car_data i position_data
                        if 'Time' in car_data_df.columns and 'Time' in pos_data_df.columns:
                            merged = pd.merge_asof(
                                car_data_df.sort_values('Time'),
                                pos_data_df.sort_values('Time'),
                                on='Time',
                                direction='nearest'
                            )
                            print(f"[DEBUG] merged shape: {merged.shape}")
                            print(f"[DEBUG] merged columns: {list(merged.columns)}")
                            return merged
                    else:
                        print(f"[DEBUG] position_data is None")
                except Exception as pos_error:
                    print(f"[DEBUG] position_data error: {pos_error} - zwracam car_data bez pozycji")
                
                # Fallback - zwróć car_data jeśli position_data nie działa
                return car_data_df
            else:
                print(f"[DEBUG] car_data is empty")
                return None
        else:
            print(f"[DEBUG] car_data is None, returning None")
            return None
    except Exception as e:
        print(f"\n[ERROR] Błąd przy pobieraniu car_data: {e}")
        import traceback
        traceback.print_exc()
        return None