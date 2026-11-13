"""
make_all_distance_charts.py
---------------------------
Generates individual and unified distance trend charts (mean and median)
from Mine/Bare components to Settlement, Forest, and Water for 2021-2026.
"""

from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

CSV_PATH = Path("outputs/proximity_rf_clean_2021-2026/proximity_clean_summary.csv")
CHARTS_DIR = Path("outputs/proximity_rf_clean_2021-2026/charts")
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(CSV_PATH)

configs = [
    {
        "target": "Settlement",
        "mean_col": "dist_settlement_mean_m",
        "median_col": "dist_settlement_median_m",
        "color_mean": "#E67E22",
        "color_median": "#B9770E",
        "filename": "proximity_settlement_distances_trend.png",
        "title": "Proximity Distance from Mine/Bare Components to Settlement (2021–2026)"
    },
    {
        "target": "Forest/Vegetation",
        "mean_col": "dist_forest_mean_m",
        "median_col": "dist_forest_median_m",
        "color_mean": "#27AE60",
        "color_median": "#1E8449",
        "filename": "proximity_forest_distances_trend.png",
        "title": "Proximity Distance from Mine/Bare Components to Forest/Vegetation (2021–2026)"
    },
    {
        "target": "Water Bodies",
        "mean_col": "dist_water_mean_m",
        "median_col": "dist_water_median_m",
        "color_mean": "#2980B9",
        "color_median": "#154360",
        "filename": "proximity_water_distances_trend.png",
        "title": "Proximity Distance from Mine/Bare Components to Water Bodies (2021–2026)"
    }
]

# 1. Generate individual charts for each class
for cfg in configs:
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=300)
    ax.plot(df["year"], df[cfg["mean_col"]], marker="s", linestyle="-", color=cfg["color_mean"], linewidth=2.2, label=f"Mean Distance to {cfg['target']}")
    ax.plot(df["year"], df[cfg["median_col"]], marker="o", linestyle="--", color=cfg["color_median"], linewidth=2.2, label=f"Median Distance to {cfg['target']}")

    for x, y in zip(df["year"], df[cfg["mean_col"]]):
        ax.annotate(f"{y:.1f}m", (x, y), textcoords="offset points", xytext=(0, 6), ha="center", fontsize=8.5, fontweight="semibold")
    for x, y in zip(df["year"], df[cfg["median_col"]]):
        ax.annotate(f"{y:.1f}m", (x, y), textcoords="offset points", xytext=(0, -13), ha="center", fontsize=8.5, color=cfg["color_median"])

    ax.set_title(cfg["title"], fontsize=11, fontweight="bold", pad=10)
    ax.set_xlabel("Year", fontsize=10)
    ax.set_ylabel("Distance (metres)", fontsize=10)
    ax.set_xticks(df["year"])
    ax.legend(fontsize=9, loc="upper right")
    ax.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()

    out_file = CHARTS_DIR / cfg["filename"]
    fig.savefig(out_file, dpi=300)
    plt.close(fig)
    print(f"Saved: {out_file}")

# 2. Generate a 3-panel side-by-side comparison chart
fig, axes = plt.subplots(1, 3, figsize=(16, 4.5), dpi=300)
for idx, cfg in enumerate(configs):
    ax = axes[idx]
    ax.plot(df["year"], df[cfg["mean_col"]], marker="s", linestyle="-", color=cfg["color_mean"], linewidth=2, label="Mean Dist")
    ax.plot(df["year"], df[cfg["median_col"]], marker="o", linestyle="--", color=cfg["color_median"], linewidth=2, label="Median Dist")
    for x, y in zip(df["year"], df[cfg["mean_col"]]):
        ax.annotate(f"{y:.0f}m", (x, y), textcoords="offset points", xytext=(0, 5), ha="center", fontsize=8)
    ax.set_title(f"To {cfg['target']}", fontsize=11, fontweight="bold")
    ax.set_xlabel("Year", fontsize=9)
    if idx == 0:
        ax.set_ylabel("Distance (metres)", fontsize=9)
    ax.set_xticks(df["year"])
    ax.legend(fontsize=8.5)
    ax.grid(True, linestyle="--", alpha=0.5)

fig.suptitle("Mine/Bare Components Distance Trends to Environmental Classes (2021–2026)", fontsize=12, fontweight="bold")
plt.tight_layout()
combined_file = CHARTS_DIR / "proximity_all_classes_distances_trend.png"
fig.savefig(combined_file, dpi=300)
plt.close(fig)
print(f"Saved: {combined_file}")
