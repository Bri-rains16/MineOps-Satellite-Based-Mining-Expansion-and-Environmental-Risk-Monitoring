"""
src/proximity_rf/run_proximity_rf_clean.py
------------------------------------------
Independent proximity and environmental exposure analysis for the 6-year
mutually exclusive Random Forest classifications (2021-2026).

Consumes ONLY:
  outputs/polygons_rf_clean/zawar_all_classes_clean_{year}.geojson

Saves ALL outputs into:
  outputs/proximity_rf_clean/
    ├── components/         # Per-component distance CSVs
    ├── buffer_exposure/    # Buffer zone exposure CSVs (250m, 500m, 1000m)
    ├── maps/               # Comparable GIS maps for all 6 years
    ├── charts/             # 6-year comparison charts
    ├── proximity_clean_summary.csv
    └── proximity_clean_summary.json
"""

import json
import logging
from pathlib import Path
import sys
from typing import Dict, List, Any

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from shapely import STRtree
from shapely.validation import make_valid

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("proximity_rf_clean")

INPUT_DIR = Path("outputs/polygons_rf_clean")
OUTPUT_BASE = Path("outputs/proximity_rf_clean_2021-2026")
COMPONENTS_DIR = OUTPUT_BASE / "components"
BUFFERS_DIR = OUTPUT_BASE / "buffer_exposure"
MAPS_DIR = OUTPUT_BASE / "maps"
CHARTS_DIR = OUTPUT_BASE / "charts"

YEARS = [2021, 2022, 2023, 2024, 2025, 2026]
CRS_METRIC = "EPSG:32643"
BUFFERS = [250, 500, 1000]

COLORS = {
    0: ("Mine/Bare Land", "#E74C3C"),      # Red
    1: ("Settlement", "#F39C12"),          # Amber / Orange
    2: ("Forest/Vegetation", "#27AE60"),   # Green
    3: ("Water Bodies", "#2980B9")         # Blue
}


def load_clean_year(year: int):
    """
    Loads outputs/polygons_rf_clean/zawar_all_classes_clean_{year}.geojson.
    Extracts individual contiguous Mine/Bare components (class 0) and
    the continuous environmental layers (classes 1, 2, 3) in EPSG:32643.
    """
    path = INPUT_DIR / f"zawar_all_classes_clean_{year}.geojson"
    if not path.exists():
        raise FileNotFoundError(f"Input file missing: {path}")

    gdf = gpd.read_file(path).to_crs(CRS_METRIC)
    gdf["geometry"] = gdf["geometry"].apply(make_valid)

    # Class 0: Mine/Bare
    mine_rows = gdf[gdf["class_id"] == 0]
    if mine_rows.empty:
        raise ValueError(f"Year {year}: No Class 0 found in {path}")
    
    # Explode multi-polygons into individual connected components safely across all GeoPandas/Pandas versions
    try:
        mine_components = mine_rows.explode(ignore_index=True)
    except TypeError:
        mine_components = mine_rows.explode().reset_index(drop=True)
    mine_components = mine_components[mine_components.geometry.area >= 1000.0].copy().reset_index(drop=True) # >= 0.1 ha
    mine_components["component_id"] = [f"MB_{year}_{i+1:03d}" for i in range(len(mine_components))]
    mine_components["area_ha"] = (mine_components.geometry.area / 10000.0).round(4)

    # Environmental layers
    settlement_gdf = gdf[gdf["class_id"] == 1].copy().reset_index(drop=True)
    forest_gdf     = gdf[gdf["class_id"] == 2].copy().reset_index(drop=True)
    water_gdf      = gdf[gdf["class_id"] == 3].copy().reset_index(drop=True)

    return mine_components, settlement_gdf, forest_gdf, water_gdf, gdf


def compute_component_distances(mine_components: gpd.GeoDataFrame, settlement_gdf, forest_gdf, water_gdf, year: int) -> pd.DataFrame:
    """Computes nearest distance in metres from each Mine/Bare polygon to settlement, forest, and water."""
    s_geom = settlement_gdf.geometry.iloc[0] if not settlement_gdf.empty else None
    f_geom = forest_gdf.geometry.iloc[0] if not forest_gdf.empty else None
    w_geom = water_gdf.geometry.iloc[0] if not water_gdf.empty else None

    records = []
    for _, row in mine_components.iterrows():
        m_geom = row.geometry
        d_s = round(float(m_geom.distance(s_geom)), 2) if s_geom else float("nan")
        d_f = round(float(m_geom.distance(f_geom)), 2) if f_geom else float("nan")
        d_w = round(float(m_geom.distance(w_geom)), 2) if w_geom else float("nan")

        records.append({
            "year": year,
            "component_id": row["component_id"],
            "area_ha": row["area_ha"],
            "dist_settlement_m": d_s,
            "dist_forest_m": d_f,
            "dist_water_m": d_w,
            "category": "Mine/Bare Land"
        })

    return pd.DataFrame(records)


def compute_buffer_exposure(mine_components: gpd.GeoDataFrame, settlement_gdf, forest_gdf, water_gdf, year: int) -> pd.DataFrame:
    """Computes environmental land cover within 250m, 500m, and 1000m buffers around all Mine/Bare land."""
    union_mine = mine_components.geometry.union_all() if hasattr(mine_components.geometry, "union_all") else mine_components.geometry.unary_union
    union_mine = make_valid(union_mine)

    s_geom = settlement_gdf.geometry.iloc[0] if not settlement_gdf.empty else None
    f_geom = forest_gdf.geometry.iloc[0] if not forest_gdf.empty else None
    w_geom = water_gdf.geometry.iloc[0] if not water_gdf.empty else None

    total_s_ha = settlement_gdf["area_ha"].sum()
    total_f_ha = forest_gdf["area_ha"].sum()
    total_w_ha = water_gdf["area_ha"].sum()

    records = []
    for buf_m in BUFFERS:
        buf_geom = make_valid(union_mine.buffer(buf_m))
        buf_area_ha = round(buf_geom.area / 10000.0, 2)

        s_exp_ha = round(s_geom.intersection(buf_geom).area / 10000.0, 2) if s_geom else 0.0
        f_exp_ha = round(f_geom.intersection(buf_geom).area / 10000.0, 2) if f_geom else 0.0
        w_exp_ha = round(w_geom.intersection(buf_geom).area / 10000.0, 2) if w_geom else 0.0

        records.append({
            "year": year,
            "buffer_radius_m": buf_m,
            "buffer_total_area_ha": buf_area_ha,
            "settlement_exposed_ha": s_exp_ha,
            "settlement_exposure_pct": round(s_exp_ha / total_s_ha * 100.0, 2) if total_s_ha > 0 else 0.0,
            "forest_exposed_ha": f_exp_ha,
            "forest_exposure_pct": round(f_exp_ha / total_f_ha * 100.0, 2) if total_f_ha > 0 else 0.0,
            "water_exposed_ha": w_exp_ha,
            "water_exposure_pct": round(w_exp_ha / total_w_ha * 100.0, 2) if total_w_ha > 0 else 0.0,
        })

    return pd.DataFrame(records)


def plot_gis_map(gdf: gpd.GeoDataFrame, mine_components: gpd.GeoDataFrame, year: int, out_path: Path):
    """Generates a high-resolution GIS map showing mutually exclusive classes and buffer zones."""
    fig, ax = plt.subplots(figsize=(10, 10), dpi=300)

    # 1. Forest
    f = gdf[gdf["class_id"] == 2]
    if not f.empty:
        f.plot(ax=ax, color=COLORS[2][1], alpha=0.55, edgecolor="none")

    # 2. Buffers
    union_mine = mine_components.geometry.union_all() if hasattr(mine_components.geometry, "union_all") else mine_components.geometry.unary_union
    union_mine = make_valid(union_mine)
    b1000 = gpd.GeoSeries([union_mine.buffer(1000)], crs=CRS_METRIC)
    b500  = gpd.GeoSeries([union_mine.buffer(500)], crs=CRS_METRIC)
    b1000.boundary.plot(ax=ax, color="#8E44AD", linestyle=":", linewidth=1.2)
    b500.boundary.plot(ax=ax, color="#9B59B6", linestyle="--", linewidth=1.5)

    # 3. Settlement
    s = gdf[gdf["class_id"] == 1]
    if not s.empty:
        s.plot(ax=ax, color=COLORS[1][1], alpha=0.8, edgecolor="none")

    # 4. Water
    w = gdf[gdf["class_id"] == 3]
    if not w.empty:
        w.plot(ax=ax, color=COLORS[3][1], alpha=0.9, edgecolor="#1B4F72", linewidth=0.5)

    # 5. Mine/Bare
    m = gdf[gdf["class_id"] == 0]
    if not m.empty:
        m.plot(ax=ax, color=COLORS[0][1], alpha=0.9, edgecolor="#78281F", linewidth=0.5)

    ax.set_title(
        f"Zawar Mining Region — Clean Random Forest Classification & Proximity ({year})\n"
        "Mutually Exclusive Land Cover | Reference: Mine/Bare Land (Class 0)",
        fontsize=11, fontweight="bold", pad=10
    )
    ax.set_xlabel("UTM Zone 43N Easting (m)", fontsize=9)
    ax.set_ylabel("UTM Zone 43N Northing (m)", fontsize=9)
    ax.grid(True, linestyle="--", alpha=0.4)

    legend_patches = [
        mpatches.Patch(color=COLORS[0][1], label="Mine/Bare Land (Class 0)"),
        mpatches.Patch(color=COLORS[1][1], label="Settlement (Class 1)"),
        mpatches.Patch(color=COLORS[2][1], label="Forest/Vegetation (Class 2)"),
        mpatches.Patch(color=COLORS[3][1], label="Water Bodies (Class 3)"),
        mpatches.Patch(facecolor="none", edgecolor="#9B59B6", linestyle="--", label="500m Impact Buffer"),
        mpatches.Patch(facecolor="none", edgecolor="#8E44AD", linestyle=":", label="1000m Impact Buffer"),
    ]
    ax.legend(handles=legend_patches, loc="upper right", framealpha=0.92, fontsize=8.5)

    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=300)
    plt.close(fig)


def generate_six_year_charts(summary_df: pd.DataFrame, all_buffers_df: pd.DataFrame, all_areas_df: pd.DataFrame):
    """Generates comprehensive comparison charts across all 6 years."""
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)

    # Chart 1: Mine/Bare Area Trend (2021-2026)
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=300)
    ax.plot(summary_df["year"], summary_df["mine_bare_total_ha"], marker="o", color=COLORS[0][1], linewidth=2.5, markersize=7)
    for x, y in zip(summary_df["year"], summary_df["mine_bare_total_ha"]):
        ax.annotate(f"{y:.1f} ha", (x, y), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=9, fontweight="bold")
    ax.set_title("Zawar Mine/Bare Land Extent Trend (2021–2026)", fontsize=12, fontweight="bold")
    ax.set_xlabel("Year", fontsize=10)
    ax.set_ylabel("Area (Hectares)", fontsize=10)
    ax.set_xticks(summary_df["year"])
    ax.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    fig.savefig(CHARTS_DIR / "mine_bare_area_trend_2021_2026.png", dpi=300)
    plt.close(fig)

    # Chart 2: Average & Median Distance Trends to Water
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=300)
    ax.plot(summary_df["year"], summary_df["dist_water_mean_m"], marker="s", linestyle="-", color=COLORS[3][1], linewidth=2, label="Mean Distance to Water")
    ax.plot(summary_df["year"], summary_df["dist_water_median_m"], marker="o", linestyle="--", color="#154360", linewidth=2, label="Median Distance to Water")
    for x, y in zip(summary_df["year"], summary_df["dist_water_mean_m"]):
        ax.annotate(f"{y:.0f}m", (x, y), textcoords="offset points", xytext=(0, 6), ha="center", fontsize=8)
    ax.set_title("Proximity Distance from Mine/Bare Components to Water (2021–2026)", fontsize=11, fontweight="bold")
    ax.set_xlabel("Year", fontsize=10)
    ax.set_ylabel("Distance (metres)", fontsize=10)
    ax.set_xticks(summary_df["year"])
    ax.legend(fontsize=9)
    ax.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    fig.savefig(CHARTS_DIR / "proximity_water_distances_trend.png", dpi=300)
    plt.close(fig)

    # Chart 3: Buffer Exposure Percentages (250m vs 500m vs 1000m)
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5), dpi=300, sharey=True)
    for idx, buf in enumerate(BUFFERS):
        ax = axes[idx]
        b_df = all_buffers_df[all_buffers_df["buffer_radius_m"] == buf]
        ax.plot(b_df["year"], b_df["settlement_exposure_pct"], marker="o", color=COLORS[1][1], label="Settlement %")
        ax.plot(b_df["year"], b_df["forest_exposure_pct"], marker="^", color=COLORS[2][1], label="Forest %")
        ax.plot(b_df["year"], b_df["water_exposure_pct"], marker="s", color=COLORS[3][1], label="Water %")
        ax.set_title(f"{buf}m Buffer Zone Exposure", fontsize=10, fontweight="bold")
        ax.set_xlabel("Year", fontsize=9)
        if idx == 0:
            ax.set_ylabel("% of Regional Class Area Exposed", fontsize=9)
        ax.set_xticks(summary_df["year"])
        ax.grid(True, linestyle="--", alpha=0.5)
        if idx == 0:
            ax.legend(fontsize=8)
    fig.suptitle("Environmental Class Exposure Within Mine/Bare Impact Buffers (2021–2026)", fontsize=12, fontweight="bold")
    plt.tight_layout()
    fig.savefig(CHARTS_DIR / "buffer_exposure_comparison_2021_2026.png", dpi=300)
    plt.close(fig)

    # Chart 4: Land-Cover Stacked Distribution
    fig, ax = plt.subplots(figsize=(9, 4.5), dpi=300)
    pivot_area = all_areas_df.pivot(index="year", columns="class_name", values="area_ha")
    classes_order = ["Mine/Bare Land", "Settlement", "Forest/Vegetation", "Water Bodies"]
    colors_order = [COLORS[0][1], COLORS[1][1], COLORS[2][1], COLORS[3][1]]
    ax.stackplot(pivot_area.index, [pivot_area[c] for c in classes_order], labels=classes_order, colors=colors_order, alpha=0.85)
    ax.set_title("Zawar AOI Mutually Exclusive Land-Cover Distribution (2021–2026)", fontsize=11, fontweight="bold")
    ax.set_xlabel("Year", fontsize=10)
    ax.set_ylabel("Area (Hectares)", fontsize=10)
    ax.set_xticks(summary_df["year"])
    ax.legend(loc="upper right", fontsize=8.5)
    ax.grid(True, linestyle="--", alpha=0.4)
    plt.tight_layout()
    fig.savefig(CHARTS_DIR / "landcover_distribution_stacked_2021_2026.png", dpi=300)
    plt.close(fig)


def main():
    log.info("=== Starting Clean Random Forest Proximity Analysis (2021–2026) ===")
    COMPONENTS_DIR.mkdir(parents=True, exist_ok=True)
    BUFFERS_DIR.mkdir(parents=True, exist_ok=True)
    MAPS_DIR.mkdir(parents=True, exist_ok=True)
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)

    all_summary_rows = []
    all_buffers_list = []
    all_areas_list = []

    for yr in YEARS:
        log.info("-" * 60)
        log.info("PROCESSING YEAR %d", yr)
        log.info("-" * 60)

        mine_components, settlement_gdf, forest_gdf, water_gdf, full_gdf = load_clean_year(yr)

        # 1. Component Distances
        dist_df = compute_component_distances(mine_components, settlement_gdf, forest_gdf, water_gdf, yr)
        dist_csv = COMPONENTS_DIR / f"proximity_components_clean_{yr}.csv"
        dist_df.to_csv(dist_csv, index=False)

        # 2. Buffer Exposure
        exp_df = compute_buffer_exposure(mine_components, settlement_gdf, forest_gdf, water_gdf, yr)
        exp_csv = BUFFERS_DIR / f"buffer_exposure_clean_{yr}.csv"
        exp_df.to_csv(exp_csv, index=False)
        all_buffers_list.append(exp_df)

        # 3. Class Areas
        for cid, (cname, _) in COLORS.items():
            c_ha = full_gdf[full_gdf["class_id"] == cid]["area_ha"].sum()
            all_areas_list.append({"year": yr, "class_id": cid, "class_name": cname, "area_ha": round(c_ha, 2)})

        # 4. GIS Map
        map_path = MAPS_DIR / f"clean_gis_map_{yr}.png"
        plot_gis_map(full_gdf, mine_components, yr, map_path)
        log.info("Saved GIS map -> %s", map_path)

        # Summary Metrics Row
        total_mine_bare_ha = full_gdf[full_gdf["class_id"] == 0]["area_ha"].sum()
        row = {
            "year": yr,
            "component_count": len(mine_components),
            "mine_bare_total_ha": round(total_mine_bare_ha, 2),
            "settlement_total_ha": round(settlement_gdf["area_ha"].sum(), 2),
            "forest_total_ha": round(forest_gdf["area_ha"].sum(), 2),
            "water_total_ha": round(water_gdf["area_ha"].sum(), 2),
            "total_aoi_ha": round(full_gdf["area_ha"].sum(), 2),
            "dist_settlement_min_m": dist_df["dist_settlement_m"].min(),
            "dist_settlement_mean_m": round(dist_df["dist_settlement_m"].mean(), 2),
            "dist_settlement_median_m": dist_df["dist_settlement_m"].median(),
            "dist_forest_min_m": dist_df["dist_forest_m"].min(),
            "dist_forest_mean_m": round(dist_df["dist_forest_m"].mean(), 2),
            "dist_forest_median_m": dist_df["dist_forest_m"].median(),
            "dist_water_min_m": dist_df["dist_water_m"].min(),
            "dist_water_mean_m": round(dist_df["dist_water_m"].mean(), 2),
            "dist_water_median_m": dist_df["dist_water_m"].median(),
        }
        all_summary_rows.append(row)

    # Combine Tables
    summary_df = pd.DataFrame(all_summary_rows)
    all_buffers_df = pd.concat(all_buffers_list, ignore_index=True)
    all_areas_df = pd.DataFrame(all_areas_list)

    summary_csv = OUTPUT_BASE / "proximity_clean_summary.csv"
    summary_json = OUTPUT_BASE / "proximity_clean_summary.json"
    summary_df.to_csv(summary_csv, index=False)

    with open(summary_json, "w", encoding="utf-8") as f:
        json.dump(all_summary_rows, f, indent=2)

    log.info("Saved multi-year summary CSV -> %s", summary_csv)
    log.info("Saved multi-year summary JSON -> %s", summary_json)

    # 5. Generate Multi-Year Charts
    generate_six_year_charts(summary_df, all_buffers_df, all_areas_df)
    log.info("Saved 4 comparison charts in %s", CHARTS_DIR)

    print("\n" + "=" * 70)
    print("  SIX-YEAR CLEAN RF PROXIMITY ANALYSIS COMPLETED")
    print("=" * 70)
    print(summary_df[["year", "mine_bare_total_ha", "dist_water_min_m", "dist_water_median_m", "dist_water_mean_m"]].to_string(index=False))
    print("=" * 70)


if __name__ == "__main__":
    main()
