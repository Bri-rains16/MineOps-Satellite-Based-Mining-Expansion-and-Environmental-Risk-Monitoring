"""
run_proximity.py
----------------
Entry point for the simple polygon-based proximity analysis.

Usage:
    python -m src.proximity.run_proximity             # all years 2021-2026
    python -m src.proximity.run_proximity --year 2021 # single year prototype

Pipeline per year:
  1. Vectorize U-Net mining raster → mining polygons (GeoJSON)
  2. Load environmental polygons from env_features GeoJSON
  3. Compute boundary-to-boundary distances for each mining polygon
  4. Save per-year metrics CSV

After all years:
  5. Merge into proximity_summary.csv
  6. Print annual summary statistics
  7. Generate 3 line charts
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

# Configure logging before any local imports
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("proximity")

from .vectorize_mining import vectorize_year
from .load_env import load_env_year
from .compute_distances import compute_distances_year
from .make_charts import make_charts

YEARS = list(range(2021, 2027))
METRICS_DIR = Path("outputs/proximity_old_U-Net/annual_metrics")
SUMMARY_CSV  = Path("outputs/proximity_old_U-Net/proximity_summary.csv")


def run_one_year(year: int) -> pd.DataFrame:
    """Full pipeline for a single year. Returns the per-component DataFrame."""
    log.info("=" * 60)
    log.info("Processing year %d", year)
    log.info("=" * 60)

    # Step 1 — vectorize mining raster
    mine_gdf = vectorize_year(year)
    log.info("  Mining polygons: %d  (total %.2f ha)", len(mine_gdf), mine_gdf["area_ha"].sum())

    # Step 2 — load environmental polygons
    env_by_class = load_env_year(year)
    for cls, gdf in env_by_class.items():
        log.info("  Env class '%s': %d polygons", cls, len(gdf))

    # Step 3 — compute distances
    df = compute_distances_year(mine_gdf, env_by_class, year)

    # Step 4 — save per-year CSV
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    out_csv = METRICS_DIR / f"proximity_metrics_{year}.csv"
    df.to_csv(out_csv, index=False)
    log.info("  Saved per-year metrics → %s", out_csv)

    # Print summary statistics for this year
    _print_year_summary(year, df)

    return df


def _print_year_summary(year: int, df: pd.DataFrame) -> None:
    """Print min/mean/median distances for a year."""
    print(f"\n{'='*55}")
    print(f"  Year {year} — Proximity Summary")
    print(f"{'='*55}")
    print(f"  Mining components : {len(df)}")
    print(f"  Total area        : {df['area_ha'].sum():.2f} ha")
    print()
    for col, label in [
        ("dist_water_m",      "Water      "),
        ("dist_settlement_m", "Settlement "),
        ("dist_forest_m",     "Forest     "),
    ]:
        s = df[col]
        if s.isna().all():
            print(f"  {label}: NO DATA")
        else:
            print(
                f"  {label}: "
                f"min={s.min():.0f} m  "
                f"median={s.median():.0f} m  "
                f"mean={s.mean():.0f} m"
            )
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="MineOps Proximity Analysis")
    parser.add_argument(
        "--year", type=int, default=None,
        help="Process a single year only (e.g. 2021). Omit for all years 2021-2026.",
    )
    args = parser.parse_args()

    years = [args.year] if args.year else YEARS

    all_dfs: list[pd.DataFrame] = []
    for year in years:
        try:
            df = run_one_year(year)
            all_dfs.append(df)
        except FileNotFoundError as exc:
            log.error("MISSING INPUT for year %d: %s", year, exc)
            log.error("Skipping year %d — resolve missing files and re-run.", year)
            continue
        except Exception as exc:
            log.exception("Unexpected error for year %d: %s", year, exc)
            continue

    if not all_dfs:
        log.error("No years processed successfully. Exiting.")
        sys.exit(1)

    # Merge all years
    summary = pd.concat(all_dfs, ignore_index=True)
    SUMMARY_CSV.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(SUMMARY_CSV, index=False)
    log.info("Merged proximity_summary.csv → %s  (%d rows)", SUMMARY_CSV, len(summary))

    # Annual aggregated stats table
    agg = (
        summary.groupby("year")[["dist_water_m", "dist_settlement_m", "dist_forest_m"]]
        .agg(["min", "mean", "median"])
        .round(1)
    )
    print("\n=== Annual Summary Statistics ===")
    print(agg.to_string())
    print()

    # Charts only make sense if we have multiple years
    if len(all_dfs) > 1:
        make_charts(summary)
        log.info("Charts saved to outputs/proximity_old_U-Net/charts/")
    else:
        log.info("Single-year run — skipping chart generation (needs multiple years).")

    log.info("Proximity analysis complete.")


if __name__ == "__main__":
    main()
