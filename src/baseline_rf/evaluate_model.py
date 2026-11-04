"""
=============================================================================
MineOps: Class-Wise Accuracy Assessment & Confusion Matrix Evaluation
Replicating the validation methods of Ojha et al. (2025) (Table 11 & Fig. 8)

Run AFTER mineops_pipeline.py has completed.
This script does NOT re-run the full pipeline. It independently re-trains
the model with identical seeds so all numbers are consistent.
=============================================================================
"""

import os
import ee
import matplotlib.pyplot as plt
import numpy as np

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# ---------------------------------------------------------------------------
# All configuration is self-contained here — no imports from mineops_pipeline
# to prevent accidentally re-running the full inference pipeline.
# ---------------------------------------------------------------------------
ee.Initialize(project="mineguard-ai-507807")
aoi = ee.Geometry.Rectangle([73.6736, 24.2972, 73.7597, 24.3778])
SCALE = 10
BASELINE_YEAR = 2021

PREDICTOR_BANDS = [
    "B2", "B3", "B4", "B5", "B8", "B11", "B12",
    "galena", "sphalerite", "pyrite", "hydroxyl", "sulphide",
    "mndwi", "ndvi", "ndbi", "bsi"
]

# ---------------------------------------------------------------------------
# Replicate the EXACT same functions and polygons as mineops_pipeline.py
# with the SAME fixed seeds — guarantees identical train/test split every run
# ---------------------------------------------------------------------------
def mask_s2_clouds(img):
    scl = img.select("SCL")
    clear = scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10))
    return img.divide(10000).updateMask(clear)

def calculate_spectral_indices(img):
    b1  = img.select("B1"); b2 = img.select("B2"); b3 = img.select("B3")
    b4  = img.select("B4"); b5 = img.select("B5"); b7 = img.select("B7")
    b8  = img.select("B8"); b11 = img.select("B11"); b12 = img.select("B12")
    eps = 1e-6
    return img.addBands([
        b5.divide(b7.add(eps)).rename("galena"),
        (b2.add(b4)).divide(b3.add(eps)).rename("sphalerite"),
        b4.divide(b5.add(eps)).rename("pyrite"),
        b11.divide(b12.add(eps)).rename("hydroxyl"),
        b1.divide(b4.add(eps)).rename("sulphide"),
        (b3.subtract(b8)).divide(b3.add(b8).add(eps)).rename("mndwi"),
        (b8.subtract(b4)).divide(b8.add(b4).add(eps)).rename("ndvi"),
        (b12.subtract(b8)).divide(b12.add(b8).add(eps)).rename("ndbi"),
        ((b11.add(b4)).subtract(b8.add(b2))).divide(
            (b11.add(b4)).add(b8.add(b2)).add(eps)).rename("bsi"),
    ])

def get_annual_clean_image(year):
    col = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
           .filterBounds(aoi)
           .filterDate(f"{year}-03-01", f"{year}-05-01")
           .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 25))
           .map(mask_s2_clouds))
    return calculate_spectral_indices(col.median().clip(aoi))

# Ground truth polygons (identical to mineops_pipeline.py)
mine_zones = ee.FeatureCollection([
    ee.Feature(ee.Geometry.Polygon([[[73.714, 24.351], [73.722, 24.351], [73.722, 24.357], [73.714, 24.357]]]), {"class": 0}),
    ee.Feature(ee.Geometry.Polygon([[[73.725, 24.352], [73.733, 24.352], [73.733, 24.358], [73.725, 24.358]]]), {"class": 0}),
    ee.Feature(ee.Geometry.Polygon([[[73.708, 24.343], [73.715, 24.343], [73.715, 24.349], [73.708, 24.349]]]), {"class": 0}),
])
settlement_zones = ee.FeatureCollection([
    ee.Feature(ee.Geometry.Polygon([[[73.702, 24.356], [73.708, 24.356], [73.708, 24.362], [73.702, 24.362]]]), {"class": 1}),
    ee.Feature(ee.Geometry.Polygon([[[73.723, 24.365], [73.728, 24.365], [73.728, 24.370], [73.723, 24.370]]]), {"class": 1}),
])
forest_zones = ee.FeatureCollection([
    ee.Feature(ee.Geometry.Polygon([[[73.682, 24.320], [73.692, 24.320], [73.692, 24.330], [73.682, 24.330]]]), {"class": 2}),
    ee.Feature(ee.Geometry.Polygon([[[73.740, 24.310], [73.750, 24.310], [73.750, 24.320], [73.740, 24.320]]]), {"class": 2}),
    ee.Feature(ee.Geometry.Polygon([[[73.678, 24.360], [73.688, 24.360], [73.688, 24.370], [73.678, 24.370]]]), {"class": 2}),
])
water_zones = ee.FeatureCollection([
    ee.Feature(ee.Geometry.Polygon([[[73.720, 24.340], [73.724, 24.340], [73.724, 24.344], [73.720, 24.344]]]), {"class": 3}),
    ee.Feature(ee.Geometry.Polygon([[[73.714, 24.330], [73.718, 24.330], [73.718, 24.334], [73.714, 24.334]]]), {"class": 3}),
])
all_training_zones = mine_zones.merge(settlement_zones).merge(forest_zones).merge(water_zones)

# ---------------------------------------------------------------------------
# Sampling & Training (SAME seeds as mineops_pipeline.py — guaranteed match)
# ---------------------------------------------------------------------------
print("[Evaluation] Fetching baseline image and features...")
baseline_img = get_annual_clean_image(BASELINE_YEAR)

training_samples = baseline_img.select(PREDICTOR_BANDS).sampleRegions(
    collection=all_training_zones,
    properties=["class"],
    scale=SCALE,
    tileScale=4
)

# SAME seed=42 as mineops_pipeline.py → identical 5% subsample every run
training_samples = training_samples.randomColumn("subsample", seed=42).filter(ee.Filter.lt("subsample", 0.05))
# SAME seed=42 → identical 80:20 split every run
training_samples = training_samples.randomColumn("random", seed=42)
train_set = training_samples.filter(ee.Filter.lt("random", 0.8))
test_set  = training_samples.filter(ee.Filter.gte("random", 0.8))

train_count = train_set.size().getInfo()
test_count  = test_set.size().getInfo()
print(f"  [OK] Train set: {train_count} pixels | Test set: {test_count} pixels")

print("[Evaluation] Training Random Forest model...")
classifier = ee.Classifier.smileRandomForest(numberOfTrees=100).train(
    features=train_set,
    classProperty="class",
    inputProperties=PREDICTOR_BANDS
)

# ---------------------------------------------------------------------------
# Error Matrix & Metrics
# ---------------------------------------------------------------------------
test_classified = test_set.classify(classifier)
error_matrix    = test_classified.errorMatrix("class", "classification")
cm              = np.array(error_matrix.getInfo())
overall_acc     = error_matrix.accuracy().getInfo()
kappa           = error_matrix.kappa().getInfo()

# Verify total test pixels in confusion matrix equals test_count
cm_total = int(cm.sum())

print("\n" + "=" * 60)
print(f"  OVERALL VALIDATION ACCURACY : {overall_acc * 100:.2f}%")
print(f"  COHEN'S KAPPA COEFFICIENT   : {kappa:.4f}")
print(f"  TEST SET SIZE               : {test_count} pixels")
print(f"  CONFUSION MATRIX TOTAL PIXELS: {cm_total} pixels")
if test_count == cm_total:
    print("  [OK] Test pixel count matches confusion matrix total exactly!")
else:
    print(f"  [WARNING] Mismatch: test_count={test_count} vs cm_total={cm_total}")
print("=" * 60)

classes = ["Mines", "Settlement", "Forests", "Water"]
print("\n" + "-" * 65)
print(f"{'Class Name':<15} | {'Precision (User)':<18} | {'Recall (Prod)':<16} | {'F1-Score'}")
print("-" * 65)

metrics = []
for i, name in enumerate(classes):
    tp = cm[i, i]
    fn = np.sum(cm[i, :]) - tp
    fp = np.sum(cm[:, i]) - tp
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1        = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    metrics.append({"class": name, "precision": precision, "recall": recall, "f1": f1})
    print(f"{name:<15} | {precision*100:<17.2f}% | {recall*100:<15.2f}% | {f1:.4f}")

print("-" * 65)

# ---------------------------------------------------------------------------
# PLOT 1: Confusion Matrix Heatmap
# ---------------------------------------------------------------------------
os.makedirs("outputs", exist_ok=True)
fig, ax = plt.subplots(figsize=(7, 6), dpi=300)
cax = ax.matshow(cm, cmap=plt.cm.Blues, alpha=0.85)
for i in range(len(classes)):
    for j in range(len(classes)):
        ax.text(x=j, y=i, s=int(cm[i, j]), va='center', ha='center', fontsize=12, fontweight='bold')
plt.title(f"Confusion Matrix — Test Set ({cm_total} pixels)", fontsize=13, pad=20, fontweight='bold')
fig.colorbar(cax)
ax.set_xticks(range(len(classes))); ax.set_yticks(range(len(classes)))
ax.set_xticklabels(classes, fontsize=11); ax.set_yticklabels(classes, fontsize=11)
ax.set_xlabel("Predicted Class", fontsize=12, fontweight='bold', labelpad=10)
ax.set_ylabel("True Class (Ground Truth)", fontsize=12, fontweight='bold')
plt.tight_layout()
plt.savefig("outputs/confusion_matrix.png")
plt.close()
print(f"\n[OK] Confusion matrix saved  -> outputs/confusion_matrix.png")

# ---------------------------------------------------------------------------
# PLOT 2: Class-Wise Accuracy Bar Chart
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=300)
x = np.arange(len(classes)); width = 0.28
ax.bar(x - width, [m["precision"] * 100 for m in metrics], width, label='Precision (User Accuracy)', color='#4285F4')
ax.bar(x,         [m["recall"] * 100 for m in metrics],    width, label='Recall (Producer Accuracy)', color='#34A853')
ax.bar(x + width, [m["f1"] * 100 for m in metrics],        width, label='F1-Score (%)', color='#FBBC05')
ax.set_ylabel('Score (%)', fontsize=12)
ax.set_title('Class-Wise Accuracy — Zawar 4-Class Classifier', fontsize=13, fontweight='bold')
ax.set_xticks(x); ax.set_xticklabels(classes, fontsize=11)
ax.set_ylim([0, 110]); ax.grid(axis='y', linestyle='--', alpha=0.7)
ax.legend(loc='lower right')
plt.tight_layout()
plt.savefig("outputs/class_accuracy_barchart.png")
plt.close()
print(f"[OK] Class accuracy chart saved -> outputs/class_accuracy_barchart.png")
