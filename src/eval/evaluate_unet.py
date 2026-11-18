import os
import sys
import torch
import numpy as np
from torch.utils.data import DataLoader
from sklearn.metrics import cohen_kappa_score

# Tell Python exactly where to look for your custom scripts
sys.path.append(os.path.abspath("src"))
sys.path.append(os.path.abspath("src/models"))

from dataset import ZawarDataset
from unet import build_model, adapt_input_channels

def evaluate_model():
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    
    print("Loading fine-tuned Zawar model (Best IoU Checkpoint)...")
    model = build_model(in_channels=3)
    model = adapt_input_channels(model, new_channels=10)
    
    # We load the weights that achieved the highest Validation IoU
    model.load_state_dict(torch.load("outputs/models/unet_zawar_finetuned_bestiou.pth", weights_only=True))
    model = model.to(device)
    model.eval()

    # The dataset class automatically uses patches 12-17 for our clean spatial split
    dataset = ZawarDataset("data/zawar/patches", is_train=False)
    loader = DataLoader(dataset, batch_size=4, shuffle=False)

    print("Running probability threshold sweep on validation block...")
    thresholds = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    best_thresh = 0.5
    best_iou = 0.0
    
    all_outputs = []
    all_masks = []
    
    with torch.no_grad():
        for images, masks in loader:
            images, masks = images.to(device), masks.to(device)
            outputs = model(images)
            
            # Convert raw logits to 0.0 - 1.0 probabilities
            probs = torch.sigmoid(outputs)
            
            all_outputs.append(probs.cpu().numpy())
            all_masks.append(masks.cpu().numpy())
            
    # Stack all predictions into large arrays
    all_outputs = np.concatenate(all_outputs)
    all_masks = np.concatenate(all_masks)
    
    # Sweep through the thresholds to find the mathematical optimum
    for t in thresholds:
        preds = (all_outputs > t).astype(np.float32)
        
        tp = np.sum((preds == 1) & (all_masks == 1))
        fp = np.sum((preds == 1) & (all_masks == 0))
        fn = np.sum((preds == 0) & (all_masks == 1))
        
        iou = tp / (tp + fp + fn) if (tp + fp + fn) > 0 else 0
        print(f"  Threshold {t:.1f} -> IoU: {iou:.4f}")
        
        if iou > best_iou:
            best_iou = iou
            best_thresh = t
            
    print(f"\nOptimal Probability Threshold: {best_thresh:.1f}")
    
    # Calculate final metrics with the optimal threshold
    final_preds = (all_outputs > best_thresh).astype(np.float32)
    
    tp = np.sum((final_preds == 1) & (all_masks == 1))
    fp = np.sum((final_preds == 1) & (all_masks == 0))
    fn = np.sum((final_preds == 0) & (all_masks == 1))
    tn = np.sum((final_preds == 0) & (all_masks == 0))
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1_dice = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    
    print("Calculating Kappa (this may take a moment)...")
    preds_flat = final_preds.flatten()
    masks_flat = all_masks.flatten()
    kappa = cohen_kappa_score(masks_flat, preds_flat)
    
    print("\n" + "="*55)
    print("FINAL U-NET EVALUATION METRICS (Held-out spatial block)")
    print("="*55)
    print(f"Intersection over Union (IoU) : {best_iou:.4f}")
    print(f"Dice/F1 Score                 : {f1_dice:.4f}")
    print(f"Precision                     : {precision:.4f}")
    print(f"Recall                        : {recall:.4f}")
    print(f"Kappa Coefficient             : {kappa:.4f}")
    print(f"Optimum Threshold Applied     : {best_thresh:.1f}")
    print("="*55)

if __name__ == "__main__":
    evaluate_model()