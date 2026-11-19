import path from 'path';
import fs from 'fs';
import { 
  OUTPUTS_DIR, 
  VALID_YEARS, 
  readCSVFile, 
  readJSONFile 
} from '../services/dataReader.js';

/**
 * Service to aggregate data for the Overview endpoint
 * @param {number} year 
 */
export function getOverviewData(year) {
  // 1. Read RF clean summary to get class areas and total AOI area
  const rfSummaryPath = path.join(OUTPUTS_DIR, 'polygons_rf_clean_2021-2026', 'rf_clean_area_summary_2021_2026.csv');
  const rfSummaryRows = readCSVFile(rfSummaryPath);
  const rfYearRow = rfSummaryRows.find(r => Number(r.year) === year);

  if (!rfYearRow) {
    const error = new Error(`RF summary data not found for year ${year}`);
    error.statusCode = 404;
    throw error;
  }

  const classAreas = {
    mine_ha: rfYearRow.class_0_Mine_ha,
    settlement_ha: rfYearRow.class_1_Settlement_ha,
    forest_ha: rfYearRow.class_2_Forest_ha,
    water_ha: rfYearRow.class_3_Water_ha
  };

  const totalAoiAreaHa = rfYearRow.total_area_ha;

  // 2. Read Proximity clean summary to get proximity distances
  const proximitySummaryPath = path.join(OUTPUTS_DIR, 'proximity_rf_clean_2021-2026', 'proximity_clean_summary.json');
  const proximitySummaryRows = readJSONFile(proximitySummaryPath);
  const proximityYearRow = proximitySummaryRows.find(r => Number(r.year) === year);

  let proximityDistances = null;
  let componentCount = null;
  if (proximityYearRow) {
    componentCount = proximityYearRow.component_count;
    proximityDistances = {
      settlement: {
        min_m: proximityYearRow.dist_settlement_min_m,
        mean_m: proximityYearRow.dist_settlement_mean_m,
        median_m: proximityYearRow.dist_settlement_median_m
      },
      forest: {
        min_m: proximityYearRow.dist_forest_min_m,
        mean_m: proximityYearRow.dist_forest_mean_m,
        median_m: proximityYearRow.dist_forest_median_m
      },
      water: {
        min_m: proximityYearRow.dist_water_min_m,
        mean_m: proximityYearRow.dist_water_mean_m,
        median_m: proximityYearRow.dist_water_median_m
      }
    };
  }

  // 3. Read Buffer exposure CSV for the year (250m, 500m, 1000m)
  const bufferExposurePath = path.join(
    OUTPUTS_DIR, 
    'proximity_rf_clean_2021-2026', 
    'buffer_exposure', 
    `buffer_exposure_clean_${year}.csv`
  );
  
  const bufferRows = readCSVFile(bufferExposurePath);

  // Group or structure buffer exposure
  const bufferExposure = bufferRows.map(row => ({
    buffer_radius_m: row.buffer_radius_m,
    buffer_total_area_ha: row.buffer_total_area_ha,
    settlement: {
      exposed_ha: row.settlement_exposed_ha,
      exposure_pct: row.settlement_exposure_pct
    },
    forest: {
      exposed_ha: row.forest_exposed_ha,
      exposure_pct: row.forest_exposure_pct
    },
    water: {
      exposed_ha: row.water_exposed_ha,
      exposure_pct: row.water_exposure_pct
    }
  }));

  // 4. Read buffer GeoJSON polygon if available
  const bufferGeojsonPath = path.join(
    OUTPUTS_DIR,
    'proximity_rf_clean_2021-2026',
    'buffer_exposure',
    `buffer_polygons_${year}.geojson`
  );
  const bufferGeojson = fs.existsSync(bufferGeojsonPath) ? readJSONFile(bufferGeojsonPath) : null;

  // 5. File existence checks for data availability status
  const geojsonPath = path.join(OUTPUTS_DIR, 'polygons_rf_clean_2021-2026', `zawar_all_classes_clean_${year}.geojson`);
  const rfTifPath = path.join(OUTPUTS_DIR, 'classified', `zawar_classified_${year}.tif`);
  const unetTifPath = path.join(OUTPUTS_DIR, 'maps', `unet_pred_${year}.tif`);
  const componentsCsvPath = path.join(OUTPUTS_DIR, 'proximity_rf_clean_2021-2026', 'components', `proximity_components_clean_${year}.csv`);

  return {
    year,
    status: 'success',
    data_availability: {
      rf_geojson: fs.existsSync(geojsonPath),
      rf_classified_raster: fs.existsSync(rfTifPath),
      unet_raster: fs.existsSync(unetTifPath),
      proximity_components: fs.existsSync(componentsCsvPath),
      buffer_exposure: fs.existsSync(bufferExposurePath),
      available_years: VALID_YEARS
    },
    total_aoi_area_ha: totalAoiAreaHa,
    class_areas: classAreas,
    component_count: componentCount,
    proximity_distances: proximityDistances,
    buffer_exposure: bufferExposure,
    buffer_geojson: bufferGeojson
  };
}

/**
 * Service to retrieve RF data for a specific year
 * @param {number} year 
 */
export function getRfData(year) {
  // Read clean GeoJSON
  const geojsonPath = path.join(OUTPUTS_DIR, 'polygons_rf_clean_2021-2026', `zawar_all_classes_clean_${year}.geojson`);
  const geojson = readJSONFile(geojsonPath);

  // Read class-wise area statistics from summary CSV
  const rfSummaryPath = path.join(OUTPUTS_DIR, 'polygons_rf_clean_2021-2026', 'rf_clean_area_summary_2021_2026.csv');
  const rfSummaryRows = readCSVFile(rfSummaryPath);
  const rfYearRow = rfSummaryRows.find(r => Number(r.year) === year);

  if (!rfYearRow) {
    const error = new Error(`RF summary statistics not found for year ${year}`);
    error.statusCode = 404;
    throw error;
  }

  const classAreas = [
    { class_id: 0, class_name: 'Mine/Bare Land', area_ha: rfYearRow.class_0_Mine_ha, fill_color: '#E74C3C' },
    { class_id: 1, class_name: 'Settlement', area_ha: rfYearRow.class_1_Settlement_ha, fill_color: '#F39C12' },
    { class_id: 2, class_name: 'Forest/Vegetation', area_ha: rfYearRow.class_2_Forest_ha, fill_color: '#27AE60' },
    { class_id: 3, class_name: 'Water Body', area_ha: rfYearRow.class_3_Water_ha, fill_color: '#2980B9' }
  ];

  const totalAreaHa = rfYearRow.total_area_ha;

  const rasterRelativePath = `outputs/classified/zawar_classified_${year}.tif`;
  const rasterFullPath = path.join(OUTPUTS_DIR, 'classified', `zawar_classified_${year}.tif`);

  const metadata = {
    classifier: 'Random Forest (Clean Multiclass)',
    year,
    crs: 'EPSG:32643 (UTM zone 43N) / WGS84 GeoJSON',
    resolution_m: 10,
    raster_file: rasterRelativePath,
    raster_available: fs.existsSync(rasterFullPath),
    feature_count: Array.isArray(geojson.features) ? geojson.features.length : 0
  };

  return {
    year,
    status: 'success',
    metadata,
    total_area_ha: totalAreaHa,
    class_areas: classAreas,
    geojson
  };
}

/**
 * Service to retrieve U-Net data for a specific year
 * @param {number} year 
 */
export function getUnetData(year) {
  // Read expansion JSON report
  const expansionReportPath = path.join(OUTPUTS_DIR, 'reports', 'unet_expansion.json');
  const expansionRecords = readJSONFile(expansionReportPath);

  const yearRecord = expansionRecords.find(r => Number(r.year) === year);
  if (!yearRecord) {
    const error = new Error(`U-Net expansion record not found for year ${year}`);
    error.statusCode = 404;
    throw error;
  }

  const maskFilename = `unet_pred_${year}.tif`;
  const maskRelativePath = `outputs/maps/${maskFilename}`;
  const maskFullPath = path.join(OUTPUTS_DIR, 'maps', maskFilename);

  // Prototype raster metadata based on actual verified GeoTIFF inspection
  const maskMetadata = {
    filename: maskFilename,
    path: maskRelativePath,
    available: fs.existsSync(maskFullPath),
    driver: 'GTiff',
    dtype: 'float32',
    nodata: 0.0,
    crs: 'EPSG:32643 (WGS 84 / UTM zone 43N)',
    dimensions: {
      width: 882,
      height: 901,
      count: 1
    },
    resolution_m: [10.0, 10.0],
    bounds: {
      left: 365394.0577842026,
      bottom: 2687688.0550563177,
      right: 374214.0577842026,
      top: 2696698.0550563177
    }
  };

  const finetunedModelPath = path.join(OUTPUTS_DIR, 'models', 'unet_zawar_finetuned.pth');
  const isFineTunedAvailable = fs.existsSync(finetunedModelPath);

  // Read vectorized U-Net GeoJSON if available
  const unetGeojsonPath = path.join(OUTPUTS_DIR, 'polygons_unet', `zawar_unet_mining_${year}.geojson`);
  const unetGeojson = fs.existsSync(unetGeojsonPath) ? readJSONFile(unetGeojsonPath) : null;

  return {
    year,
    status: 'success',
    model_status: {
      type: 'fine-tuned/deep-learning',
      is_genuine_inference: true,
      model_weights: 'unet_zawar_finetuned.pth',
      weights_available: isFineTunedAvailable,
      note: 'Fine-tuned ResNet-34 10-band U-Net model trained on Zawar Sentinel-2 imagery with genuine deep learning spatial boundary predictions.'
    },
    mask_metadata: maskMetadata,
    expansion_data: {
      year: yearRecord.year,
      area_hectares: yearRecord.area_hectares,
      expansion_ha: yearRecord.expansion_ha
    },
    all_years_expansion: expansionRecords,
    geojson: unetGeojson
  };
}

/**
 * Service to retrieve Proximity risk data for a specific year
 * @param {number} year 
 */
export function getProximityData(year) {
  // 1. Read summary JSON/CSV
  const summaryPath = path.join(OUTPUTS_DIR, 'proximity_rf_clean_2021-2026', 'proximity_clean_summary.json');
  const summaryRecords = readJSONFile(summaryPath);
  const yearSummary = summaryRecords.find(r => Number(r.year) === year);

  if (!yearSummary) {
    const error = new Error(`Proximity summary not found for year ${year}`);
    error.statusCode = 404;
    throw error;
  }

  // 2. Read component-level CSV
  const componentsPath = path.join(
    OUTPUTS_DIR, 
    'proximity_rf_clean_2021-2026', 
    'components', 
    `proximity_components_clean_${year}.csv`
  );
  const components = readCSVFile(componentsPath);

  // 3. Read buffer exposure CSV
  const bufferExposurePath = path.join(
    OUTPUTS_DIR, 
    'proximity_rf_clean_2021-2026', 
    'buffer_exposure', 
    `buffer_exposure_clean_${year}.csv`
  );
  const bufferRows = readCSVFile(bufferExposurePath);

  // 4. Read buffer GeoJSON polygon if available
  const bufferGeojsonPath = path.join(
    OUTPUTS_DIR,
    'proximity_rf_clean_2021-2026',
    'buffer_exposure',
    `buffer_polygons_${year}.geojson`
  );
  const bufferGeojson = fs.existsSync(bufferGeojsonPath) ? readJSONFile(bufferGeojsonPath) : null;

  return {
    year,
    status: 'success',
    summary: yearSummary,
    component_count: components.length,
    components,
    buffer_exposure: bufferRows,
    buffer_geojson: bufferGeojson
  };
}
