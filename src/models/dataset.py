import os
import numpy as np
import torch
from torch.utils.data import Dataset
import albumentations as A
from albumentations.pytorch import ToTensorV2

class ZawarDataset(Dataset):
    def __init__(self, patches_dir, is_train=True):
        self.images_dir = os.path.join(patches_dir, "images")
        self.masks_dir = os.path.join(patches_dir, "masks")
        
        # 1. Fetch and numerically sort filenames to maintain the geographic grid layout
        all_patches = [f for f in os.listdir(self.images_dir) if f.endswith('.npy')]
        all_patches = sorted(all_patches, key=lambda x: int(x.split('_')[1].split('.')[0]))
        
        # 2. Reserve a 6-patch contiguous block from the MIDDLE of the map for validation
        val_start = 12
        val_end = 18
        
        if is_train:
            self.patch_names = all_patches[:val_start] + all_patches[val_end:]
            # Lossless spatial augmentations only
            self.transform = A.Compose([
                A.HorizontalFlip(p=0.5),
                A.VerticalFlip(p=0.5),
                A.RandomRotate90(p=0.5),
                ToTensorV2(),
            ])
        else:
            self.patch_names = all_patches[val_start:val_end]
            self.transform = A.Compose([
                ToTensorV2(),
            ])

        self.is_train = is_train

    def __len__(self):
        return len(self.patch_names)

    def __getitem__(self, idx):
        img = np.load(os.path.join(self.images_dir, self.patch_names[idx])).astype(np.float32)
        mask = np.load(os.path.join(self.masks_dir, self.patch_names[idx])).astype(np.float32)
        
        img = np.nan_to_num(img, nan=0.0, posinf=0.0, neginf=0.0)
        img = img / 10000.0
        img = np.clip(img, 0, 1)
        
        img = np.transpose(img, (1, 2, 0))
        
        augmented = self.transform(image=img, mask=mask)
        img_aug = augmented['image']
        mask_aug = augmented['mask'].unsqueeze(0)
        
        return img_aug, mask_aug