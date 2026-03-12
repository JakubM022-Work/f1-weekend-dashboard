import matplotlib.pyplot as plt


def plot_stints(stints):
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