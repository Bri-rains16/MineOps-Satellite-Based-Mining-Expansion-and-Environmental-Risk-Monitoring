import os
import random
import torch
import numpy as np
from torch.utils.data import DataLoader
from torch.optim.lr_scheduler import ReduceLROnPlateau
import segmentation_models_pytorch as smp

from unet import build_model, adapt_input_channels
from dataset import ZawarDataset

# ============================== CONFIG ==============================
PRETRAINED_PATH = "outputs/models/unet_lames_pretrained.pth"
PATCH_DIR = "data/zawar/patches"
OUT_PATH = "outputs/models/unet_zawar_finetuned.pth"            # best val LOSS
OUT_PATH_IOU = "outputs/models/unet_zawar_finetuned_bestiou.pth"  # best val IoU

MAX_EPOCHS = 100
PATIENCE = 15            # early stopping on val loss
BATCH_SIZE = 4
LR_BASE = 1e-4           # pretrained layers
LR_FIRST_CONV = 1e-3     # first conv (7 of 10 input bands are randomly initialised)
POS_WEIGHT = None        # e.g. 3.0 if mines are rare (<5% of pixels); None = off
SEED = 42
# ====================================================================


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def pos_fraction(ds):
    """Fraction of mine pixels across a dataset (sanity check for the split)."""
    total, pos = 0, 0.0
    for i in range(len(ds)):
        _, m = ds[i]
        pos += float(m.sum())
        total += m.numel()
    return pos / total if total else 0.0


if __name__ == "__main__":
    set_seed(SEED)
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    device = "mps" if torch.backends.mps.is_available() else "cpu"

    print("1. Loading pretrained LAMES model...")
    model = build_model(in_channels=3)
    model.load_state_dict(torch.load(PRETRAINED_PATH, weights_only=True))

    print("2. Performing weight surgery...")
    model = adapt_input_channels(model, new_channels=10)
    model = model.to(device)

    print("3. Loading Train and Validation datasets...")
    train_dataset = ZawarDataset(PATCH_DIR, is_train=True)
    val_dataset = ZawarDataset(PATCH_DIR, is_train=False)

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False)

    # ---- Sanity checks (read these before trusting any training run) ----
    print(f"   Patches   train/val : {len(train_dataset)} / {len(val_dataset)}")
    train_pos, val_pos = pos_fraction(train_dataset), pos_fraction(val_dataset)
    print(f"   Mine px%  train/val : {train_pos*100:.2f}% / {val_pos*100:.2f}%")
    if val_pos < 0.005:
        print("   [WARN] Validation set has almost no mine pixels: IoU will be meaningless. "
              "Choose a spatial block that contains part of the mine.")
    if train_pos < 0.05 and POS_WEIGHT is None:
        print("   [HINT] Mines are rare in training data: consider POS_WEIGHT = 3.0")

    sample_imgs, _ = next(iter(train_loader))
    print(f"   Input stats (one batch): shape={tuple(sample_imgs.shape)} "
          f"min={sample_imgs.min():.3f} max={sample_imgs.max():.3f} "
          f"mean={sample_imgs.mean():.3f} std={sample_imgs.std():.3f}")
    if sample_imgs.abs().max() > 50:
        print("   [WARN] Input values are large. Bands should be scaled to ~0-1 or standardised, "
              "otherwise the 7 new random bands can swamp the pretrained RGB features.")

    # ---- Optimizer: higher LR for the new first conv, lower for the rest ----
    first_conv_params = [p for n, p in model.named_parameters() if n.startswith("encoder.conv1")]
    other_params = [p for n, p in model.named_parameters() if not n.startswith("encoder.conv1")]
    if first_conv_params:
        optimizer = torch.optim.AdamW([
            {"params": first_conv_params, "lr": LR_FIRST_CONV},
            {"params": other_params, "lr": LR_BASE},
        ])
    else:
        print("   [WARN] 'encoder.conv1' not found, using a single learning rate.")
        optimizer = torch.optim.AdamW(model.parameters(), lr=LR_BASE)

    scheduler = ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=3)

    # ---- Loss: 0.75 * BCE + 0.25 * Dice ----
    dice_loss = smp.losses.DiceLoss(smp.losses.BINARY_MODE, from_logits=True)
    if POS_WEIGHT is not None:
        bce_loss = smp.losses.SoftBCEWithLogitsLoss(
            pos_weight=torch.tensor([POS_WEIGHT], device=device))
    else:
        bce_loss = smp.losses.SoftBCEWithLogitsLoss()

    def criterion(y_pred, y_true):
        return 0.75 * bce_loss(y_pred, y_true) + 0.25 * dice_loss(y_pred, y_true)

    print(f"4. Starting training on {device.upper()} (early stopping on val loss)...")

    best_val_loss = float("inf")
    best_val_iou = 0.0
    epochs_without_improvement = 0

    for epoch in range(1, MAX_EPOCHS + 1):
        # --------------------------- TRAIN ---------------------------
        model.train()
        train_loss = 0.0
        for images, masks in train_loader:
            images, masks = images.to(device), masks.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, masks)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
        avg_train_loss = train_loss / len(train_loader)

        # ------------------------ VALIDATION -------------------------
        # IoU is computed from GLOBAL pixel counts over the whole val set,
        # not averaged per batch (empty batches would otherwise score 0).
        model.eval()
        val_loss = 0.0
        tp = fp = fn = 0.0
        max_prob = 0.0
        with torch.no_grad():
            for images, masks in val_loader:
                images, masks = images.to(device), masks.to(device)
                outputs = model(images)
                val_loss += criterion(outputs, masks).item()

                preds = (outputs > 0.0).float()
                tp += (preds * masks).sum().item()
                fp += (preds * (1 - masks)).sum().item()
                fn += ((1 - preds) * masks).sum().item()
                max_prob = max(max_prob, torch.sigmoid(outputs).max().item())

        avg_val_loss = val_loss / len(val_loader)
        denom = tp + fp + fn
        val_iou = tp / denom if denom > 0 else 0.0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        lr_now = optimizer.param_groups[-1]["lr"]

        print(f"Epoch {epoch:03d} | Train {avg_train_loss:.4f} | Val {avg_val_loss:.4f} | "
              f"IoU {val_iou:.4f} | P {precision:.3f} | R {recall:.3f} | "
              f"max prob {max_prob:.3f} | lr {lr_now:.1e}")

        scheduler.step(avg_val_loss)

        # Keep the best-IoU checkpoint as a secondary save
        if val_iou > best_val_iou:
            best_val_iou = val_iou
            torch.save(model.state_dict(), OUT_PATH_IOU)

        # ---------- EARLY STOPPING & CHECKPOINTING (on val loss) ----------
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            epochs_without_improvement = 0
            torch.save(model.state_dict(), OUT_PATH)
            print(f"  -> Best model saved (val loss {best_val_loss:.4f}, IoU {val_iou:.4f})")
        else:
            epochs_without_improvement += 1
            if epochs_without_improvement >= PATIENCE:
                print(f"\nEarly stopping: val loss has not improved for {PATIENCE} epochs.")
                break

    print(f"\nTraining complete. Best val loss: {best_val_loss:.4f} | Best val IoU: {best_val_iou:.4f}")
    print(f"Saved: {OUT_PATH}")
    print(f"Saved: {OUT_PATH_IOU}")