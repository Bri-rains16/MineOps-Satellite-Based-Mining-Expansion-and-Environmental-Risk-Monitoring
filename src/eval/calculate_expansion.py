import os
import yaml
import json
import rasterio
import matplotlib.pyplot as plt

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

years = config['data']['years']
resolution = config['data']['resolution']
pixel_area_ha = (resolution * resolution) / 10000.0  # 10m x 10m = 100m^2 = 0.01 ha

expansion_history = []
previous_area = None

print("-" * 55)
print(f"{'Year':<8} | {'Mine Area (Ha)':<16} | {'Expansion (Ha)'}")
print("-" * 55)

for year in years:
    map_path = f"outputs/maps/unet_pred_{year}.tif"
    with rasterio.open(map_path) as src:
        pred = src.read(1)
    
    # Count pixels classified as 1 (Mine) and calculate area
    mine_pixels = (pred == 1).sum()
    area_ha = mine_pixels * pixel_area_ha
    
    expansion = 0.0 if previous_area is None else (area_ha - previous_area)
    expansion_str = "Baseline" if previous_area is None else f"{expansion:+.2f} ha"
    
    print(f"{year:<8} | {area_ha:<16.2f} | {expansion_str}")
    
    expansion_history.append({
        "year": year,
        "area_hectares": round(area_ha, 2),
        "expansion_ha": round(expansion, 2) if previous_area is not None else 0.0
    })
    previous_area = area_ha

print("-" * 55)

# Save JSON Report
os.makedirs("outputs/reports", exist_ok=True)
with open("outputs/reports/unet_expansion.json", "w") as f:
    json.dump(expansion_history, f, indent=4)

# Generate and Save Plot
areas = [d["area_hectares"] for d in expansion_history]
plt.figure(figsize=(10, 5), dpi=300)
plt.plot(years, areas, marker='o', linewidth=2.5, markersize=8, color='#0078D7', label='U-Net Active Mine Footprint')
plt.title("Zawar U-Net Mine Footprint Expansion (2021 - 2026)", fontsize=14, fontweight='bold')
plt.xlabel("Year", fontsize=12)
plt.ylabel("Detected Area (Hectares)", fontsize=12)
plt.grid(True, linestyle='--', alpha=0.6)

for y, a in zip(years, areas):
    plt.annotate(f"{a:.1f} ha", (y, a), textcoords="offset points", xytext=(0, 10), ha='center', fontweight='semibold')

plt.tight_layout()
plt.savefig("outputs/reports/unet_expansion_trend.png")
print(f"\n[OK] Report saved to outputs/reports/unet_expansion.json")
print(f"[OK] Expansion chart saved to outputs/reports/unet_expansion_trend.png")