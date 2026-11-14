"""
src/baseline_rf/run_rf_all_years.py
-----------------------------------
Runs genuine multi-temporal Random Forest classification for all 6 years (2021-2026):
1. Trains Random Forest model on 2021 baseline Sentinel-2 composite + ESA WorldCover v200 ground truth.
2. For each year (2021-2026), runs inference on pre-monsoon cloud-masked Sentinel-2 imagery.
3. Downloads 10m classified GeoTIFF to outputs/classified/zawar_classified_{year}.tif.
4. Generates mutually exclusive vector polygons directly from the classified GeoTIFF raster:
   - Every pixel belongs to exactly one class.
   - Zero interior overlaps between classes.
   - Calculates area in EPSG:32643 and exports clean GeoJSON in EPSG:4326 to outputs/polygons_rf_clean/.
"""

import json
import logging
import os
import sys
from pathlib import Path
import ee
import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import shapes
import requests
from shapely.geometry import shape
from shapely.validation import make_valid
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("rf_multi_year")

# 1. INITIALIZE EARTH ENGINE
GEE_PROJECT = os.getenv("GEE_PROJECT_ID", "major-project-1-508714")
log.info("Initializing Earth Engine with project: %s", GEE_PROJECT)
ee.Initialize(project=GEE_PROJECT)

# 2. CONFIGURATION
aoi = ee.Geometry.Rectangle([73.6736, 24.2972, 73.7597, 24.3778])
YEARS = [2021, 2022, 2023, 2024, 2025, 2026]
BASELINE_YEAR = 2021
COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"
CRS = "EPSG:32643"
SCALE = 10
SAMPLES_PER_CLASS = 500

CLASSIFIED_DIR = Path("outputs/classified")
POLYGONS_CLEAN_DIR = Path("outputs/polygons_rf_clean_2021-2026")
CLASSIFIED_DIR.mkdir(parents=True, exist_ok=True)
POLYGONS_CLEAN_DIR.mkdir(parents=True, exist_ok=True)

CLASS_CONFIG = {
    0: ("Mine", "#E74C3C"),
    1: ("Settlement", "#F39C12"),
    2: ("Forest", "#27AE60"),
    3: ("Water", "#2980B9")
}

# 3. SPECTRAL FEATURE ENGINEERING (Ojha et al. 2025)
def mask_s2_clouds(img):
    scl = img.select("SCL")
    clear = scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10))
    return img.divide(10000).updateMask(clear)


def calculate_spectral_indices(img):
    b1  = img.select("B1")
    b2  = img.select("B2")
    b3  = img.select("B3")
    b4  = img.select("B4")
    b5  = img.select("B5")
    b7  = img.select("B7")
    b8  = img.select("B8")
    b11 = img.select("B11")
    b12 = img.select("B12")

    eps = 1e-6
    galena       = b5.divide(b7.add(eps)).rename("galena")
    sphalerite   = (b2.add(b4)).divide(b3.add(eps)).rename("sphalerite")
    pyrite       = b4.divide(b5.add(eps)).rename("pyrite")
    hydroxyl     = b11.divide(b12.add(eps)).rename("hydroxyl")
    sulphide     = b1.divide(b4.add(eps)).rename("sulphide")
    iron_oxide   = b2.divide(b3.add(eps)).rename("iron_oxide")
    ferric_oxide = b4.divide(b3.add(eps)).rename("ferric_oxide")

    ndvi         = (b8.subtract(b4)).divide(b8.add(b4).add(eps)).rename("ndvi")
    ndvi_re      = (b8.subtract(b5)).divide(b8.add(b5).add(eps)).rename("ndvi_re")
    rvi          = b8.divide(b5.add(eps)).rename("rvi")
    siderite     = b8.divide(b5.add(eps)).rename("siderite")

    mndwi        = (b3.subtract(b8)).divide(b3.add(b8).add(eps)).rename("mndwi")
    ndbi         = (b12.subtract(b8)).divide(b12.add(b8).add(eps)).rename("ndbi")
    nbi          = (b12.multiply(b4)).divide(b8.add(eps)).rename("nbi")
    bsi          = ((b11.add(b4)).subtract(b8.add(b2))).divide(
                    (b11.add(b4)).add(b8.add(b2)).add(eps)).rename("bsi")

    return img.addBands([
        galena, sphalerite, pyrite, hydroxyl, sulphide,
        iron_oxide, ferric_oxide,
        ndvi, ndvi_re, rvi, siderite,
        mndwi, ndbi, nbi, bsi
    ])


def get_annual_clean_image(year):
    col = (ee.ImageCollection(COLLECTION)
           .filterBounds(aoi)
           .filterDate(f"{year}-03-01", f"{year}-05-01")
           .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 25))
           .map(mask_s2_clouds))
    composite = col.median().clip(aoi)
    return calculate_spectral_indices(composite)


PREDICTOR_BANDS = [
    "B1", "B2", "B3", "B4", "B5", "B7", "B8", "B11", "B12",
    "galena", "sphalerite", "pyrite", "hydroxyl", "sulphide",
    "mndwi", "ndvi", "ndvi_re", "ndbi", "bsi"
]


def train_classifier():
    log.info("Loading ESA WorldCover v200 ground truth...")
    worldcover = ee.ImageCollection("ESA/WorldCover/v200").first().clip(aoi)
    esa_to_class = worldcover.remap(
        [10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100],
        [ 2,  2,  2,  2,  1,  0,  2,  3,  3,  3,   2],
        defaultValue=2
    ).rename("class").toInt()

    log.info("Sampling %d stratified points per class from baseline year %d...", SAMPLES_PER_CLASS, BASELINE_YEAR)
    baseline_img = get_annual_clean_image(BASELINE_YEAR)
    feature_img = baseline_img.select(PREDICTOR_BANDS).addBands(esa_to_class)

    training_samples = feature_img.stratifiedSample(
        numPoints=SAMPLES_PER_CLASS,
        classBand="class",
        region=aoi,
        scale=SCALE,
        seed=42,
        tileScale=4,
        classValues=[0, 1, 2, 3],
        classPoints=[SAMPLES_PER_CLASS, SAMPLES_PER_CLASS, SAMPLES_PER_CLASS, SAMPLES_PER_CLASS]
    )

    training_samples = training_samples.randomColumn("random", seed=42)
    train_set = training_samples.filter(ee.Filter.lt("random", 0.8))
    test_set  = training_samples.filter(ee.Filter.gte("random", 0.8))

    log.info("Training Random Forest classifier (150 trees)...")
    classifier = ee.Classifier.smileRandomForest(
        numberOfTrees=150,
        seed=42
    ).train(
        features=train_set,
        classProperty="class",
        inputProperties=PREDICTOR_BANDS
    )

    train_accuracy = classifier.confusionMatrix().accuracy().getInfo()
    test_results   = test_set.classify(classifier)
    test_accuracy  = test_results.errorMatrix("class", "classification").accuracy().getInfo()
    log.info("Training Accuracy: %.2f%% | Validation Accuracy: %.2f%%", train_accuracy * 100, test_accuracy * 100)
    return classifier


def ensure_geotiff(year: int, classifier) -> Path:
    tif_path = CLASSIFIED_DIR / f"zawar_classified_{year}.tif"
    if tif_path.exists():
        log.info("Year %d: GeoTIFF already exists on disk -> %s", year, tif_path)
        return tif_path

    log.info("Year %d: Fetching Sentinel-2 composite and classifying...", year)
    annual_img = get_annual_clean_image(year)
    classified = annual_img.select(PREDICTOR_BANDS).classify(classifier)

    log.info("Year %d: Downloading classified GeoTIFF from Earth Engine...", year)
    url = classified.getDownloadURL({
        "name":   f"zawar_classified_{year}",
        "region": aoi,
        "scale":  SCALE,
        "crs":    CRS,
        "format": "GEO_TIFF"
    })
    r = requests.get(url, timeout=300)
    r.raise_for_status()
    with open(tif_path, "wb") as f:
        f.write(r.content)
    log.info("Year %d: Saved GeoTIFF -> %s (%.1f KB)", year, tif_path, len(r.content)/1024)
    return tif_path


def vectorize_mutually_exclusive(tif_path: Path, year: int) -> Path:
    """
    Polygonizes a single classified raster. Every pixel belongs to exactly one class.
    Dissolves contiguous regions per class and exports clean, mutually exclusive polygons.
    """
    with rasterio.open(tif_path) as src:
        arr = src.read(1)
        transform = src.transform
        raster_crs = src.crs

    log.info("Year %d: Extracting shapes from raster grid %s...", year, arr.shape)
    raw_features = []
    # Mask out any invalid / nodata pixels if present
    for geom, val in shapes(arr, transform=transform):
        val = int(val)
        if val in CLASS_CONFIG:
            raw_features.append({
                "geometry": shape(geom),
                "class_id": val,
                "class_name": CLASS_CONFIG[val][0],
                "fill_color": CLASS_CONFIG[val][1],
                "year": year
            })

    gdf = gpd.GeoDataFrame(raw_features, crs=raster_crs)
    gdf["geometry"] = gdf["geometry"].apply(make_valid)

    # Filter out empty or tiny slivers (< 100 m² = 1 pixel)
    gdf = gdf[gdf.geometry.area >= 100.0].copy()

    # Dissolve contiguous parts by class_id to form consolidated multi-polygons
    dissolved = gdf.dissolve(by=["class_id", "class_name", "fill_color", "year"], as_index=False)
    dissolved["area_ha"] = (dissolved.geometry.area / 10000.0).round(2)

    # Validate mutual exclusivity (zero 2D interior overlap)
    c_geoms = {row.class_id: row.geometry for _, row in dissolved.iterrows()}
    for c1 in c_geoms:
        for c2 in c_geoms:
            if c1 < c2:
                overlap = c_geoms[c1].intersection(c_geoms[c2]).area
                assert overlap < 1e-4, f"Overlap detected between class {c1} and {c2}: {overlap} m2"

    # Export to clean GeoJSON in EPSG:4326 for GIS standards
    out_geojson = POLYGONS_CLEAN_DIR / f"zawar_all_classes_clean_{year}.geojson"
    dissolved_4326 = dissolved.to_crs("EPSG:4326")
    dissolved_4326.to_file(out_geojson, driver="GeoJSON")
    log.info("Year %d: Clean mutually exclusive GeoJSON saved -> %s", year, out_geojson)

    return out_geojson


def main():
    log.info("=== Multi-Temporal Random Forest Clean Vectorization (2021-2026) ===")
    classifier = train_classifier()

    summary_records = []
    for yr in YEARS:
        log.info("-" * 65)
        log.info("PROCESSING YEAR %d", yr)
        log.info("-" * 65)
        try:
            tif_path = ensure_geotiff(yr, classifier)
            geojson_path = vectorize_mutually_exclusive(tif_path, yr)

            # Read back clean GeoJSON for summary
            gdf_clean = gpd.read_file(geojson_path).to_crs(CRS)
            year_data = {"year": yr, "tif_path": str(tif_path), "geojson_path": str(geojson_path)}
            for _, row in gdf_clean.iterrows():
                cid = row["class_id"]
                cname = row["class_name"]
                year_data[f"class_{cid}_{cname}_ha"] = row["area_ha"]
            total_ha = sum(row["area_ha"] for _, row in gdf_clean.iterrows())
            year_data["total_area_ha"] = round(total_ha, 2)
            summary_records.append(year_data)

        except Exception as e:
            log.exception("FAILED for year %d: %s", yr, e)
            print(f"[ERROR] Year {yr} failed: {e}", file=sys.stderr)
            sys.exit(1)

    summary_csv = POLYGONS_CLEAN_DIR / "rf_clean_area_summary_2021_2026.csv"
    summary_df = gpd.pd.DataFrame(summary_records)
    summary_df.to_csv(summary_csv, index=False)
    log.info("Saved 6-year summary table -> %s", summary_csv)

    print("\n" + "=" * 70)
    print("  SIX-YEAR RANDOM FOREST CLEAN VECTORIZATION COMPLETED")
    print("=" * 70)
    print(summary_df.to_string(index=False))
    print("=" * 70)


if __name__ == "__main__":
    main()
