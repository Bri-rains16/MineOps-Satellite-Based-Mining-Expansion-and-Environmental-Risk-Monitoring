import os
import yaml
import rasterio
import numpy as np

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

patch_size = config['data']['patch_size']
img_path = "data/zawar/composites/zawar_s2_2021.tif"
mask_path = "data/zawar/labels/zawar_mines_mask.tif"
out_dir = "data/zawar/patches"

os.makedirs(os.path.join(out_dir, "images"), exist_ok=True)
os.makedirs(os.path.join(out_dir, "masks"), exist_ok=True)

print(f"Slicing 2021 composite and mask into {patch_size}x{patch_size} patches...")

with rasterio.open(img_path) as src_img, rasterio.open(mask_path) as src_mask:
    img_data = src_img.read()      # Shape: (10, H, W)
    mask_data = src_mask.read(1)   # Shape: (H, W)

    _, h, w = img_data.shape
    stride = patch_size // 2       # 50% overlap to generate more training data
    patch_idx = 0

    for y in range(0, h - patch_size + 1, stride):
        for x in range(0, w - patch_size + 1, stride):
            img_patch = img_data[:, y:y+patch_size, x:x+patch_size]
            mask_patch = mask_data[y:y+patch_size, x:x+patch_size]

            np.save(os.path.join(out_dir, "images", f"patch_{patch_idx}.npy"), img_patch)
            np.save(os.path.join(out_dir, "masks", f"patch_{patch_idx}.npy"), mask_patch)
            patch_idx += 1

print(f"Successfully extracted {patch_idx} patches!")