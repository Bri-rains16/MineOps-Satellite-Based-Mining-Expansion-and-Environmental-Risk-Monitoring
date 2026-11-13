"""
compute_distances.py
--------------------
Compute boundary-to-boundary nearest distances between mining polygons
and environmental polygons (water / settlement / forest).

Algorithm:
  For each mining polygon M:
    For each env class C:
      1. Use STRtree on C to find the nearest env polygon E.
      2. Distance = M.boundary.distance(E.boundary)
         (or 0.0 if M and E intersect / overlap)

All geometries must be in EPSG:32643 (metres).

Output: pandas DataFrame with columns:
    year, component_id, area_ha,
    dist_water_m, dist_settlement_m, dist_forest_m
"""

from __future__ import annotations

import logging
from typing import Optional

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely import STRtree

log = logging.getLogger(__name__)


def _nearest_distance(mine_geom, env_gdf: gpd.GeoDataFrame) -> float:
    """
    Return the boundary-to-boundary distance (metres) from mine_geom
    to the nearest polygon in env_gdf.

    Returns NaN if env_gdf is empty.
    Returns 0.0 if any polygon intersects or overlaps mine_geom.
    """
    if env_gdf.empty:
        return float("nan")

    env_geoms = list(env_gdf.geometry)
    tree = STRtree(env_geoms)

    # Find the index of the nearest geometry by centroid distance first (fast)
    idx = tree.nearest(mine_geom)
    nearest_geom = env_geoms[idx]

    # Check intersection
    if mine_geom.intersects(nearest_geom):
        return 0.0

    # Boundary-to-boundary distance
    dist = mine_geom.boundary.distance(nearest_geom.boundary)
    return round(float(dist), 2)


def compute_distances_year(
    mine_gdf: gpd.GeoDataFrame,
    env_by_class: dict[str, gpd.GeoDataFrame],
    year: int,
) -> pd.DataFrame:
    """
    Compute proximity metrics for one year.

    Parameters
    ----------
    mine_gdf : GeoDataFrame of mining polygons (EPSG:32643)
        Required columns: component_id, area_ha, geometry
    env_by_class : dict mapping class name → GeoDataFrame (EPSG:32643)
        Keys: 'water', 'settlement', 'forest'
    year : int

    Returns
    -------
    DataFrame with one row per mining polygon.
    """
    records = []
    for _, row in mine_gdf.iterrows():
        mine_geom = row.geometry

        dist_water      = _nearest_distance(mine_geom, env_by_class.get("water",      gpd.GeoDataFrame()))
        dist_settlement = _nearest_distance(mine_geom, env_by_class.get("settlement", gpd.GeoDataFrame()))
        dist_forest     = _nearest_distance(mine_geom, env_by_class.get("forest",     gpd.GeoDataFrame()))

        records.append({
            "year":              year,
            "component_id":      row["component_id"],
            "area_ha":           row["area_ha"],
            "dist_water_m":      dist_water,
            "dist_settlement_m": dist_settlement,
            "dist_forest_m":     dist_forest,
        })

    df = pd.DataFrame(records)
    log.info(
        "Year %d: %d mining polygons | "
        "water min=%.0f m | settlement min=%.0f m | forest min=%.0f m",
        year, len(df),
        df["dist_water_m"].min(),
        df["dist_settlement_m"].min(),
        df["dist_forest_m"].min(),
    )
    return df
