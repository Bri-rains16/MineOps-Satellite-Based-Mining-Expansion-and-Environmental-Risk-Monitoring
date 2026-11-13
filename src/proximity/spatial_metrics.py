"""
Spatial proximity and exposure metrics for MineOps:
- Boundary-to-boundary Euclidean distance calculation via STRtree spatial index
- Component-level measurements and annual distribution statistics
- Dissolved buffer exposure analysis (100m, 250m, 500m, 1000m)
"""

import logging
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.strtree import STRtree
from shapely.ops import unary_union
from typing import Dict, List, Tuple, Any

logger = logging.getLogger("MineOps.Proximity.SpatialMetrics")

def calculate_boundary_distances(
    mine_gdf: gpd.GeoDataFrame,
    env_gdfs: Dict[str, gpd.GeoDataFrame]
) -> gpd.GeoDataFrame:
    """
    Calculate the exact minimum boundary-to-boundary Euclidean distance in metres
    from each mining component to the nearest environmental feature geometry
    using shapely.STRtree spatial indexing.
    """
    res_gdf = mine_gdf.copy()
    if res_gdf.empty:
        for cat in ["water", "settlement", "forest"]:
            res_gdf[f"dist_{cat}_m"] = []
        return res_gdf

    for cat_name, env_gdf in env_gdfs.items():
        col_name = f"dist_{cat_name}_m"
        if env_gdf.empty:
            logger.warning(f"Environmental layer '{cat_name}' is empty. Setting distances to NaN.")
            res_gdf[col_name] = np.nan
            continue
            
        env_geoms = [g for g in env_gdf.geometry if not g.is_empty]
        if not env_geoms:
            res_gdf[col_name] = np.nan
            continue
            
        tree = STRtree(env_geoms)
        distances = []
        
        for mine_geom in res_gdf.geometry:
            if mine_geom.is_empty:
                distances.append(np.nan)
                continue
                
            # Query nearest geometry in tree
            nearest_idx = tree.nearest(mine_geom)
            # STRtree.nearest can return an integer index or geometry object depending on shapely version
            if isinstance(nearest_idx, (int, np.integer)):
                nearest_geom = env_geoms[nearest_idx]
            else:
                nearest_geom = nearest_idx
                
            # Exact boundary-to-boundary distance in meters (0.0 if overlapping or touching)
            d = mine_geom.distance(nearest_geom)
            distances.append(round(float(d), 2))
            
        res_gdf[col_name] = distances
        
    return res_gdf

def compute_summary_statistics(
    components_gdf: gpd.GeoDataFrame,
    year: int,
    footprint_type: str = "total"
) -> Dict[str, Any]:
    """
    Compute distribution summary statistics (min, 25th, median, mean, 75th, std)
    for distances to water, settlement, and forest across all mining components.
    """
    summary = {
        "year": year,
        "footprint_type": footprint_type,
        "component_count": len(components_gdf),
        "total_area_ha": round(float(components_gdf["area_ha"].sum()), 2) if not components_gdf.empty else 0.0
    }
    
    categories = ["water", "settlement", "forest"]
    for cat in categories:
        col = f"dist_{cat}_m"
        if col in components_gdf.columns and not components_gdf[col].dropna().empty:
            vals = components_gdf[col].dropna().values
            summary[f"{cat}_min_m"] = round(float(np.min(vals)), 2)
            summary[f"{cat}_p25_m"] = round(float(np.percentile(vals, 25)), 2)
            summary[f"{cat}_median_m"] = round(float(np.median(vals)), 2)
            summary[f"{cat}_mean_m"] = round(float(np.mean(vals)), 2)
            summary[f"{cat}_p75_m"] = round(float(np.percentile(vals, 75)), 2)
            summary[f"{cat}_std_m"] = round(float(np.std(vals)), 2)
        else:
            summary[f"{cat}_min_m"] = np.nan
            summary[f"{cat}_p25_m"] = np.nan
            summary[f"{cat}_median_m"] = np.nan
            summary[f"{cat}_mean_m"] = np.nan
            summary[f"{cat}_p75_m"] = np.nan
            summary[f"{cat}_std_m"] = np.nan
            
    return summary

def calculate_buffer_exposure(
    mine_gdf: gpd.GeoDataFrame,
    env_gdfs: Dict[str, gpd.GeoDataFrame],
    buffer_distances: List[int] = [100, 250, 500, 1000],
    year: int = 2021,
    footprint_type: str = "total"
) -> List[Dict[str, Any]]:
    """
    Calculate buffer exposure for water, settlement, and forest independently:
    1. Buffer environmental features by distance R.
    2. Dissolve overlapping buffers with unary_union so mining area is not double counted.
    3. Calculate geometric intersection with mining polygons.
    4. Compute exposure percentage: (intersected_area / total_area) * 100.
    """
    exposure_records = []
    total_mine_area_m2 = mine_gdf.geometry.area.sum() if not mine_gdf.empty else 0.0
    total_mine_area_ha = total_mine_area_m2 / 10000.0
    
    # Combined mining union geometry for fast intersection
    mine_union = unary_union(mine_gdf.geometry.values) if not mine_gdf.empty else None
    
    for cat_name, env_gdf in env_gdfs.items():
        if env_gdf.empty or mine_union is None or mine_union.is_empty:
            for dist in buffer_distances:
                exposure_records.append({
                    "year": year,
                    "footprint_type": footprint_type,
                    "category": cat_name,
                    "buffer_radius_m": dist,
                    "total_mine_area_ha": round(total_mine_area_ha, 2),
                    "exposed_area_ha": 0.0,
                    "exposure_pct": 0.0
                })
            continue
            
        env_geoms = [g for g in env_gdf.geometry if not g.is_empty]
        for dist in buffer_distances:
            # Buffer geometries
            buffered = [g.buffer(dist) for g in env_geoms]
            # Dissolve to eliminate overlapping area duplication
            dissolved_buffer = unary_union(buffered)
            
            # Intersection with mining footprint
            if dissolved_buffer.is_empty:
                inter_area_ha = 0.0
            else:
                inter_geom = mine_union.intersection(dissolved_buffer)
                inter_area_m2 = inter_geom.area if not inter_geom.is_empty else 0.0
                inter_area_ha = inter_area_m2 / 10000.0
                
            pct = (inter_area_ha / total_mine_area_ha * 100.0) if total_mine_area_ha > 0 else 0.0
            
            exposure_records.append({
                "year": year,
                "footprint_type": footprint_type,
                "category": cat_name,
                "buffer_radius_m": dist,
                "total_mine_area_ha": round(total_mine_area_ha, 2),
                "exposed_area_ha": round(inter_area_ha, 2),
                "exposure_pct": round(pct, 2)
            })
            
    return exposure_records
