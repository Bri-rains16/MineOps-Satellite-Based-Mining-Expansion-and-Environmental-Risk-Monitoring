import json
import matplotlib.pyplot as plt

with open("outputs/expansion_summary.json", "r") as f:
    data = json.load(f)

years = [d["year"] for d in data]
areas = [d["area_hectares"] for d in data]

plt.figure(figsize=(10, 5), dpi=300)
plt.plot(years, areas, marker='o', linewidth=2.5, markersize=8, color='#d9534f', label='Active Mine Footprint')
plt.title("Zawar Lead-Zinc Mine Footprint Expansion (2021 - 2026)", fontsize=14, fontweight='bold')
plt.xlabel("Year", fontsize=12)
plt.ylabel("Detected Area (Hectares)", fontsize=12)
plt.grid(True, linestyle='--', alpha=0.6)

for y, a in zip(years, areas):
    plt.annotate(f"{a:.1f} ha", (y, a), textcoords="offset points", xytext=(0, 10), ha='center', fontweight='semibold')

plt.tight_layout()
plt.savefig("outputs/mine_expansion_trend.png")
print("[OK] Expansion chart saved to outputs/mine_expansion_trend.png")
