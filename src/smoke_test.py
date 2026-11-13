import yaml
import os
import ee
from dotenv import load_dotenv
import torch

load_dotenv()
import segmentation_models_pytorch as smp

# 1. Load Configuration
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)
print(f"Config loaded. Patch size: {config['data']['patch_size']}")

# 2. Check PyTorch & Apple Silicon (MPS) GPU
device = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"PyTorch using device: {device.upper()}")

# 3. Test U-Net Initialization (Binary segmentation, 10 input bands)
model = smp.Unet(
    encoder_name="resnet34",
    encoder_weights=None,
    in_channels=len(config['data']['bands']),
    classes=1
).to(device)

dummy_input = torch.randn(
    1, 10, config['data']['patch_size'], config['data']['patch_size']).to(device)
output = model(dummy_input)
print(f"U-Net forward pass successful! Output shape: {output.shape}")

# 4. Earth Engine Authentication
GEE_PROJECT = os.getenv("GEE_PROJECT_ID", "major-project-1-508714")
try:
    ee.Initialize(project=GEE_PROJECT)
    print(f"Earth Engine initialized successfully with project {GEE_PROJECT}!")
except Exception as e:
    print("Earth Engine needs authentication. A browser window will open...")
    ee.Authenticate()
    ee.Initialize(project=GEE_PROJECT)
    print(f"Earth Engine authenticated and initialized with project {GEE_PROJECT}!")
