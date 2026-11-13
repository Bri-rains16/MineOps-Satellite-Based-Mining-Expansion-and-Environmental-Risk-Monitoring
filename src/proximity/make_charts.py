"""
make_charts.py
--------------
Generate three simple line graphs showing annual median proximity distances:
  1. Mining-to-Water
  2. Mining-to-Settlement
  3. Mining-to-Forest

X-axis: year (2021–2026)
Y-axis: median distance in metres across all mining components that year

Output PNGs saved to outputs/proximity/charts/.
"""

from __future__ import annotations

import logging
from pathlib import Path

import matplotlib
matplotlib.use("Agg")          # non-interactive backend — must be before pyplot import
import matplotlib.pyplot as plt
import pandas as pd

log = logging.getLogger(__name__)

CHARTS_DIR = Path("outputs/proximity/charts")

_CHART_CONFIG = [
    {
        "col":   "dist_water_m",
        "label": "Mining-to-Water Distance",
        "color": "#2196F3",
        "file":  "proximity_water_trend.png",
    },
    {
        "col":   "dist_settlement_m",
        "label": "Mining-to-Settlement Distance",
        "color": "#FF5722",
        "file":  "proximity_settlement_trend.png",
    },
    {
        "col":   "dist_forest_m",
        "label": "Mining-to-Forest Distance",
        "color": "#4CAF50",
        "file":  "proximity_forest_trend.png",
    },
]


def make_charts(summary_df: pd.DataFrame) -> None:
    """
    Generate one line chart per environmental class.

    Parameters
    ----------
    summary_df : DataFrame with columns year + dist_water_m, dist_settlement_m, dist_forest_m
        (all years combined, one row per mining polygon per year)
    """
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)

    # Annual median per class
    annual = (
        summary_df.groupby("year")[["dist_water_m", "dist_settlement_m", "dist_forest_m"]]
        .median()
        .reset_index()
    )

    for cfg in _CHART_CONFIG:
        col   = cfg["col"]
        label = cfg["label"]
        color = cfg["color"]
        out   = CHARTS_DIR / cfg["file"]

        years  = annual["year"].tolist()
        values = annual[col].tolist()

        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(years, values, marker="o", color=color, linewidth=2, markersize=7)

        # Annotate each point with its value
        for x, y in zip(years, values):
            if pd.notna(y):
                ax.annotate(
                    f"{y:.0f} m",
                    xy=(x, y),
                    xytext=(0, 10),
                    textcoords="offset points",
                    ha="center",
                    fontsize=9,
                )

        ax.set_title(f"{label} (2021–2026)", fontsize=13, fontweight="bold")
        ax.set_xlabel("Year", fontsize=11)
        ax.set_ylabel("Median Distance (m)", fontsize=11)
        ax.set_xticks(years)
        ax.grid(True, linestyle="--", alpha=0.5)
        plt.tight_layout()
        fig.savefig(out, dpi=300)
        plt.close(fig)
        log.info("Saved chart → %s", out)

    log.info("All 3 proximity charts generated in %s", CHARTS_DIR)
