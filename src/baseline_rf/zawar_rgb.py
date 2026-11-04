# =========================================================
# MINEOPS - ZAWAR BLOCK I
# STEP 1: download EVERY individual Sentinel-2 image
# =========================================================
# One GeoTIFF per image, saved as:
#   zawar_images/<year>/Zawar_<date>_<id>.tif
# Layers (7): B2 B3 B4 B5 B8 B11 B12  (reflectance 0-1)
# Cloudy pixels are stored as -9999 (treated as "no data").
#
# Safe to stop and re-run: files already downloaded are skipped.
# Run:  python zawar_download_each_image.py
# =========================================================

import os
import time
from datetime import datetime, timezone
import ee
import requests

ee.Initialize(project="mineguard-ai-507807")

aoi = ee.Geometry.Rectangle([73.6736, 24.2972, 73.7597, 24.3778])

YEARS = [2021, 2022, 2023, 2024, 2025, 2026]
BANDS = ["B2", "B3", "B4", "B5", "B8", "B11", "B12"]
COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"
CRS = "EPSG:32643"     # same grid for every image (needed for the median later)
SCALE = 10
NODATA = -9999
OUT = "zawar_images"


def prepare(img):
    """Cloud-mask with SCL, convert to reflectance, fill masked with NODATA."""
    scl = img.select("SCL")
    clear = (scl.neq(3).And(scl.neq(8))
             .And(scl.neq(9)).And(scl.neq(10)))
    refl = img.select(BANDS).divide(10000).updateMask(clear)
    return refl.unmask(NODATA).toFloat()


def download(url, path):
    r = requests.get(url, timeout=600)
    r.raise_for_status()
    with open(path, "wb") as f:
        f.write(r.content)


for year in YEARS:
    folder = os.path.join(OUT, str(year))
    os.makedirs(folder, exist_ok=True)

    col = (ee.ImageCollection(COLLECTION)
           .filterBounds(aoi)
           .filterDate(f"{year}-03-01", f"{year}-06-01")
           .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
           .sort("system:time_start"))

    ids = col.aggregate_array("system:index").getInfo()
    times = col.aggregate_array("system:time_start").getInfo()
    print(f"\n=== {year}: {len(ids)} images ===")

    for i, (sid, t) in enumerate(zip(ids, times), 1):
        date = datetime.fromtimestamp(t / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
        path = os.path.join(folder, f"Zawar_{date}_{sid}.tif")

        if os.path.exists(path) and os.path.getsize(path) > 1000:
            print(f"[{i}/{len(ids)}] {date} already downloaded")
            continue

        for attempt in range(3):
            try:
                img = prepare(ee.Image(f"{COLLECTION}/{sid}"))
                url = img.getDownloadURL({
                    "name": f"Zawar_{date}",
                    "region": aoi,
                    "scale": SCALE,
                    "crs": CRS,
                    "format": "GEO_TIFF",
                })
                download(url, path)
                print(f"[{i}/{len(ids)}] {date} saved")
                break
            except Exception as e:
                print(f"[{i}/{len(ids)}] {date} attempt {attempt + 1} failed: "
                      f"{str(e)[:100]}")
                time.sleep(5)
        else:
            print(f"[{i}/{len(ids)}] {date} GAVE UP - re-run to retry")

print("\nDONE. Images are in:", os.path.abspath(OUT))