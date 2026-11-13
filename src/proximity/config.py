"""
Configuration loader and validator for proximity analysis.
"""

import os
from dataclasses import dataclass, field
from typing import List, Tuple
from dotenv import load_dotenv
import yaml

load_dotenv()

@dataclass
class ProximityConfig:
    aoi_path: str = "data/zawar/aoi.geojson"
    years: List[int] = field(default_factory=lambda: [2021, 2022, 2023, 2024, 2025, 2026])
    season_window: Tuple[str, str] = ("02-01", "04-30")
    resolution: int = 10
    crs_area: str = "EPSG:32643"
    
    # Proximity parameters
    ee_project: str = os.getenv("GEE_PROJECT_ID", "major-project-1-508714")
    dynamic_world_dir: str = "data/zawar/dynamic_world"
    unet_maps_dir: str = "outputs/maps"
    output_dir: str = "outputs/proximity"
    min_component_area_m2: float = 1000.0
    noise_filter_kernel_size: int = 3
    dw_min_confidence: float = 0.35
    buffer_distances: List[int] = field(default_factory=lambda: [100, 250, 500, 1000])

def load_proximity_config(config_path: str = "config.yaml") -> ProximityConfig:
    """Load configuration from config.yaml with sensible defaults."""
    cfg = ProximityConfig()
    
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
            
        data_cfg = raw.get("data", {})
        if "aoi_path" in data_cfg:
            cfg.aoi_path = data_cfg["aoi_path"]
        if "years" in data_cfg:
            cfg.years = list(data_cfg["years"])
        if "season_window" in data_cfg:
            cfg.season_window = tuple(data_cfg["season_window"])
        if "resolution" in data_cfg:
            cfg.resolution = int(data_cfg["resolution"])
        if "crs_area" in data_cfg:
            cfg.crs_area = data_cfg["crs_area"]
            
        prox_cfg = raw.get("proximity", {})
        if "ee_project" in prox_cfg:
            cfg.ee_project = prox_cfg["ee_project"]
        if "dynamic_world_dir" in prox_cfg:
            cfg.dynamic_world_dir = prox_cfg["dynamic_world_dir"]
        if "unet_maps_dir" in prox_cfg:
            cfg.unet_maps_dir = prox_cfg["unet_maps_dir"]
        if "output_dir" in prox_cfg:
            cfg.output_dir = prox_cfg["output_dir"]
        if "min_component_area_m2" in prox_cfg:
            cfg.min_component_area_m2 = float(prox_cfg["min_component_area_m2"])
        if "noise_filter_kernel_size" in prox_cfg:
            cfg.noise_filter_kernel_size = int(prox_cfg["noise_filter_kernel_size"])
        if "dw_min_confidence" in prox_cfg:
            cfg.dw_min_confidence = float(prox_cfg["dw_min_confidence"])
        if "buffer_distances" in prox_cfg:
            cfg.buffer_distances = list(prox_cfg["buffer_distances"])
            
    return cfg
