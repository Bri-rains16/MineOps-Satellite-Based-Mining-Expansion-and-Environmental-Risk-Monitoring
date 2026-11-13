"""
Visualization module for MineOps Proximity Analysis:
- Graph 1: Annual Proximity Trend (Median & Minimum distances to Water, Settlement, Forest)
- Graph 2: Buffer Exposure Trend (Percentage of mining area within 250m, 500m, 1km)
- Graph 3: Newly Expanded Mining Proximity vs Total Footprint
- Graph 4: Annual Multi-Layer GIS Maps
"""

import os
import logging
import matplotlib
matplotlib.use("Agg")  # Thread-safe headless backend, prevents Tkinter multi-thread crash
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import geopandas as gpd
from typing import Dict, List, Optional
from shapely.ops import unary_union

logger = logging.getLogger("MineOps.Proximity.Visualizer")

# Set standard aesthetic styling
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#333333'
plt.rcParams['axes.linewidth'] = 0.8

def plot_annual_proximity_trend(
    summary_df: pd.DataFrame,
    out_dir: str
) -> str:
    """
    Graph 1: Annual Proximity Trend (2021-2026)
    Median nearest distance for Water, Settlement, Forest, with dashed min lines.
    """
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "proximity_trend_2021_2026.png")
    
    # Filter to total footprint records only
    df = summary_df[summary_df["footprint_type"] == "total"].sort_values("year")
    if df.empty:
        logger.warning("No total footprint summary data to plot.")
        return ""
        
    years = df["year"].values
    
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    
    colors = {
        "water": "#1f77b4",       # Solid blue
        "settlement": "#ff7f0e",  # Solid orange
        "forest": "#2ca02c"       # Solid green
    }
    
    markers = {"water": "o", "settlement": "s", "forest": "^"}
    
    for cat in ["water", "settlement", "forest"]:
        median_col = f"{cat}_median_m"
        min_col = f"{cat}_min_m"
        
        if median_col in df.columns:
            ax.plot(
                years, df[median_col],
                label=f"{cat.capitalize()} (Median)",
                color=colors[cat],
                marker=markers[cat],
                linewidth=2.5,
                markersize=8
            )
            # Add data callouts
            for y, val in zip(years, df[median_col]):
                if not np.isnan(val):
                    ax.annotate(f"{val:.0f}m", (y, val), textcoords="offset points", xytext=(0, 8),
                                ha='center', fontsize=9, fontweight='bold', color=colors[cat])
                                
        if min_col in df.columns:
            ax.plot(
                years, df[min_col],
                label=f"{cat.capitalize()} (Minimum)",
                color=colors[cat],
                linestyle="--",
                alpha=0.65,
                linewidth=1.5
            )

    ax.set_title("Zawar Mine Proximity to Environmental & Social Assets (2021–2026)", fontsize=13, fontweight='bold', pad=15)
    ax.set_xlabel("Year", fontsize=11, fontweight='bold')
    ax.set_ylabel("Boundary-to-Boundary Distance (metres)", fontsize=11, fontweight='bold')
    ax.set_xticks(years)
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="upper right", frameon=True, fontsize=9, ncol=2)
    
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
    logger.info(f"Graph 1 saved -> {out_path}")
    return out_path

def plot_buffer_exposure_trend(
    exposure_df: pd.DataFrame,
    out_dir: str
) -> str:
    """
    Graph 2: Buffer Exposure Trend
    Percentage of mining area within 250m, 500m, and 1km across years.
    """
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "buffer_exposure_trend.png")
    
    df = exposure_df[
        (exposure_df["footprint_type"] == "total") &
        (exposure_df["buffer_radius_m"].isin([250, 500, 1000]))
    ].copy()
    
    if df.empty:
        logger.warning("No buffer exposure data to plot.")
        return ""
        
    categories = ["water", "settlement", "forest"]
    fig, axes = plt.subplots(1, 3, figsize=(16, 5), dpi=300, sharey=True)
    
    radii_colors = {
        250: "#d9534f",   # High risk (red)
        500: "#f0ad4e",   # Medium risk (amber)
        1000: "#5bc0de"   # Moderate risk (cyan)
    }
    
    years = sorted(df["year"].unique())
    
    for i, cat in enumerate(categories):
        ax = axes[i]
        cat_df = df[df["category"] == cat]
        
        for radius in [250, 500, 1000]:
            r_data = cat_df[cat_df["buffer_radius_m"] == radius].sort_values("year")
            if not r_data.empty:
                ax.plot(
                    r_data["year"], r_data["exposure_pct"],
                    label=f"Within {radius}m",
                    color=radii_colors[radius],
                    marker="o",
                    linewidth=2.0,
                    markersize=6
                )
                for y, pct in zip(r_data["year"], r_data["exposure_pct"]):
                    if pct > 0:
                        ax.annotate(f"{pct:.1f}%", (y, pct), textcoords="offset points", xytext=(0, 6),
                                    ha='center', fontsize=8, color=radii_colors[radius], fontweight='semibold')
                                    
        ax.set_title(f"Exposure: {cat.capitalize()}", fontsize=12, fontweight='bold')
        ax.set_xlabel("Year", fontsize=10, fontweight='bold')
        ax.set_xticks(years)
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.set_ylim(-2, 105)
        if i == 0:
            ax.set_ylabel("Mining Area in Buffer (%)", fontsize=11, fontweight='bold')
        ax.legend(loc="upper left", fontsize=8)
        
    fig.suptitle("Zawar Mine Footprint Buffer Encroachment (2021–2026)", fontsize=14, fontweight='bold', y=0.98)
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
    logger.info(f"Graph 2 saved -> {out_path}")
    return out_path

def plot_expansion_proximity(
    summary_df: pd.DataFrame,
    out_dir: str
) -> str:
    """
    Graph 3: Newly Expanded Mining Proximity
    Compares median distance of newly detected mining patches vs total footprint.
    """
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "expansion_proximity_trend.png")
    
    new_df = summary_df[summary_df["footprint_type"] == "newly_expanded"].sort_values("year")
    tot_df = summary_df[summary_df["footprint_type"] == "total"].sort_values("year")
    
    if new_df.empty:
        logger.warning("No newly expanded footprint summary data to plot.")
        return ""
        
    years = new_df["year"].values
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 5), dpi=300)
    categories = ["water", "settlement", "forest"]
    cat_colors = {"water": "#1f77b4", "settlement": "#ff7f0e", "forest": "#2ca02c"}
    
    for i, cat in enumerate(categories):
        ax = axes[i]
        col = f"{cat}_median_m"
        
        # Plot newly expanded patches
        ax.plot(
            years, new_df[col],
            label="Newly Expanded Areas",
            color="#d9534f",
            marker="D",
            linewidth=2.5,
            markersize=7
        )
        for y, val in zip(years, new_df[col]):
            if not np.isnan(val):
                ax.annotate(f"{val:.0f}m", (y, val), textcoords="offset points", xytext=(0, 7),
                            ha='center', fontsize=8, fontweight='bold', color="#d9534f")
                            
        # Plot total baseline for comparison
        tot_sub = tot_df[tot_df["year"].isin(years)]
        if not tot_sub.empty and col in tot_sub.columns:
            ax.plot(
                tot_sub["year"], tot_sub[col],
                label="Total Footprint (Baseline)",
                color=cat_colors[cat],
                linestyle="--",
                marker="o",
                alpha=0.7,
                linewidth=1.8
            )
            
        ax.set_title(f"Proximity to {cat.capitalize()}", fontsize=12, fontweight='bold')
        ax.set_xlabel("Year", fontsize=10, fontweight='bold')
        ax.set_ylabel("Median Distance (m)", fontsize=10, fontweight='bold')
        ax.set_xticks(years)
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.legend(loc="upper right", fontsize=8)
        
    fig.suptitle("Newly Detected Mining Footprint Proximity Trajectory", fontsize=13, fontweight='bold', y=0.98)
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
    logger.info(f"Graph 3 saved -> {out_path}")
    return out_path

def generate_annual_gis_map(
    year: int,
    mine_gdf: gpd.GeoDataFrame,
    env_gdfs: Dict[str, gpd.GeoDataFrame],
    out_dir: str,
    exp_gdf: Optional[gpd.GeoDataFrame] = None,
    buffer_radius_m: int = 500
) -> str:
    """
    Graph 4: Annual GIS Map with Dual-Panel Visualization:
    - Left Panel: Regional Context (85 km² study area with 500m buffer zones)
    - Right Panel: High-Resolution Zoom Inset on Active Mining Pits (Mochia, Balaria, Zawarmala)
      highlighting baseline vs newly expanded mining footprint with metrics callout.
    """
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"gis_map_{year}.png")
    
    fig, (ax_main, ax_zoom) = plt.subplots(1, 2, figsize=(18, 9), dpi=300)
    
    # ----------------------------------------------------
    # Helper to plot base environmental layers
    # ----------------------------------------------------
    def plot_layers(ax, show_labels=False):
        if "forest" in env_gdfs and not env_gdfs["forest"].empty:
            env_gdfs["forest"].plot(ax=ax, color="#27AE60", alpha=0.45)
            
        # 500m buffer contours
        buffer_geoms = []
        for cat in ["settlement", "water"]:
            if cat in env_gdfs and not env_gdfs[cat].empty:
                buf = [g.buffer(buffer_radius_m) for g in env_gdfs[cat].geometry if not g.is_empty]
                buffer_geoms.extend(buf)
        if buffer_geoms:
            dissolved_buf = unary_union(buffer_geoms)
            if not dissolved_buf.is_empty:
                gpd.GeoSeries([dissolved_buf], crs=mine_gdf.crs).boundary.plot(
                    ax=ax, color="#7F8C8D", linestyle=":", linewidth=1.1, alpha=0.7
                )
                
        if "water" in env_gdfs and not env_gdfs["water"].empty:
            env_gdfs["water"].plot(ax=ax, color="#2980B9", alpha=0.85)
            
        if "settlement" in env_gdfs and not env_gdfs["settlement"].empty:
            env_gdfs["settlement"].plot(ax=ax, color="#E67E22", alpha=0.85)
            
        # Mining footprint: Base in deep crimson, New Expansion in vibrant gold
        if not mine_gdf.empty:
            mine_gdf.plot(ax=ax, color="#900C3F", edgecolor="#581845", linewidth=0.8, alpha=0.85)
            
        if exp_gdf is not None and not exp_gdf.empty and year > 2021:
            exp_gdf.plot(ax=ax, color="#FFD700", edgecolor="#D35400", linewidth=1.2, alpha=0.95)
            
    # Panel 1: Full AOI Regional Overview
    plot_layers(ax_main)
    ax_main.set_title(f"Regional Land Cover & Buffer Context ({year})\nAOI: 85 km² (EPSG:32643)", fontsize=12, fontweight='bold', pad=10)
    ax_main.set_xlabel("Easting (m)", fontsize=10)
    ax_main.set_ylabel("Northing (m)", fontsize=10)
    ax_main.grid(True, linestyle="--", alpha=0.4)
    
    # Active mining core zoom bounding box (Mochia, Balaria, Zawarmala)
    zoom_minx, zoom_maxx = 368200, 372200
    zoom_miny, zoom_maxy = 2692200, 2695800
    
    # Draw zoom boundary rectangle on main map
    rect = plt.Rectangle(
        (zoom_minx, zoom_miny), zoom_maxx - zoom_minx, zoom_maxy - zoom_miny,
        fill=False, color="#C0392B", linestyle="-", linewidth=1.8
    )
    ax_main.add_patch(rect)
    ax_main.annotate("Focus Inset", (zoom_minx, zoom_maxy + 120), color="#C0392B", fontweight='bold', fontsize=9)
    
    # Panel 2: Zoomed-in Core Mining Extent
    plot_layers(ax_zoom)
    ax_zoom.set_xlim(zoom_minx, zoom_maxx)
    ax_zoom.set_ylim(zoom_miny, zoom_maxy)
    ax_zoom.set_title(f"Active Mining Core: Encroachment Detail ({year})\nHigh-Resolution Extent (4 km × 3.6 km)", fontsize=12, fontweight='bold', pad=10)
    ax_zoom.set_xlabel("Easting (m)", fontsize=10)
    ax_zoom.set_ylabel("Northing (m)", fontsize=10)
    ax_zoom.grid(True, linestyle="--", alpha=0.4)
    
    # Key Metrics Callout Badge on Zoomed Panel
    total_area_ha = mine_gdf["area_ha"].sum() if not mine_gdf.empty else 0.0
    new_area_ha = exp_gdf["area_ha"].sum() if (exp_gdf is not None and not exp_gdf.empty and year > 2021) else 0.0
    
    badge_text = f"Total Footprint: {total_area_ha:.1f} ha"
    if year > 2021:
        badge_text += f"\nNew Expansion: +{new_area_ha:.2f} ha"
        
    ax_zoom.text(
        0.03, 0.95, badge_text,
        transform=ax_zoom.transAxes,
        fontsize=10, fontweight='bold',
        verticalalignment='top',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='#333333', alpha=0.9)
    )
    
    # Custom Legend
    legend_elements = [
        mpatches.Patch(facecolor="#900C3F", edgecolor="#581845", label="Active Mining Baseline"),
        mpatches.Patch(facecolor="#FFD700", edgecolor="#D35400", label="Newly Detected Expansion" if year > 2021 else "Baseline Mining Units"),
        mpatches.Patch(facecolor="#2980B9", label="Water (Dynamic World 0)"),
        mpatches.Patch(facecolor="#E67E22", label="Built-up / Settlement (DW 6)"),
        mpatches.Patch(facecolor="#27AE60", alpha=0.5, label="Forest / Tree Cover (DW 1)"),
        mpatches.Patch(facecolor="none", edgecolor="#7F8C8D", linestyle=":", label=f"{buffer_radius_m}m Buffer Zone")
    ]
    ax_main.legend(handles=legend_elements, loc="lower right", framealpha=0.9, fontsize=8.5)
    
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
    logger.info(f"Annual Dual-Panel GIS Map {year} saved -> {out_path}")
    return out_path
