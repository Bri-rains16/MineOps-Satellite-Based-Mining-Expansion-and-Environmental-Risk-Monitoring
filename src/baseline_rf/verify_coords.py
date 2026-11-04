import ee
ee.Initialize(project='mineguard-ai-507807')

worldcover = ee.ImageCollection('ESA/WorldCover/v200').first()

legend = {
    10: 'Trees/Forest',
    20: 'Shrubs',
    30: 'Grassland',
    40: 'Cropland',
    50: 'BuiltUp/Settlement',
    60: 'Bare/Sparse (Mine/Rock)',
    70: 'Snow/Ice',
    80: 'Water',
    90: 'Wetland',
    95: 'Mangrove',
    100: 'MossLichen'
}

polygons = {
    'Mine_Mochia':      ee.Geometry.Polygon([[[73.714, 24.351],[73.722, 24.351],[73.722, 24.357],[73.714, 24.357]]]),
    'Mine_Balaria':     ee.Geometry.Polygon([[[73.725, 24.352],[73.733, 24.352],[73.733, 24.358],[73.725, 24.358]]]),
    'Mine_Zawarmala':   ee.Geometry.Polygon([[[73.708, 24.343],[73.715, 24.343],[73.715, 24.349],[73.708, 24.349]]]),
    'Settl_Township':   ee.Geometry.Polygon([[[73.702, 24.356],[73.708, 24.356],[73.708, 24.362],[73.702, 24.362]]]),
    'Settl_Colony':     ee.Geometry.Polygon([[[73.723, 24.365],[73.728, 24.365],[73.728, 24.370],[73.723, 24.370]]]),
    'Forest_WestArav':  ee.Geometry.Polygon([[[73.682, 24.320],[73.692, 24.320],[73.692, 24.330],[73.682, 24.330]]]),
    'Forest_SEReserve': ee.Geometry.Polygon([[[73.740, 24.310],[73.750, 24.310],[73.750, 24.320],[73.740, 24.320]]]),
    'Forest_NWForest':  ee.Geometry.Polygon([[[73.678, 24.360],[73.688, 24.360],[73.688, 24.370],[73.678, 24.370]]]),
    'Water_TiriRiver':  ee.Geometry.Polygon([[[73.720, 24.340],[73.724, 24.340],[73.724, 24.344],[73.720, 24.344]]]),
    'Water_Reservoir':  ee.Geometry.Polygon([[[73.714, 24.330],[73.718, 24.330],[73.718, 24.334],[73.714, 24.334]]]),
}

print('--- ESA WorldCover v200 (10m) Verification ---')
print('Polygon Name           | ESA Dominant Class         | Code | Status')
print('-' * 75)

for name, geom in polygons.items():
    stats = worldcover.reduceRegion(
        reducer=ee.Reducer.mode(),
        geometry=geom,
        scale=10,
        maxPixels=1e8
    ).getInfo()
    code = int(stats.get('Map', 0))
    label = legend.get(code, f'Unknown ({code})')

    # Determine if what ESA says matches what we expect
    expected_prefix = name.split('_')[0]
    match = {
        'Mine':   code in [60, 50, 40],   # Bare/Sparse or BuiltUp acceptable for mines
        'Settl':  code in [50, 40],
        'Forest': code in [10, 20, 30],
        'Water':  code in [80, 90],
    }.get(expected_prefix, False)

    status = '[OK]  ' if match else '[WARN]'
    print(f'{name:<22} | {label:<26} | {code:>4} | {status}')
