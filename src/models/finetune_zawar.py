import os
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from unet import build_model, adapt_input_channels
from dataset import ZawarDataset

if __name__ == "__main__":
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    
    print("1. Loading pretrained LAMES model (3 channels)...")
    model = build_model(in_channels=3)
    model.load_state_dict(torch.load("outputs/models/unet_lames_pretrained.pth", weights_only=True))
    
    print("2. Performing weight surgery (expanding to 10 channels)...")
    model = adapt_input_channels(model, new_channels=10)
    model = model.to(device)
    
    print("3. Loading Zawar 10-band dataset...")
    dataset = ZawarDataset("data/zawar/patches")
    loader = DataLoader(dataset, batch_size=4, shuffle=True)
    
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4)
    criterion = nn.BCEWithLogitsLoss()
    
    print(f"4. Starting Zawar fine-tuning on {device.upper()}...")
    model.train()
    
    for epoch in range(1, 31):  # 3 epochs for this initial test [it was 1-4 first, now changed to 1-31]
        epoch_loss = 0
        for i, (images, masks) in enumerate(loader):
            images, masks = images.to(device), masks.to(device)
            
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, masks)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
            
        print(f"Epoch {epoch} complete - Avg Loss: {epoch_loss/len(loader):.4f}")
        
    out_path = "outputs/models/unet_zawar_finetuned.pth"
    torch.save(model.state_dict(), out_path)
    print(f"Fine-tuned weights saved to {out_path}")