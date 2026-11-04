import rasterio
import matplotlib.pyplot as plt
import numpy as np
import os

print("Generating visual overlay for 2026...")

# 1. Load 2026 Satellite Image (Bands B4, B3, B2 for RGB)
with rasterio.open("data/zawar/composites/zawar_s2_2026.tif") as src:
    r = src.read(3)  # B4 (Red)
    g = src.read(2)  # B3 (Green)
    b = src.read(1)  # B2 (Blue)

rgb = np.dstack((r, g, b))
rgb = np.nan_to_num(rgb)
rgb = np.clip(rgb / 3000.0, 0, 1)  # Normalize and brighten for display

# 2. Load 2026 U-Net Prediction Mask
with rasterio.open("outputs/maps/unet_pred_2026.tif") as src:
    pred = src.read(1)

# 3. Create Side-by-Side Plot
fig, axes = plt.subplots(1, 2, figsize=(14, 6), dpi=300)
axes[0].imshow(rgb)
axes[0].set_title("Raw Sentinel-2 Satellite Image (2026)",fontweight='bold', fontsize=12)
axes[0].axis('off')

axes[1].imshow(rgb)
mask = np.ma.masked_where(pred < 0.5, pred)
axes[1].imshow(mask, cmap='Reds', vmin=0, vmax=1,alpha=0.7)  # Overlay predictions in red
axes[1].set_title("U-Net Detected Mine Footprint (2026)", fontweight='bold', fontsize=12)
axes[1].axis('off')

os.makedirs("outputs/reports", exist_ok=True)
plt.tight_layout()
plt.savefig("outputs/reports/teacher_demo_2026.png")
print("Visual saved to outputs/reports/teacher_demo_2026.png")
