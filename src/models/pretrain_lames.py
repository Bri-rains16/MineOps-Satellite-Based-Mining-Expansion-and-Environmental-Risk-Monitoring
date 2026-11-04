import os
import io
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from PIL import Image
from unet import build_model

class LAMESDataset(Dataset):
    def __init__(self, parquet_path):
        self.df = pd.read_parquet(parquet_path)
        
    def __len__(self):
        return len(self.df)
        
    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        
        # Decode RGB image and normalize to 0-1
        img_bytes = row['image']['bytes']
        img = np.array(Image.open(io.BytesIO(img_bytes))) / 255.0
        img = torch.from_numpy(img).permute(2, 0, 1).float() # Shape: (3, H, W)
        
        # Decode Binary mask
        mask_bytes = row['mask']['bytes']
        mask = np.array(Image.open(io.BytesIO(mask_bytes)))
        mask = torch.from_numpy(mask).unsqueeze(0).float()   # Shape: (1, H, W)
        
        return img, mask

if __name__ == "__main__":
    os.makedirs("outputs/models", exist_ok=True)
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    
    print("Loading LAMES dataset...")
    dataset = LAMESDataset("data/lames/data/train-00000-of-00027.parquet")
    
    # Batch size 8 is safe for Mac unified memory
    loader = DataLoader(dataset, batch_size=8, shuffle=True)
    
    # Initialize 3-channel U-Net
    model = build_model(in_channels=3).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
    criterion = nn.BCEWithLogitsLoss()
    
    print(f"Starting pretraining on {device.upper()}...")
    model.train()
    
    for i, (images, masks) in enumerate(loader):
        images, masks = images.to(device), masks.to(device)
        
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, masks)
        loss.backward()
        optimizer.step()
        
        if i % 5 == 0:
            print(f"Batch {i}/{len(loader)} - Loss: {loss.item():.4f}")
            
        if i == 20:  # Short run to validate the pipeline without waiting hours
            print("Stopping test run early to save pipeline weights...")
            break
            
    out_path = "outputs/models/unet_lames_pretrained.pth"
    torch.save(model.state_dict(), out_path)
    print(f"Pretrained weights saved to {out_path}")