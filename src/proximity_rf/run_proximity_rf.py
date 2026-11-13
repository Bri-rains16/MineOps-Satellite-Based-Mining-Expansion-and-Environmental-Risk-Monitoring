"""
src/proximity_rf/run_proximity_rf.py
------------------------------------
Main execution entry point for the Random Forest proximity analysis module.

Usage:
    python -m src.proximity_rf.run_proximity_rf
    python -m src.proximity_rf.run_proximity_rf --year 2021
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
import sys
from typing import List

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("proximity_rf")

from src.proximity_rf.loader import load_rf_year
from src.proximity_rf.metrics import (
    compute_component_distances,
    compute_buffer_exposure,
    compute_class_areas
)
from src.proximity_rf.visualizer import plot_gis_map, plot_charts

OUTPUT_BASE = Path("outputs/proximity_rf")
COMPONENTS_DIR = OUTPUT_BASE / "components"
BUFFERS_DIR = OUTPUT_BASE / "buffer_exposure"
CHARTS_DIR = OUTPUT_BASE / "charts"
GIS_DIR = OUTPUT_BASE / "maps"
GEOJSON_OUT_DIR = OUTPUT_BASE / "geojson"


def run_year(year: int) -> dict:
    """Processes proximity and buffer exposure for a single year using RF GeoJSON."""
    log.info("=" * 65)
    log.info("Processing Random Forest Proximity Analysis for Year %d", year)
    log.info("=" * 65)

    # 1. Load data
    mine_bare_gdf, env_dict = load_rf_year(year)

    # 2. Export extracted reference polygons as GeoJSON in EPSG:4326 for standard GIS interchange
    GEOJSON_OUT_DIR.mkdir(parents=True, exist_ok=True)
    mine_bare_out_4326 = mine_bare_gdf.to_crs("EPSG:4326")
    mine_bare_path = GEOJSON_OUT_DIR / f"rf_mine_bare_{year}.geojson"
    mine_bare_out_4326.to_file(mine_bare_path, driver="GeoJSON")
    log.info("Saved reference mine/bare polygons -> %s", mine_bare_path)

    # 3. Compute component distances
    dist_df = compute_component_distances(mine_bare_gdf, env_dict, year)
    COMPONENTS_DIR.mkdir(parents=True, exist_ok=True)
    dist_csv = COMPONENTS_DIR / f"rf_proximity_components_{year}.csv"
    dist_df.to_csv(dist_csv, index=False)
    log.info("Saved component distance metrics -> %s", dist_csv)

    # 4. Compute buffer exposure
    exposure_df = compute_buffer_exposure(mine_bare_gdf, env_dict, year)
    BUFFERS_DIR.mkdir(parents=True, exist_ok=True)
    exposure_csv = BUFFERS_DIR / f"rf_buffer_exposure_{year}.csv"
    exposure_df.to_csv(exposure_csv, index=False)
    log.info("Saved buffer exposure metrics -> %s", exposure_csv)

    # 5. Compute class areas
    areas_df = compute_class_areas(mine_bare_gdf, env_dict, year)

    # 6. Generate visual outputs (GIS Map and Charts)
    gis_map_path = GIS_DIR / f"rf_proximity_gis_map_{year}.png"
    plot_gis_map(mine_bare_gdf, env_dict, year, gis_map_path)
    plot_charts(dist_df, exposure_df, year, CHARTS_DIR)

    # 7. Build summary dictionary
    year_summary = {
        "year": year,
        "input_source": f"outputs/polygons/zawar_all_classes_{year}.geojson",
        "reference_class": "Class 0: Mine/Bare Land (unvegetated surfaces, pits, waste rock, outcrops)",
        "component_count": len(mine_bare_gdf),
        "total_mine_bare_area_ha": round(mine_bare_gdf["area_ha"].sum(), 2),
        "distance_metrics_metres": {
            "to_settlement": {
                "min": float(dist_df["dist_settlement_m"].min()),
                "median": float(dist_df["dist_settlement_m"].median()),
                "mean": round(float(dist_df["dist_settlement_m"].mean()), 2),
            },
            "to_forest": {
                "min": float(dist_df["dist_forest_m"].min()),
                "median": float(dist_df["dist_forest_m"].median()),
                "mean": round(float(dist_df["dist_forest_m"].mean()), 2),
            },
            "to_water": {
                "min": float(dist_df["dist_water_m"].min()),
                "median": float(dist_df["dist_water_m"].median()),
                "mean": round(float(dist_df["dist_water_m"].mean()), 2),
            }
        },
        "buffer_exposure": exposure_df.to_dict(orient="records"),
        "landscape_areas": areas_df.to_dict(orient="records")
    }

    return year_summary


def main():
    parser = argparse.ArgumentParser(description="MineOps Random Forest Proximity Analysis")
    parser.add_argument("--year", type=int, default=2021, help="Year to process (defaults to 2021)")
    args = parser.parse_args()

    # Target years to check
    years_to_process = [args.year] if args.year else [2021]

    all_summaries = []
    for yr in years_to_process:
        try:
            summary = run_year(yr)
            all_summaries.append(summary)
        except FileNotFoundError as e:
            log.warning("Skipping year %d: %s", yr, e)
        except Exception as e:
            log.exception("Error processing year %d: %s", yr, e)

    if not all_summaries:
        log.error("No data processed. Please check input files.")
        sys.exit(1)

    # Save summary JSON
    OUTPUT_BASE.mkdir(parents=True, exist_ok=True)
    summary_json_path = OUTPUT_BASE / "rf_proximity_summary.json"
    with open(summary_json_path, "w", encoding="utf-8") as f:
        json.dump(all_summaries, f, indent=2)
    log.info("Saved combined summary JSON -> %s", summary_json_path)

    # Save summary CSV
    summary_rows = []
    for s in all_summaries:
        row = {
            "year": s["year"],
            "component_count": s["component_count"],
            "mine_bare_area_ha": s["total_mine_bare_area_ha"],
            "dist_settlement_min_m": s["distance_metrics_metres"]["to_settlement"]["min"],
            "dist_settlement_median_m": s["distance_metrics_metres"]["to_settlement"]["median"],
            "dist_forest_min_m": s["distance_metrics_metres"]["to_forest"]["min"],
            "dist_forest_median_m": s["distance_metrics_metres"]["to_forest"]["median"],
            "dist_water_min_m": s["distance_metrics_metres"]["to_water"]["min"],
            "dist_water_median_m": s["distance_metrics_metres"]["to_water"]["median"],
        }
        summary_rows.append(row)

    summary_csv_path = OUTPUT_BASE / "rf_proximity_summary.csv"
    pd.DataFrame(summary_rows).to_csv(summary_csv_path, index=False)
    log.info("Saved combined summary CSV -> %s", summary_csv_path)

    print("\n" + "=" * 65)
    print("  RANDOM FOREST PROXIMITY ANALYSIS COMPLETED")
    print("=" * 65)
    print(f"  Processed Year(s)        : {[s['year'] for s in all_summaries]}")
    print(f"  Summary JSON             : {summary_json_path}")
    print(f"  Summary CSV              : {summary_csv_path}")
    print(f"  Component Metrics        : {COMPONENTS_DIR}")
    print(f"  Buffer Exposure Metrics  : {BUFFERS_DIR}")
    print(f"  Charts                   : {CHARTS_DIR}")
    print(f"  GIS Maps                 : {GIS_DIR}")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
