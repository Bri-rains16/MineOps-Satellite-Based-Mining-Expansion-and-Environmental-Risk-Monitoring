import os
import numpy as np
import torch
from torch.utils.data import Dataset

class ZawarDataset(Dataset):
    def __init__(self, patches_dir):
        self.images_dir = os.path.join(patches_dir, "images")
        self.masks_dir = os.path.join(patches_dir, "masks")
        self.patch_names = [f for f in os.listdir(self.images_dir) if f.endswith('.npy')]

    def __len__(self):
        return len(self.patch_names)

    def __getitem__(self, idx):
        img = np.load(os.path.join(self.images_dir, self.patch_names[idx])).astype(np.float32)
        mask = np.load(os.path.join(self.masks_dir, self.patch_names[idx])).astype(np.float32)
        
        # 1. Clean the data: Replace Earth Engine NaNs/Infinities with 0
        img = np.nan_to_num(img, nan=0.0, posinf=0.0, neginf=0.0)
        
        # 2. Normalize: Sentinel-2 SR is scaled by 10000. Convert to 0-1 range.
        img = img / 10000.0
        img = np.clip(img, 0, 1)
        
        return torch.from_numpy(img), torch.from_numpy(mask).unsqueeze(0)

if __name__ == "__main__":
    ds = ZawarDataset("data/zawar/patches")
    img, mask = ds[0]
    print(f"Data sanitized! Image min: {img.min():.4f}, max: {img.max():.4f}, NaNs: {torch.isnan(img).any().item()}")