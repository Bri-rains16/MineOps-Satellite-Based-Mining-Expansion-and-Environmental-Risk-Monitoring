"""
src/proximity_rf/visualizer.py
------------------------------
Generates:
1. Spatial GIS map displaying Mine/Bare reference polygons alongside environmental classes & buffer rings.
2. Proximity distance distribution chart.
3. Buffer exposure comparison chart.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd
from shapely.validation import make_valid

log = logging.getLogger(__name__)

# Standard MineOps Color Palette
COLORS = {
    "mine_bare": "#E74C3C",    # Red
    "settlement": "#F39C12",   # Amber / Orange
    "forest": "#27AE60",       # Forest Green
    "water": "#2980B9",        # Blue
    "buffer": "#8E44AD"        # Purple
}


def plot_gis_map(
    mine_bare_gdf: gpd.GeoDataFrame,
    env_dict: Dict[str, gpd.GeoDataFrame],
    year: int,
    output_path: Path
) -> None:
    """Renders a spatial GIS map in EPSG:32643 showing classes and 500m/1000m buffer zones."""
    fig, ax = plt.subplots(figsize=(10, 10), dpi=300)

    # 1. Plot Forest (base landscape)
    if not env_dict["forest"].empty:
        env_dict["forest"].plot(ax=ax, color=COLORS["forest"], alpha=0.45, edgecolor="none", label="Forest/Vegetation")

    # 2. Plot Buffer Zones around Mine/Bare Land
    if not mine_bare_gdf.empty:
        union_geom = mine_bare_gdf.geometry.union_all() if hasattr(mine_bare_gdf.geometry, "union_all") else mine_bare_gdf.geometry.unary_union
        union_geom = make_valid(union_geom)

        buf1000 = gpd.GeoSeries([union_geom.buffer(1000)], crs=mine_bare_gdf.crs)
        buf500 = gpd.GeoSeries([union_geom.buffer(500)], crs=mine_bare_gdf.crs)

        buf1000.boundary.plot(ax=ax, color="#8E44AD", linestyle=":", linewidth=1.2, label="1000m Buffer")
        buf500.boundary.plot(ax=ax, color="#9B59B6", linestyle="--", linewidth=1.5, label="500m Buffer")

    # 3. Plot Settlement
    if not env_dict["settlement"].empty:
        env_dict["settlement"].plot(ax=ax, color=COLORS["settlement"], alpha=0.75, edgecolor="none", label="Settlement")

    # 4. Plot Water
    if not env_dict["water"].empty:
        env_dict["water"].plot(ax=ax, color=COLORS["water"], alpha=0.85, edgecolor="#1B4F72", linewidth=0.5, label="Water")

    # 5. Plot Mine/Bare Reference Polygons
    if not mine_bare_gdf.empty:
        mine_bare_gdf.plot(ax=ax, color=COLORS["mine_bare"], alpha=0.85, edgecolor="#78281F", linewidth=0.8, label="Mine/Bare Land")

    ax.set_title(
        f"Zawar Region — Random Forest Land Cover & Proximity GIS Map ({year})\n"
        "Reference: Mine/Bare Land (Class 0) vs. Environmental Features",
        fontsize=12, fontweight="bold", pad=12
    )
    ax.set_xlabel("UTM Zone 43N Easting (m)", fontsize=10)
    ax.set_ylabel("UTM Zone 43N Northing (m)", fontsize=10)
    ax.grid(True, linestyle="--", alpha=0.4)

    # Custom Legend
    legend_patches = [
        mpatches.Patch(color=COLORS["mine_bare"], label=f"Mine/Bare Land ({len(mine_bare_gdf)} polygons)"),
        mpatches.Patch(color=COLORS["settlement"], label=f"Settlement ({len(env_dict['settlement'])} polygons)"),
        mpatches.Patch(color=COLORS["forest"], label=f"Forest/Vegetation ({len(env_dict['forest'])} polygons)"),
        mpatches.Patch(color=COLORS["water"], label=f"Water Bodies ({len(env_dict['water'])} polygons)"),
        mpatches.Patch(facecolor="none", edgecolor="#9B59B6", linestyle="--", label="500m Buffer Zone"),
        mpatches.Patch(facecolor="none", edgecolor="#8E44AD", linestyle=":", label="1000m Buffer Zone"),
    ]
    ax.legend(handles=legend_patches, loc="upper right", framealpha=0.9, fontsize=9)

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    log.info("Saved GIS map -> %s", output_path)


def plot_charts(
    distances_df: pd.DataFrame,
    exposure_df: pd.DataFrame,
    year: int,
    charts_dir: Path
) -> None:
    """Generates proximity distance distribution and environmental buffer exposure charts."""
    charts_dir.mkdir(parents=True, exist_ok=True)

    # Chart 1: Proximity Distances Boxplot / Component Distribution
    fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
    dist_data = [
        distances_df["dist_settlement_m"].dropna(),
        distances_df["dist_forest_m"].dropna(),
        distances_df["dist_water_m"].dropna(),
    ]
    labels = ["To Settlement", "To Forest", "To Water"]
    colors = [COLORS["settlement"], COLORS["forest"], COLORS["water"]]

    box = ax.boxplot(dist_data, tick_labels=labels, patch_artist=True, medianprops=dict(color="black", linewidth=1.5))
    for patch, color in zip(box["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    # Annotate medians
    for i, data in enumerate(dist_data, start=1):
        med = data.median()
        ax.text(i, med + 40, f"Median: {med:.0f} m", ha="center", fontsize=9, fontweight="bold")

    ax.set_title(f"Distance from Mine/Bare Polygons to Nearest Features ({year})", fontsize=11, fontweight="bold")
    ax.set_ylabel("Distance (metres)", fontsize=10)
    ax.grid(True, linestyle="--", alpha=0.5, axis="y")
    plt.tight_layout()
    dist_chart_path = charts_dir / f"proximity_distances_{year}.png"
    fig.savefig(dist_chart_path, dpi=300)
    plt.close(fig)
    log.info("Saved distance chart -> %s", dist_chart_path)

    # Chart 2: Buffer Zone Environmental Exposure (Hectares)
    if not exposure_df.empty:
        fig, ax = plt.subplots(figsize=(9, 5), dpi=300)
        x = exposure_df["buffer_radius_m"].astype(str) + "m"
        width = 0.25

        ax.bar(
            [i - width for i in range(len(x))],
            exposure_df["forest_exposed_ha"],
            width=width, label="Forest Area Exposed", color=COLORS["forest"], alpha=0.85
        )
        ax.bar(
            range(len(x)),
            exposure_df["settlement_exposed_ha"],
            width=width, label="Settlement Area Exposed", color=COLORS["settlement"], alpha=0.85
        )
        ax.bar(
            [i + width for i in range(len(x))],
            exposure_df["water_exposed_ha"],
            width=width, label="Water Area Exposed", color=COLORS["water"], alpha=0.85
        )

        ax.set_xticks(range(len(x)))
        ax.set_xticklabels([f"Buffer: {val}" for val in x], fontsize=10)
        ax.set_ylabel("Exposed Area (Hectares)", fontsize=10)
        ax.set_title(f"Environmental Land Cover within Proximity Buffers ({year})", fontsize=11, fontweight="bold")
        ax.legend(loc="upper left", fontsize=9)
        ax.grid(True, linestyle="--", alpha=0.5, axis="y")

        plt.tight_layout()
        exposure_chart_path = charts_dir / f"buffer_exposure_{year}.png"
        fig.savefig(exposure_chart_path, dpi=300)
        plt.close(fig)
        log.info("Saved buffer exposure chart -> %s", exposure_chart_path)
