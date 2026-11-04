import os
import yaml
import torch
import numpy as np
import rasterio
import sys

sys.path.append(os.path.abspath("src/models"))
from unet import build_model, adapt_input_channels

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

device = "mps" if torch.backends.mps.is_available() else "cpu"
print("Loading model for multi-temporal inference...")
model = build_model(in_channels=3)
model = adapt_input_channels(model, new_channels=10)
model.load_state_dict(torch.load("outputs/models/unet_zawar_finetuned.pth", weights_only=True))
model = model.to(device)
model.eval()

os.makedirs("outputs/maps", exist_ok=True)

# U-Net requires input dimensions to be divisible by 32. This pads the edges safely.
def pad_image(img_array, multiple=32):
    _, h, w = img_array.shape
    pad_h = (multiple - h % multiple) % multiple
    pad_w = (multiple - w % multiple) % multiple
    padded = np.pad(img_array, ((0, 0), (0, pad_h), (0, pad_w)), mode='reflect')
    return padded, h, w

with torch.no_grad():
    for year in config['data']['years']:
        print(f"Predicting mining footprint for {year}...")
        img_path = f"data/zawar/composites/zawar_s2_{year}.tif"
        out_path = f"outputs/maps/unet_pred_{year}.tif"
        
        with rasterio.open(img_path) as src:
            profile = src.profile
            img = src.read()
            
        # Sanitize and normalize identical to training
        img = np.nan_to_num(img, nan=0.0, posinf=0.0, neginf=0.0) / 10000.0
        img = np.clip(img, 0, 1).astype(np.float32)
        
        padded_img, orig_h, orig_w = pad_image(img)
        tensor_img = torch.from_numpy(padded_img).unsqueeze(0).to(device)
        
        output = model(tensor_img)
        pred = (output > 0.0).float().squeeze().cpu().numpy()
        
        # Crop back to exact geographical bounds
        pred = pred[:orig_h, :orig_w]
        
        # Save as a single-band GeoTIFF
        profile.update(dtype=rasterio.float32, count=1)
        with rasterio.open(out_path, 'w', **profile) as dst:
            dst.write(pred, 1)

print("\nPhase 6 Complete: Predicted maps saved to outputs/maps/")