"""
=============================================================================
MineOps: Single-Year (2021) Random Forest Runner for Zawar Region
Target Outputs:
  - outputs/polygons/zawar_all_classes_2021.geojson
  - outputs/classified/zawar_classified_2021.tif

Reuses exact methodology from Ojha et al. (2025) and Sidhi's Random Forest
baseline (src/baseline_rf/mineops_pipeline.py) without altering classification
logic or modifying existing scripts.
=============================================================================
"""

import json
import os
import sys
import requests
import ee
from dotenv import load_dotenv

load_dotenv()

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# 1. INITIALIZE EARTH ENGINE
GEE_PROJECT = os.getenv("GEE_PROJECT_ID", "major-project-1-508714")
print(f"[Step 0] Initializing Google Earth Engine with project {GEE_PROJECT}...")
ee.Initialize(project=GEE_PROJECT)
print("  [OK] Earth Engine connected successfully!\n")

# 2. CONFIGURATION (Identical to mineops_pipeline.py)
aoi = ee.Geometry.Rectangle([73.6736, 24.2972, 73.7597, 24.3778])
TARGET_YEAR = 2021
BASELINE_YEAR = 2021
COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"
CRS = "EPSG:32643"   # UTM Zone 43N
SCALE = 10
SAMPLES_PER_CLASS = 500

OUTPUT_DIR = "outputs"
POLYGONS_DIR = os.path.join(OUTPUT_DIR, "polygons_2021")
CLASSIFIED_DIR = os.path.join(OUTPUT_DIR, "classified")
os.makedirs(POLYGONS_DIR, exist_ok=True)
os.makedirs(CLASSIFIED_DIR, exist_ok=True)

# 3. SPECTRAL FEATURE ENGINEERING (Ojha et al. 2025, Table 2)
def mask_s2_clouds(img):
    """Cloud/shadow masking via Sentinel-2 Scene Classification Layer (SCL)."""
    scl = img.select("SCL")
    clear = scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10))
    return img.divide(10000).updateMask(clear)


def calculate_spectral_indices(img):
    """15 mineral, vegetation, water, and built-up indices from Ojha et al."""
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

    # Mineral indices
    galena       = b5.divide(b7.add(eps)).rename("galena")
    sphalerite   = (b2.add(b4)).divide(b3.add(eps)).rename("sphalerite")
    pyrite       = b4.divide(b5.add(eps)).rename("pyrite")
    hydroxyl     = b11.divide(b12.add(eps)).rename("hydroxyl")
    sulphide     = b1.divide(b4.add(eps)).rename("sulphide")
    iron_oxide   = b2.divide(b3.add(eps)).rename("iron_oxide")
    ferric_oxide = b4.divide(b3.add(eps)).rename("ferric_oxide")

    # Vegetation indices
    ndvi         = (b8.subtract(b4)).divide(b8.add(b4).add(eps)).rename("ndvi")
    ndvi_re      = (b8.subtract(b5)).divide(b8.add(b5).add(eps)).rename("ndvi_re")
    rvi          = b8.divide(b5.add(eps)).rename("rvi")
    siderite     = b8.divide(b5.add(eps)).rename("siderite")

    # Water index
    mndwi        = (b3.subtract(b8)).divide(b3.add(b8).add(eps)).rename("mndwi")

    # Built-up / Bare soil indices
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
    """Pre-monsoon cloud-free median composite with all spectral indices."""
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

# 4. GROUND TRUTH LABELS VIA ESA WORLDCOVER v200
print("[Step 1] Loading ESA WorldCover v200 ground-truth reference...")
worldcover = ee.ImageCollection("ESA/WorldCover/v200").first().clip(aoi)

esa_to_class = worldcover.remap(
    [10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100],
    [ 2,  2,  2,  2,  1,  0,  2,  3,  3,  3,   2],
    defaultValue=2
).rename("class").toInt()

# 5. STRATIFIED SAMPLING (500 per class)
print(f"[Step 2] Extracting stratified training points ({SAMPLES_PER_CLASS}/class)...")
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

train_count = train_set.size().getInfo()
test_count  = test_set.size().getInfo()
print(f"  [OK] Train set: {train_count} | Test set: {test_count}")

# 6. MODEL TRAINING
print("[Step 3] Training Random Forest classifier (150 trees, seed=42)...")
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
test_kappa     = test_results.errorMatrix("class", "classification").kappa().getInfo()

print(f"  [OK] Training Accuracy  : {train_accuracy * 100:.2f}%")
print(f"  [OK] Validation Accuracy: {test_accuracy  * 100:.2f}%")
print(f"  [OK] Kappa Coefficient  : {test_kappa:.4f}")

# 7. INFERENCE FOR YEAR 2021 ONLY
print(f"\n[Step 4] Running 2021 Inference & Vector Polygon Export...")
CLASS_CONFIG = [
    (0, "Mine",       "#E74C3C"),
    (1, "Settlement", "#F39C12"),
    (2, "Forest",     "#27AE60"),
    (3, "Water",      "#2980B9"),
]

annual_img = get_annual_clean_image(TARGET_YEAR)
classified = annual_img.select(PREDICTOR_BANDS).classify(classifier)

# Compute Mine Area
kernel = ee.Kernel.square(radius=1)
mine_mask = classified.eq(0).selfMask()
pixel_area = mine_mask.multiply(ee.Image.pixelArea())
area_m2 = (pixel_area
           .reduceRegion(reducer=ee.Reducer.sum(), geometry=aoi,
                          scale=SCALE, maxPixels=1e9)
           .get("classification").getInfo())
area_m2 = area_m2 if area_m2 else 0
area_ha = area_m2 / 10_000
area_km2 = area_m2 / 1_000_000
print(f"  2021 Mine Footprint: {area_ha:.2f} ha ({area_km2:.3f} km2)")

# Vector Polygon Export
all_features = []
for class_id, class_name, color in CLASS_CONFIG:
    class_mask = classified.eq(class_id).selfMask()
    smoothed = (class_mask
                .focal_min(kernel=kernel)
                .focal_max(kernel=kernel)
                .selfMask())
    try:
        vectors = smoothed.reduceToVectors(
            geometry=aoi,
            scale=50,
            geometryType="polygon",
            eightConnected=True,
            maxPixels=1e8,
            bestEffort=True
        )
        vectors = vectors.map(lambda f: f.set({
            "class_id":   class_id,
            "class_name": class_name,
            "fill_color": color,
            "year":       TARGET_YEAR
        }))
        class_info = vectors.getInfo()
        feats = class_info.get("features", [])
        all_features.extend(feats)
        print(f"    Class {class_id} ({class_name:<10}): {len(feats)} polygons")
    except Exception as e:
        print(f"    Class {class_id} ({class_name:<10}): ERROR -> {str(e)[:60]}")

# Write GeoJSON
geojson_path = os.path.join(POLYGONS_DIR, f"zawar_all_classes_{TARGET_YEAR}.geojson")
combined_geojson = {"type": "FeatureCollection", "features": all_features}
with open(geojson_path, "w", encoding="utf-8") as f:
    json.dump(combined_geojson, f)
print(f"  [OK] 4-class GeoJSON saved -> {geojson_path}")

# Download Classified GeoTIFF
tif_path = os.path.join(CLASSIFIED_DIR, f"zawar_classified_{TARGET_YEAR}.tif")
print(f"  Downloading classified GeoTIFF to {tif_path}...")
try:
    url = classified.getDownloadURL({
        "name":   f"zawar_classified_{TARGET_YEAR}",
        "region": aoi,
        "scale":  SCALE,
        "crs":    CRS,
        "format": "GEO_TIFF"
    })
    r = requests.get(url, timeout=300)
    with open(tif_path, "wb") as f:
        f.write(r.content)
    print(f"  [OK] GeoTIFF saved successfully -> {tif_path} ({len(r.content)/1024:.1f} KB)")
except Exception as e:
    print(f"  [WARNING] GeoTIFF download deferred: {e}")

print("\n[DONE] 2021 Random Forest Execution Complete.")
