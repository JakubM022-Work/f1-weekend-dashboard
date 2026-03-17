#!/usr/bin/env python3
"""
Debug script - sprawdzenie czy car_data jest dostępna w FF1
"""
import fastf1
import pandas as pd

# Wczytaj sesję
year = 2025
round_num = 1
session_code = "R"

print(f"\n[TEST] Ładuję sesję {year} Round {round_num} Session {session_code}")
session = fastf1.get_session(year, round_num, session_code)

print("[TEST] Załadowuję Z telemetry=True...")
session.load(telemetry=True)
print(f"[TEST] Session loaded, laps count: {len(session.laps)}")

# Wybierz kierowcę
try:
    driver_abbr = session.results.iloc[0]["Abbreviation"]
except:
    driver_abbr = session.laps.iloc[0]["Driver"]

print(f"[TEST] Wybieram kierowcę: {driver_abbr}")

# Weź jego lapy
try:
    driver_laps = session.laps.pick_driver(driver_abbr)
except:
    driver_laps = session.laps[session.laps["Driver"] == driver_abbr]

print(f"[TEST] Liczba lapów dla {driver_abbr}: {len(driver_laps)}")

if len(driver_laps) > 0:
    lap1 = driver_laps.iloc[0]
    lap_num = lap1["LapNumber"]
    print(f"[TEST] Sprawdzam Lap #{lap_num}")
    
    # Spróbuj get_car_data bez telemetrii
    print("[TEST] Próbuję get_car_data() bez telemetrii...")
    car_data_no_tel = lap1.get_car_data()
    print(f"[TEST] Wynik bez telemetrii: {car_data_no_tel}")
    
    # Teraz załaduj Z telemetrią
    print("\n[TEST] Załadowuję sesję Z telemetrią...")
    session2 = fastf1.get_session(year, round_num, session_code)
    session2.load(telemetry=True)
    print(f"[TEST] Session loaded with telemetry, laps count: {len(session2.laps)}")
    
    # Spróbuj get_car_data z telemetrią
    try:
        driver_laps2 = session2.laps.pick_driver(driver_abbr)
    except:
        driver_laps2 = session2.laps[session2.laps["Driver"] == driver_abbr]
    
    if len(driver_laps2) > 0:
        lap1_tel = driver_laps2.iloc[0]
        print(f"[TEST] Próbuję get_car_data() Z telemetrią dla Lap #{lap_num}...")
        car_data_with_tel = lap1_tel.get_car_data()
        print(f"[TEST] Wynik Z telemetrią: {type(car_data_with_tel)}")
        
        if car_data_with_tel is not None:
            print(f"[TEST] Car data length: {len(car_data_with_tel)}")
            if len(car_data_with_tel) > 0:
                df = pd.DataFrame(car_data_with_tel)
                print(f"[TEST] DataFrame shape: {df.shape}")
                print(f"[TEST] Kolumny: {list(df.columns)}")
                print(f"[TEST] First row:\n{df.iloc[0]}")
            else:
                print("[TEST] Car data jest pusty")
        else:
            print("[TEST] Car data jest None")

print("\n[TEST] Test zakończony")
