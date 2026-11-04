import ee
import yaml
import geemap
import geopandas as gpd
import os

# 1. Load config
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

ee.Initialize(project='mineops-major-porject')

# 2. Load AOI boundary
aoi_gdf = gpd.read_file(config['data']['aoi_path'])
bounds = aoi_gdf.geometry.total_bounds  # [minx, miny, maxx, maxy]
aoi_ee = ee.Geometry.Rectangle([bounds[0], bounds[1], bounds[2], bounds[3]])

out_dir = "data/zawar/composites"
os.makedirs(out_dir, exist_ok=True)

# 3. Cloud Masking Function


def mask_s2_clouds(image):
    scl = image.select('SCL')
    # Remove cloud shadows (3), medium prob clouds (8), high prob clouds (9), cirrus (10)
    mask = scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10))
    return image.updateMask(mask)


# 4. Generate & Download Yearly Composites
for year in config['data']['years']:
    print(f"\nProcessing year {year}...")
    start_date = f"{year}-{config['data']['season_window'][0]}"
    end_date = f"{year}-{config['data']['season_window'][1]}"

    # Filter the Sentinel-2 Harmonized Surface Reflectance collection
    collection = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                  .filterBounds(aoi_ee)
                  .filterDate(start_date, end_date)
                  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', config['data']['cloud_pct_max']))
                  .map(mask_s2_clouds)
                  .select(config['data']['bands']))

    # Create median composite and clip to our exact AOI
    median_composite = collection.median().clip(aoi_ee)

    out_path = os.path.join(out_dir, f"zawar_s2_{year}.tif")
    print(
        f"Downloading 10-band composite to {out_path} (this may take a minute)...")

    # Download directly to local machine
    geemap.download_ee_image(
        image=median_composite,
        filename=out_path,
        scale=config['data']['resolution'],
        crs=config['data']['crs_area'],
        region=aoi_ee
    )

print("\nAll downloads complete!")
