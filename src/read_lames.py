import pandas as pd
import numpy as np
from PIL import Image
import io

file_path = "data/lames/data/train-00000-of-00027.parquet"
print(f"Decoding first patch from {file_path}...\n")
df = pd.read_parquet(file_path)
first_row = df.iloc[0]

# 1. Decode Image
img_bytes = first_row['image']['bytes']
img = Image.open(io.BytesIO(img_bytes))
img_arr = np.array(img)

# 2. Decode Mask
mask_bytes = first_row['mask']['bytes']
mask = Image.open(io.BytesIO(mask_bytes))
mask_arr = np.array(mask)

print(f"Image Properties:")
print(f" - Shape (Height, Width, Channels): {img_arr.shape}")
print(f" - Pillow Mode: {img.mode}")

print(f"\nMask Properties:")
print(f" - Shape: {mask_arr.shape}")
print(f" - Unique pixel values: {np.unique(mask_arr)}")
