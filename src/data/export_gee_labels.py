import ee
import yaml
import geemap
import geopandas as gpd
import os

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

ee.Initialize(project='mineops-major-porject')

aoi_gdf = gpd.read_file(config['data']['aoi_path'])
bounds = aoi_gdf.geometry.total_bounds
aoi_ee = ee.Geometry.Rectangle([bounds[0], bounds[1], bounds[2], bounds[3]])

os.makedirs("data/zawar/labels", exist_ok=True)

# Load ESA WorldCover and isolate Class 60 (Bare/Sparse / Mine)
worldcover = ee.ImageCollection('ESA/WorldCover/v200').first()
mine_mask = worldcover.eq(60).clip(aoi_ee)

out_path = "data/zawar/labels/zawar_mines_mask.tif"
print(f"Downloading WorldCover binary mine mask to {out_path}...")

geemap.download_ee_image(
    image=mine_mask,
    filename=out_path,
    scale=config['data']['resolution'],
    crs=config['data']['crs_area'],
    region=aoi_ee
)
print("\nLabel mask download complete!")