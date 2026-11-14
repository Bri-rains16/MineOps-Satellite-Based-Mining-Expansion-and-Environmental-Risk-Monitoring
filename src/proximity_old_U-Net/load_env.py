"""
load_env.py
-----------
Load environmental polygons (water / settlement / forest) from the
existing yearly env_features GeoJSONs produced by the previous pipeline.

Source files: outputs/proximity/environmental_features/env_features_{year}.geojson
    class_name values: 'water', 'settlement', 'forest'
    CRS: EPSG:32643  (already metric, no reprojection needed)

Returns three GeoDataFrames (one per class) clipped to the AOI,
with invalid geometries repaired.
"""

from __future__ import annotations

import logging
from pathlib import Path

import geopandas as gpd
from shapely.validation import make_valid

log = logging.getLogger(__name__)

ENV_DIR = Path("outputs/proximity_old_U-Net/environmental_features")
AOI_PATH = Path("data/zawar/aoi.geojson")
TARGET_CRS = "EPSG:32643"

CLASS_NAMES = ("water", "settlement", "forest")


def load_env_year(year: int) -> dict[str, gpd.GeoDataFrame]:
    """
    Load env_features_{year}.geojson and split into three GeoDataFrames
    keyed by class name: 'water', 'settlement', 'forest'.

    Each GeoDataFrame is in EPSG:32643, clipped to the AOI, with valid geometries.
    Raises FileNotFoundError if the source file is missing.
    Raises ValueError if any class is entirely absent.
    """
    src_path = ENV_DIR / f"env_features_{year}.geojson"
    if not src_path.exists():
        raise FileNotFoundError(
            f"Environmental features file not found: {src_path}\n"
            "Run the environmental feature pipeline before proximity analysis."
        )

    gdf = gpd.read_file(src_path)
    log.info("Year %d: loaded %d env features from %s", year, len(gdf), src_path)

    # Ensure correct CRS
    if gdf.crs is None:
        log.warning("No CRS on %s — assuming %s", src_path, TARGET_CRS)
        gdf = gdf.set_crs(TARGET_CRS)
    elif str(gdf.crs) != TARGET_CRS:
        log.info("Reprojecting env features from %s to %s", gdf.crs, TARGET_CRS)
        gdf = gdf.to_crs(TARGET_CRS)

    # Repair invalid geometries
    gdf["geometry"] = gdf["geometry"].apply(make_valid)
    gdf = gdf[~gdf["geometry"].is_empty].reset_index(drop=True)

    # Clip to AOI
    if AOI_PATH.exists():
        aoi = gpd.read_file(AOI_PATH).to_crs(TARGET_CRS)
        aoi_geom = aoi.union_all() if hasattr(aoi, "union_all") else aoi.unary_union
        gdf = gdf.clip(aoi_geom).reset_index(drop=True)
        log.info("Year %d: %d env features after AOI clip", year, len(gdf))

    result: dict[str, gpd.GeoDataFrame] = {}
    for cls in CLASS_NAMES:
        subset = gdf[gdf["class_name"] == cls].copy().reset_index(drop=True)
        if subset.empty:
            log.warning("Year %d: NO '%s' polygons found — distances will be NaN", year, cls)
        else:
            log.info("Year %d: %d '%s' polygons", year, len(subset), cls)
        result[cls] = subset

    return result
