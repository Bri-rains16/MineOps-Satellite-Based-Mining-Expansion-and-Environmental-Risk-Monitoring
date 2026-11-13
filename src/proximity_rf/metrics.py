"""
src/proximity_rf/metrics.py
---------------------------
Calculates:
1. Nearest boundary-to-boundary distance from each Mine/Bare polygon to environmental classes.
2. Buffer zone exposure analysis (250m, 500m, 1000m) around Mine/Bare areas.
3. Total area metrics per land-cover class.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Any

import geopandas as gpd
import pandas as pd
from shapely import STRtree
from shapely.validation import make_valid

log = logging.getLogger(__name__)

BUFFERS = [250, 500, 1000]


def _calc_min_distance(ref_geom, target_gdf: gpd.GeoDataFrame) -> float:
    """Calculate minimum distance from ref_geom to nearest polygon in target_gdf in metres."""
    if target_gdf.empty:
        return float("nan")

    geoms = list(target_gdf.geometry)
    tree = STRtree(geoms)
    nearest_idx = tree.nearest(ref_geom)
    nearest_geom = geoms[nearest_idx]

    if ref_geom.intersects(nearest_geom):
        return 0.0

    return round(float(ref_geom.distance(nearest_geom)), 2)


def compute_component_distances(
    mine_bare_gdf: gpd.GeoDataFrame,
    env_dict: Dict[str, gpd.GeoDataFrame],
    year: int
) -> pd.DataFrame:
    """
    Computes minimum distance from each Mine/Bare polygon to nearest settlement, forest, and water feature.
    """
    records: List[Dict[str, Any]] = []

    for _, row in mine_bare_gdf.iterrows():
        geom = row.geometry
        dist_settlement = _calc_min_distance(geom, env_dict.get("settlement", gpd.GeoDataFrame()))
        dist_forest = _calc_min_distance(geom, env_dict.get("forest", gpd.GeoDataFrame()))
        dist_water = _calc_min_distance(geom, env_dict.get("water", gpd.GeoDataFrame()))

        records.append({
            "year": year,
            "component_id": row["component_id"],
            "area_ha": row["area_ha"],
            "dist_settlement_m": dist_settlement,
            "dist_forest_m": dist_forest,
            "dist_water_m": dist_water,
            "note": "Class 0 represents Mine/Bare land (excavations, pits, tailings, or rocky outcrops)"
        })

    return pd.DataFrame(records)


def compute_buffer_exposure(
    mine_bare_gdf: gpd.GeoDataFrame,
    env_dict: Dict[str, gpd.GeoDataFrame],
    year: int
) -> pd.DataFrame:
    """
    Evaluates environmental land-cover areas exposed within 250m, 500m, and 1000m buffer zones
    around the aggregate Mine/Bare footprint.
    """
    if mine_bare_gdf.empty:
        return pd.DataFrame()

    # Union all mine/bare geometries into an aggregate boundary
    mine_union = mine_bare_gdf.geometry.union_all() if hasattr(mine_bare_gdf.geometry, "union_all") else mine_bare_gdf.geometry.unary_union
    mine_union = make_valid(mine_union)

    records: List[Dict[str, Any]] = []

    for buf_m in BUFFERS:
        buffer_geom = make_valid(mine_union.buffer(buf_m))

        row: Dict[str, Any] = {
            "year": year,
            "buffer_radius_m": buf_m,
            "buffer_total_area_ha": round(buffer_geom.area / 10000.0, 2)
        }

        for class_name, env_gdf in env_dict.items():
            if env_gdf.empty:
                row[f"{class_name}_exposed_ha"] = 0.0
                row[f"{class_name}_exposure_pct"] = 0.0
            else:
                total_class_area_ha = env_gdf["area_ha"].sum()
                clipped = env_gdf.clip(buffer_geom)
                exposed_ha = round(clipped.geometry.area.sum() / 10000.0, 2)
                pct = round((exposed_ha / total_class_area_ha * 100.0), 2) if total_class_area_ha > 0 else 0.0

                row[f"{class_name}_exposed_ha"] = exposed_ha
                row[f"{class_name}_exposure_pct"] = pct

        records.append(row)

    return pd.DataFrame(records)


def compute_class_areas(
    mine_bare_gdf: gpd.GeoDataFrame,
    env_dict: Dict[str, gpd.GeoDataFrame],
    year: int
) -> pd.DataFrame:
    """Computes total area in hectares and relative proportion for all 4 classes."""
    classes = [
        ("Mine/Bare Land (Class 0)", mine_bare_gdf["area_ha"].sum(), len(mine_bare_gdf)),
        ("Settlement (Class 1)", env_dict["settlement"]["area_ha"].sum(), len(env_dict["settlement"])),
        ("Forest/Vegetation (Class 2)", env_dict["forest"]["area_ha"].sum(), len(env_dict["forest"])),
        ("Water (Class 3)", env_dict["water"]["area_ha"].sum(), len(env_dict["water"])),
    ]

    total_landscape_ha = sum(area for _, area, _ in classes)

    rows = []
    for name, area_ha, count in classes:
        rows.append({
            "year": year,
            "class_name": name,
            "polygon_count": count,
            "area_ha": round(area_ha, 2),
            "percentage_of_aoi": round(area_ha / total_landscape_ha * 100.0, 2) if total_landscape_ha > 0 else 0.0
        })

    return pd.DataFrame(rows)
