"""
vectorize_mining.py
-------------------
Convert a binary U-Net prediction GeoTIFF into mining polygons.

Each connected component (8-connectivity) that is >= MIN_AREA_M2 becomes
one polygon.  Saves a GeoJSON to outputs/proximity/mining_polygons/.
"""

from __future__ import annotations

import logging
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import shapes
from scipy.ndimage import label
from shapely.geometry import shape
from shapely.validation import make_valid

log = logging.getLogger(__name__)

UNET_DIR = Path("outputs/maps")
OUT_DIR = Path("outputs/proximity_old_U-Net/mining_polygons")
MIN_AREA_M2 = 1_000          # drop components smaller than 0.1 ha
BINARY_THRESHOLD = 0.5


def vectorize_year(year: int) -> gpd.GeoDataFrame:
    """
    Load unet_pred_{year}.tif, polygonize connected mining components,
    and save to outputs/proximity/mining_polygons/mine_polygons_{year}.geojson.

    Returns a GeoDataFrame with columns:
        component_id, year, area_ha, geometry
    """
    tif_path = UNET_DIR / f"unet_pred_{year}.tif"
    if not tif_path.exists():
        raise FileNotFoundError(f"U-Net raster not found: {tif_path}")

    out_path = OUT_DIR / f"mine_polygons_{year}.geojson"
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with rasterio.open(tif_path) as src:
        crs = src.crs
        transform = src.transform
        pixel_area_m2 = abs(src.res[0] * src.res[1])   # e.g. 100 m² at 10 m res
        arr = src.read(1)

    # --- binary mask ---
    mask = (arr > BINARY_THRESHOLD).astype(np.int32)

    # --- label connected components (8-connectivity) ---
    struct = np.ones((3, 3), dtype=np.int32)
    labeled, n_components = label(mask, structure=struct)
    log.info("Year %d: %d connected components found before area filter", year, n_components)

    # --- build one polygon per component ---
    rows = []
    for comp_id in range(1, n_components + 1):
        comp_mask = (labeled == comp_id).astype(np.uint8)
        pixel_count = int(comp_mask.sum())
        area_m2 = pixel_count * pixel_area_m2

        if area_m2 < MIN_AREA_M2:
            continue   # skip noise

        # Polygonize the component mask
        polys = [
            shape(geom)
            for geom, val in shapes(comp_mask, transform=transform)
            if val == 1
        ]
        if not polys:
            continue

        # Dissolve all sub-shapes into one polygon
        from shapely.ops import unary_union
        geom = make_valid(unary_union(polys))

        rows.append({
            "component_id": f"M_{year}_{comp_id:03d}",
            "year": year,
            "area_ha": round(area_m2 / 10_000, 4),
            "geometry": geom,
        })

    if not rows:
        raise ValueError(f"No mining polygons >= {MIN_AREA_M2} m² found for year {year}")

    gdf = gpd.GeoDataFrame(rows, crs=crs)
    gdf.to_file(out_path, driver="GeoJSON")
    log.info(
        "Year %d: %d mining polygons saved → %s (total %.2f ha)",
        year, len(gdf), out_path, gdf["area_ha"].sum(),
    )
    return gdf
