"""
Vectorizer for MineOps Proximity Module:
- Connected-component labeling on mining rasters
- Area threshold filtering
- Rasterio polygonization preserving exact CRS and georeferencing
- Environmental feature polygonization
"""

import logging
import numpy as np
import geopandas as gpd
from shapely.geometry import shape, MultiPolygon, Polygon
from shapely.validation import make_valid
from scipy.ndimage import label, generate_binary_structure
import rasterio.features
from typing import Dict, Optional

logger = logging.getLogger("MineOps.Proximity.Vectorizer")

def polygonize_binary_mask(
    mask: np.ndarray,
    transform: rasterio.Affine,
    crs: str = "EPSG:32643",
    min_area_m2: float = 100.0,
    class_name: str = "feature",
    year: int = 2021
) -> gpd.GeoDataFrame:
    """
    Polygonize a binary mask (e.g., water, settlement, forest) into a GeoDataFrame.
    Applies minimal area thresholding and validates geometries.
    """
    if mask.sum() == 0:
        return gpd.GeoDataFrame(
            columns=["feature_id", "class_name", "year", "area_m2", "area_ha", "geometry"],
            crs=crs
        )
        
    shapes_gen = rasterio.features.shapes(
        mask.astype(np.int32),
        mask=(mask == 1),
        transform=transform,
        connectivity=8
    )
    
    records = []
    idx = 1
    for geom_dict, val in shapes_gen:
        if val != 1:
            continue
        geom = make_valid(shape(geom_dict))
        if geom.is_empty:
            continue
            
        area_m2 = geom.area
        if area_m2 < min_area_m2:
            continue
            
        records.append({
            "feature_id": f"{class_name.upper()[:3]}_{year}_{idx:04d}",
            "class_name": class_name,
            "year": year,
            "area_m2": round(area_m2, 2),
            "area_ha": round(area_m2 / 10000.0, 4),
            "geometry": geom
        })
        idx += 1
        
    gdf = gpd.GeoDataFrame(records, crs=crs)
    return gdf

def polygonize_mining_components(
    mining_mask: np.ndarray,
    transform: rasterio.Affine,
    crs: str = "EPSG:32643",
    year: int = 2021,
    min_area_m2: float = 1000.0,
    prefix: str = "M"
) -> gpd.GeoDataFrame:
    """
    Perform connected component labeling on mining mask, filter small components,
    and convert to individual polygon features with unique component IDs.
    """
    if mining_mask.sum() == 0:
        logger.warning(f"Empty mining mask for year {year} ({prefix})")
        return gpd.GeoDataFrame(
            columns=["component_id", "year", "pixel_count", "area_m2", "area_ha", "geometry"],
            crs=crs
        )
        
    # 8-connectivity structure
    structure = generate_binary_structure(2, 2)
    labeled_array, num_features = label(mining_mask, structure=structure)
    
    logger.info(f"Year {year} ({prefix}): Identified {num_features} connected components before area filtering.")
    
    # Calculate pixel counts per component
    component_ids, counts = np.unique(labeled_array, return_counts=True)
    valid_components = set()
    pixel_area_m2 = abs(transform.a * transform.e) # e.g. 10 * 10 = 100 m^2
    
    for cid, cnt in zip(component_ids, counts):
        if cid == 0:
            continue
        area_m2 = cnt * pixel_area_m2
        if area_m2 >= min_area_m2:
            valid_components.add(cid)
            
    logger.info(f"Year {year} ({prefix}): {len(valid_components)} components meet the {min_area_m2} m² threshold.")
    
    if not valid_components:
        return gpd.GeoDataFrame(
            columns=["component_id", "year", "pixel_count", "area_m2", "area_ha", "geometry"],
            crs=crs
        )
        
    # Mask out invalid components
    filtered_labeled = np.where(np.isin(labeled_array, list(valid_components)), labeled_array, 0).astype(np.int32)
    
    shapes_gen = rasterio.features.shapes(
        filtered_labeled,
        mask=(filtered_labeled > 0),
        transform=transform,
        connectivity=8
    )
    
    records = []
    # Collect shapes by component ID (in case rasterio returns multi-parts)
    comp_geoms: Dict[int, list] = {}
    for geom_dict, cid_val in shapes_gen:
        cid = int(cid_val)
        if cid <= 0:
            continue
        geom = make_valid(shape(geom_dict))
        if not geom.is_empty:
            comp_geoms.setdefault(cid, []).append(geom)
            
    seq = 1
    for cid, geoms in comp_geoms.items():
        if len(geoms) == 1:
            poly_geom = geoms[0]
        else:
            poly_geom = make_valid(MultiPolygon([g for g in geoms if isinstance(g, Polygon)]))
            
        if poly_geom.is_empty:
            continue
            
        area_m2 = poly_geom.area
        pixel_count = int(np.sum(labeled_array == cid))
        
        records.append({
            "component_id": f"{prefix}_{year}_{seq:03d}",
            "year": year,
            "pixel_count": pixel_count,
            "area_m2": round(area_m2, 2),
            "area_ha": round(area_m2 / 10000.0, 4),
            "geometry": poly_geom
        })
        seq += 1
        
    gdf = gpd.GeoDataFrame(records, crs=crs)
    logger.info(f"Year {year} ({prefix}): Generated {len(gdf)} valid polygonized components.")
    return gdf
