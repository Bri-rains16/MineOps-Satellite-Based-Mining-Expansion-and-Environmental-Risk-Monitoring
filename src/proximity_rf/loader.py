"""
src/proximity_rf/loader.py
--------------------------
Safely load and validate multi-class GeoJSON outputs from the Random Forest pipeline.
Reprojects to EPSG:32643 and repairs geometries.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Tuple

import geopandas as gpd
from shapely.validation import make_valid

log = logging.getLogger(__name__)

# Check renamed folder first, fallback to original if needed
RF_POLYGONS_DIR = Path("outputs/polygons_2021") if Path("outputs/polygons_2021").exists() else Path("outputs/polygons")
TARGET_CRS = "EPSG:32643"

CLASS_LABELS = {
    0: "mine_bare",
    1: "settlement",
    2: "forest",
    3: "water"
}


def load_rf_year(year: int) -> Tuple[gpd.GeoDataFrame, Dict[str, gpd.GeoDataFrame]]:
    """
    Load outputs/polygons/zawar_all_classes_{year}.geojson.
    
    Returns:
        mine_bare_gdf: GeoDataFrame in EPSG:32643 containing Class 0 (Mine/Bare land).
        env_dict: Dict with keys 'settlement', 'forest', 'water' mapping to EPSG:32643 GeoDataFrames.
    
    Raises:
        FileNotFoundError: If the year's GeoJSON is missing.
    """
    file_path = RF_POLYGONS_DIR / f"zawar_all_classes_{year}.geojson"
    if not file_path.exists():
        raise FileNotFoundError(f"Random Forest classification file not found: {file_path}")

    gdf = gpd.read_file(file_path)
    log.info("Loaded %d features from %s", len(gdf), file_path)

    # Reproject to metric CRS for accurate distance and area calculations
    if gdf.crs != TARGET_CRS:
        gdf = gdf.to_crs(TARGET_CRS)

    # Validate and repair all geometries
    gdf["geometry"] = gdf["geometry"].apply(make_valid)
    gdf = gdf[~gdf["geometry"].is_empty & gdf["geometry"].notna()].reset_index(drop=True)

    # Calculate individual polygon area in hectares
    gdf["area_ha"] = (gdf.geometry.area / 10000.0).round(4)

    # Split into reference (Class 0) and environmental classes (Classes 1, 2, 3)
    mine_bare_gdf = gdf[gdf["class_id"] == 0].copy().reset_index(drop=True)
    mine_bare_gdf["component_id"] = [f"RF_MB_{year}_{i+1:03d}" for i in range(len(mine_bare_gdf))]
    mine_bare_gdf["category"] = "Mine/Bare Land"

    env_dict = {
        "settlement": gdf[gdf["class_id"] == 1].copy().reset_index(drop=True),
        "forest": gdf[gdf["class_id"] == 2].copy().reset_index(drop=True),
        "water": gdf[gdf["class_id"] == 3].copy().reset_index(drop=True),
    }

    log.info(
        "Year %d: %d Mine/Bare (%.2f ha), %d Settlement (%.2f ha), %d Forest (%.2f ha), %d Water (%.2f ha)",
        year,
        len(mine_bare_gdf), mine_bare_gdf["area_ha"].sum(),
        len(env_dict["settlement"]), env_dict["settlement"]["area_ha"].sum(),
        len(env_dict["forest"]), env_dict["forest"]["area_ha"].sum(),
        len(env_dict["water"]), env_dict["water"]["area_ha"].sum(),
    )

    return mine_bare_gdf, env_dict
