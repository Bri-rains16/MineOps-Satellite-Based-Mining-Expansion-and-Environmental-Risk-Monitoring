import os
import yaml
import json
import rasterio
import matplotlib.pyplot as plt
import numpy as np
from rasterio.windows import Window
from matplotlib.colors import ListedColormap

# =====================================================================
# 1. EXPANSION TREND ANALYSIS
# =====================================================================
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

os.makedirs("outputs/reports", exist_ok=True)
with open("outputs/reports/unet_expansion.json", "w") as f:
    json.dump(expansion_history, f, indent=4)

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


# =====================================================================
# 2. STRATEGY COMPARISON BAR CHART
# =====================================================================
# Updated Fine-Tuned U-Net with your newly calculated 0.6950 and 0.8200 scores!
labels = ['Zero-Shot U-Net\n(Global Only)', 'Random Forest', 'Fine-Tuned U-Net\n(Ours)']
iou_scores = [0.0221, 0.6200, 0.6950] 
dice_scores = [0.0433, 0.7654, 0.8200]

x = np.arange(len(labels))
width = 0.35

plt.figure(figsize=(9, 6), dpi=300)
bars1 = plt.bar(x - width/2, iou_scores, width, label='Intersection over Union (IoU)', color='#ff7675') # Coral/Red
bars2 = plt.bar(x + width/2, dice_scores, width, label='Dice/F1 Score', color='#48dbfb') # Cyan/Teal

plt.ylabel('Performance Score (0 to 1)', fontweight='bold')
plt.title('MineOps Detection Strategies: Performance Comparison', fontweight='bold', pad=15)
plt.xticks(x, labels, fontweight='bold')
plt.ylim(0, 1.05)
plt.legend(loc='upper left')
plt.grid(axis='y', linestyle='--', alpha=0.6)

def add_labels(bars):
    for bar in bars:
        height = bar.get_height()
        plt.annotate(f'{height:.4f}', xy=(bar.get_x() + bar.get_width() / 2, height),
                     xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontweight='bold')

add_labels(bars1)
add_labels(bars2)

plt.tight_layout()
plt.savefig("outputs/reports/strategy_comparison.png")
print(f"[OK] Strategy comparison saved to outputs/reports/strategy_comparison.png")


# =====================================================================
# 3. TEACHER DEMO VISUAL OVERLAY
# =====================================================================
img_path = "data/zawar/composites/zawar_s2_2026.tif"
mask_path = "outputs/maps/unet_pred_2026.tif"

if os.path.exists(img_path) and os.path.exists(mask_path):
    crop_window = Window(col_off=250, row_off=250, width=500, height=500)
    
    with rasterio.open(img_path) as src_img, rasterio.open(mask_path) as src_mask:
        img = src_img.read([3, 2, 1], window=crop_window) 
        img = np.nan_to_num(img, nan=0.0) / 10000.0
        img = np.clip(img, 0, 1).transpose(1, 2, 0)
        mask = src_mask.read(1, window=crop_window)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6), dpi=300)

    ax1.imshow(img)
    ax1.set_title("Zawar Satellite Feed (2026)", fontweight='bold')
    ax1.axis('off')

    ax2.imshow(img)
    cmap = ListedColormap(['none', '#ff4757']) # Transparent background, bold red mask
    ax2.imshow(mask, cmap=cmap, alpha=0.5)
    ax2.set_title("Fine-Tuned U-Net Prediction", fontweight='bold')
    ax2.axis('off')

    plt.tight_layout()
    plt.savefig("outputs/reports/teacher_demo_2026.png")
    print(f"[OK] Teacher demo overlay saved to outputs/reports/teacher_demo_2026.png")