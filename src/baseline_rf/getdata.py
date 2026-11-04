import ee
import requests
import os

# ============================================================
# 1. INITIALIZE EARTH ENGINE
# ============================================================

ee.Initialize(project="mineguard-ai-507807")

print("Earth Engine connected successfully!")


# ============================================================
# 2. CREATE OUTPUT FOLDER
# ============================================================

output_folder = "mineguard_data"
os.makedirs(output_folder, exist_ok=True)


# ============================================================
# 3. DEFINE TEST AREA IN KEONJHAR, ODISHA
# ============================================================
#
# IMPORTANT:
# This is currently a TEST AREA, not an actual mine boundary.
# We will replace this with real mine polygons later.
#
# Coordinates are:
# [longitude, latitude]
#

mine_area = ee.Geometry.Polygon([
    [
        [85.25, 21.60],
        [85.35, 21.60],
        [85.35, 21.70],
        [85.25, 21.70],
        [85.25, 21.60]
    ]
])


# ============================================================
# 4. CLOUD MASK
# ============================================================

def mask_s2_clouds(image):

    qa = image.select("QA60")

    cloud_bit_mask = 1 << 10
    cirrus_bit_mask = 1 << 11

    mask = (
        qa.bitwiseAnd(cloud_bit_mask)
        .eq(0)
        .And(
            qa.bitwiseAnd(cirrus_bit_mask)
            .eq(0)
        )
    )

    return (
        image
        .updateMask(mask)
        .divide(10000)
        .copyProperties(
            image,
            ["system:time_start"]
        )
    )


# ============================================================
# 5. LOAD SENTINEL-2
# ============================================================

print("Searching for Sentinel-2 images...")

dataset = (
    ee.ImageCollection(
        "COPERNICUS/S2_SR_HARMONIZED"
    )

    # Only images covering our area
    .filterBounds(mine_area)

    # 2020 data
    .filterDate(
        "2020-01-01",
        "2020-12-31"
    )

    # Maximum 20% cloud cover
    .filter(
        ee.Filter.lt(
            "CLOUDY_PIXEL_PERCENTAGE",
            20
        )
    )

    # Apply cloud masking
    .map(mask_s2_clouds)
)


# ============================================================
# 6. CHECK NUMBER OF IMAGES
# ============================================================

image_count = dataset.size().getInfo()

print(
    f"Suitable Sentinel-2 images found: {image_count}"
)

if image_count == 0:

    print(
        "No images found. "
        "Try increasing the cloud threshold."
    )

    exit()


# ============================================================
# 7. CREATE MEDIAN COMPOSITE
# ============================================================

print("Creating satellite composite...")

composite = (
    dataset
    .median()
    .clip(mine_area)
)


# ============================================================
# 8. SELECT BANDS
# ============================================================

bands = [
    "B2",   # Blue
    "B3",   # Green
    "B4",   # Red
    "B8",   # Near Infrared
    "B11",  # SWIR
    "B12"   # SWIR
]

image_download = composite.select(bands)


# ============================================================
# 9. DOWNLOAD GEOTIFF
# ============================================================

print("Preparing GeoTIFF download...")

download_url = image_download.getDownloadURL({

    "name": "odisha_mineguard_2020",

    "bands": bands,

    "region": mine_area,

    "scale": 20,

    "crs": "EPSG:4326",

    "format": "GEO_TIFF"
})


output_tif = os.path.join(
    output_folder,
    "odisha_mineguard_2020.tif"
)


print("Downloading GeoTIFF...")

response = requests.get(
    download_url,
    timeout=300
)

response.raise_for_status()


with open(output_tif, "wb") as file:

    file.write(response.content)


print(
    "\nGeoTIFF downloaded successfully!"
)

print(
    f"Location: {output_tif}"
)


# ============================================================
# 10. CREATE RGB PREVIEW
# ============================================================

print("Creating RGB preview...")

rgb = composite.select(
    ["B4", "B3", "B2"]
)


rgb_url = rgb.getThumbURL({

    "region": mine_area,

    "dimensions": 1500,

    "format": "png",

    "min": 0,

    "max": 0.3,

    "bands": [
        "B4",
        "B3",
        "B2"
    ]
})


output_png = os.path.join(
    output_folder,
    "odisha_mineguard_2020_RGB.png"
)


rgb_response = requests.get(
    rgb_url,
    timeout=300
)

rgb_response.raise_for_status()


with open(output_png, "wb") as file:

    file.write(rgb_response.content)


print(
    "RGB preview downloaded successfully!"
)

print(
    f"Location: {output_png}"
)


# ============================================================
# 11. FINISHED
# ============================================================

print("\n====================================")
print("       MINEGUARD DOWNLOAD DONE")
print("====================================")

print(
    f"\nFiles saved in: {output_folder}/"
)

print(
    "\n1. odisha_mineguard_2020.tif"
)

print(
    "2. odisha_mineguard_2020_RGB.png"
)

print(
    "\nOpen the PNG first to inspect the satellite image."
)