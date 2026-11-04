import matplotlib.pyplot as plt
import numpy as np
import os

print("Generating strategy comparison chart...")

# Define the three methodologies
strategies = [
    'Zero-Shot U-Net\n(Global Only)',
    'Random Forest',
    'Fine-Tuned U-Net'
]

# Final Evaluation Metrics
iou_scores = [0.0221, 0.6200, 0.6821]

# Estimating RF F1 score mathematically from its ~0.62 IoU (F1 = 2*IoU / (1+IoU))
f1_scores = [0.0433, 0.7654, 0.8110]

x = np.arange(len(strategies))
width = 0.35

# Build the Grouped Bar Chart
fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
rects1 = ax.bar(x - width/2, iou_scores, width,
                label='Intersection over Union (IoU)', color='#FF6B6B')
rects2 = ax.bar(x + width/2, f1_scores, width,
                label='Dice/F1 Score', color='#4ECDC4')

ax.set_ylabel('Performance Score (0 to 1)', fontsize=12, fontweight='bold')
ax.set_title('MineOps Detection Strategies: Performance Comparison',
             fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(strategies, fontsize=11, fontweight='bold')
ax.legend(loc='upper left', fontsize=10)
ax.set_ylim(0, 1.0)
ax.grid(axis='y', linestyle='--', alpha=0.7)

# Attach text labels above each bar


def autolabel(rects):
    for rect in rects:
        height = rect.get_height()
        ax.annotate(f'{height:.4f}',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 5),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=10, fontweight='bold')


autolabel(rects1)
autolabel(rects2)

fig.tight_layout()
os.makedirs("outputs/reports", exist_ok=True)
plt.savefig("outputs/reports/strategy_comparison.png")
print("[OK] Chart saved to outputs/reports/strategy_comparison.png")
