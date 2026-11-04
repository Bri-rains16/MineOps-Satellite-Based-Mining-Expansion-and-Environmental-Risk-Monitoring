import torch
import numpy as np
from torch.utils.data import DataLoader
from sklearn.metrics import cohen_kappa_score
import sys
import os

sys.path.append(os.path.abspath("src/models"))
from unet import build_model, adapt_input_channels
from dataset import ZawarDataset

def evaluate_zeroshot():
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    
    print("Loading base LAMES model (Zero-Shot test)...")
    model = build_model(in_channels=3)
    
    # CRITICAL DIFFERENCE: Load the weights from BEFORE fine-tuning
    model.load_state_dict(torch.load("outputs/models/unet_lames_pretrained.pth", weights_only=True))
    
    # Adapt to 10 channels using weight surgery, but DO NOT train
    model = adapt_input_channels(model, new_channels=10)
    model = model.to(device)
    model.eval()

    dataset = ZawarDataset("data/zawar/patches")
    loader = DataLoader(dataset, batch_size=4, shuffle=False)

    total_tp, total_fp, total_fn, total_tn = 0, 0, 0, 0
    all_preds, all_labels = [], []

    print("Running zero-shot inference on Zawar patches...")
    with torch.no_grad():
        for images, masks in loader:
            images, masks = images.to(device), masks.to(device)
            outputs = model(images)
            preds = (outputs > 0.0).float()
            
            preds_flat = preds.cpu().numpy().flatten()
            masks_flat = masks.cpu().numpy().flatten()
            
            all_preds.append(preds_flat)
            all_labels.append(masks_flat)
            
            total_tp += np.sum((preds_flat == 1) & (masks_flat == 1))
            total_fp += np.sum((preds_flat == 1) & (masks_flat == 0))
            total_fn += np.sum((preds_flat == 0) & (masks_flat == 1))
            total_tn += np.sum((preds_flat == 0) & (masks_flat == 0))

    iou = total_tp / (total_tp + total_fp + total_fn) if (total_tp + total_fp + total_fn) > 0 else 0
    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
    f1_dice = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    
    y_pred = np.concatenate(all_preds)
    y_true = np.concatenate(all_labels)
    kappa = cohen_kappa_score(y_true, y_pred)

    print("\n" + "="*50)
    print("ZERO-SHOT U-NET EVALUATION METRICS")
    print("="*50)
    print(f"Intersection over Union (IoU) : {iou:.4f}")
    print(f"Dice/F1 Score                 : {f1_dice:.4f}")
    print(f"Precision                     : {precision:.4f}")
    print(f"Recall                        : {recall:.4f}")
    print(f"Kappa Coefficient             : {kappa:.4f}")
    print("="*50)

if __name__ == "__main__":
    evaluate_zeroshot()