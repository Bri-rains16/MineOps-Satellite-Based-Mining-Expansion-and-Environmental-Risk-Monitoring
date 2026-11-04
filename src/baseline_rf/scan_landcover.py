"""
Scan the entire Zawar AOI using ESA WorldCover v200 (10m authoritative reference)
to find the actual spatial locations of each land cover class.
This gives us scientifically verified coordinate candidates for training polygons.
"""
import ee
ee.Initialize(project='mineguard-ai-507807')

aoi = ee.Geometry.Rectangle([73.6736, 24.2972, 73.7597, 24.3778])
worldcover = ee.ImageCollection('ESA/WorldCover/v200').first().clip(aoi)

# ESA WorldCover class codes
legend = {
    10: 'Trees/Forest',
    20: 'Shrubs',
    30: 'Grassland',
    40: 'Cropland',
    50: 'BuiltUp/Settlement',
    60: 'Bare/Sparse (Mine/Rock)',
    80: 'Water',
    90: 'Wetland',
}

print("=== Step 1: Area of each class in our AOI ===")
for code, name in legend.items():
    mask = worldcover.eq(code)
    area = mask.multiply(ee.Image.pixelArea()).reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=aoi,
        scale=30,
        maxPixels=1e9
    ).getInfo()
    area_ha = area.get('Map', 0) / 10000.0
    print(f"  Code {code:>3} ({name:<28}): {area_ha:>8.1f} ha")

print()
print("=== Step 2: Centroid coordinates of each key class ===")
for code, name in legend.items():
    mask = worldcover.eq(code).selfMask()
    try:
        vectors = mask.reduceToVectors(
            geometry=aoi,
            scale=100,
            geometryType='centroid',
            maxPixels=1e8,
            bestEffort=True
        )
        count = vectors.size().getInfo()
        if count > 0:
            # Get a representative centroid
            sample = vectors.limit(5)
            coords_list = sample.toList(5).getInfo()
            print(f"  Code {code} ({name}):")
            for feat in coords_list[:3]:
                c = feat['geometry']['coordinates']
                print(f"    -> [{c[0]:.4f}, {c[1]:.4f}]")
    except Exception as e:
        print(f"  Code {code} ({name}): could not vectorize ({str(e)[:50]})")

print()
print("=== Step 3: Sample random points per class for training ===")
for code, name in [(50,'BuiltUp'), (60,'Bare/Mine'), (80,'Water')]:
    mask = worldcover.eq(code).selfMask()
    pts = mask.sample(
        region=aoi,
        scale=30,
        numPixels=20,
        seed=42,
        geometries=True
    )
    count = pts.size().getInfo()
    print(f"  Code {code} ({name:<12}): {count} sample points found")
    if count > 0:
        pts_list = pts.toList(count).getInfo()
        for feat in pts_list[:5]:
            c = feat['geometry']['coordinates']
            print(f"    [{c[0]:.5f}, {c[1]:.5f}]")
