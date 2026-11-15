// Genuine project metadata and multi-year metrics extracted from authentic analytical runs
export const ZAWAR_AOI = {
  center: [24.3450, 73.7180],
  bounds: [
    [24.2972, 73.6736],
    [24.3778, 73.7597]
  ],
  zoom: 13,
  name: "Zawar Lead-Zinc Mining Region, Udaipur (Rajasthan)",
  areaHa: 7955.83,
  crs: "EPSG:32643 (UTM Zone 43N)",
  geographicCrs: "EPSG:4326 (WGS84)"
};

export const COLOR_PALETTE = {
  mine: "#E74C3C",        // Class 0: Mine/Bare Land (Coral Red)
  settlement: "#F39C12",  // Class 1: Settlement (Warm Amber)
  forest: "#27AE60",      // Class 2: Forest/Vegetation (Forest Green)
  water: "#2980B9",       // Class 3: Water Bodies (River Blue)
  buffer250: "#F39C12",   // 250m Impact Buffer
  buffer500: "#9B59B6",   // 500m Impact Buffer (Amethyst)
  buffer1000: "#8E44AD",  // 1000m Impact Buffer (Deep Purple)
  unetMask: "#E11D48",    // U-Net Prototype Mask (Crimson)
  accent: "#0D9488",      // Teal Primary
  navyDark: "#0F172A",    // Deep Navy
  navySidebar: "#1E293B"  // Slate Navy
};

// Extracted directly from outputs/polygons_rf_clean_2021-2026/rf_clean_area_summary_2021_2026.csv
// and outputs/proximity_rf_clean_2021-2026/proximity_clean_summary.csv
export const GENUINE_RF_METRICS = [
  {
    year: 2021,
    mineHa: 310.26,
    settlementHa: 909.10,
    forestHa: 6729.18,
    waterHa: 7.29,
    totalAreaHa: 7955.83,
    componentCount: 98,
    waterDistMin: 0.0,
    waterDistMedian: 396.1,
    waterDistMean: 528.34,
    forestDistMin: 0.0,
    forestDistMedian: 0.0,
    forestDistMean: 5.78,
    settlementDistMin: 0.0,
    settlementDistMedian: 0.0,
    settlementDistMean: 3.68
  },
  {
    year: 2022,
    mineHa: 279.79,
    settlementHa: 1332.32,
    forestHa: 6335.13,
    waterHa: 8.59,
    totalAreaHa: 7955.83,
    componentCount: 72,
    waterDistMin: 0.0,
    waterDistMedian: 235.86,
    waterDistMean: 404.69,
    forestDistMin: 0.0,
    forestDistMedian: 0.0,
    forestDistMean: 8.94,
    settlementDistMin: 0.0,
    settlementDistMedian: 0.0,
    settlementDistMean: 1.11
  },
  {
    year: 2023,
    mineHa: 288.75,
    settlementHa: 2073.34,
    forestHa: 5573.90,
    waterHa: 16.45,
    totalAreaHa: 7955.83,
    componentCount: 79,
    waterDistMin: 0.0,
    waterDistMedian: 158.11,
    waterDistMean: 248.50,
    forestDistMin: 0.0,
    forestDistMedian: 0.0,
    forestDistMean: 6.72,
    settlementDistMin: 0.0,
    settlementDistMedian: 0.0,
    settlementDistMean: 0.00
  },
  {
    year: 2024,
    mineHa: 273.68,
    settlementHa: 1105.86,
    forestHa: 6549.98,
    waterHa: 15.06,
    totalAreaHa: 7955.83,
    componentCount: 67,
    waterDistMin: 0.0,
    waterDistMedian: 200.0,
    waterDistMean: 277.58,
    forestDistMin: 0.0,
    forestDistMedian: 0.0,
    forestDistMean: 8.81,
    settlementDistMin: 0.0,
    settlementDistMedian: 0.0,
    settlementDistMean: 0.00
  },
  {
    year: 2025,
    mineHa: 330.94,
    settlementHa: 1165.09,
    forestHa: 6448.71,
    waterHa: 11.09,
    totalAreaHa: 7955.83,
    componentCount: 109,
    waterDistMin: 0.0,
    waterDistMedian: 410.12,
    waterDistMean: 526.72,
    forestDistMin: 0.0,
    forestDistMedian: 0.0,
    forestDistMean: 9.37,
    settlementDistMin: 0.0,
    settlementDistMedian: 0.0,
    settlementDistMean: 10.95
  },
  {
    year: 2026,
    mineHa: 301.14,
    settlementHa: 1105.50,
    forestHa: 6539.83,
    waterHa: 9.36,
    totalAreaHa: 7955.83,
    componentCount: 81,
    waterDistMin: 0.0,
    waterDistMedian: 160.0,
    waterDistMean: 341.30,
    forestDistMin: 0.0,
    forestDistMedian: 0.0,
    forestDistMean: 11.26,
    settlementDistMin: 0.0,
    settlementDistMedian: 0.0,
    settlementDistMean: 0.96
  }
];

// Single Source of Truth: outputs/reports/unet_expansion.json
import unetExpansionData from "./unet_expansion.json";

export const UNET_TARGET_STATS = unetExpansionData.map((d) => ({
  year: d.year,
  areaHa: d.area_hectares,
  expansionHa: d.expansion_ha,
  status: d.year === 2021 ? "Baseline (Calibrated Target)" : "Calibrated Target"
}));

// Extracted directly from outputs/proximity_rf_clean_2021-2026/buffer_exposure/buffer_exposure_clean_YYYY.csv
export const BUFFER_EXPOSURE_STATS = [
  {
    year: 2021,
    b250: { settlementHa: 511.30, settlementPct: 56.24, waterHa: 5.05, waterPct: 69.27, forestHa: 1963.04, forestPct: 29.17, totalBufferHa: 3667.95 },
    b500: { settlementHa: 753.43, settlementPct: 82.88, waterHa: 6.23, waterPct: 85.46, forestHa: 4138.37, forestPct: 61.50, totalBufferHa: 7055.78 },
    b1000: { settlementHa: 898.23, settlementPct: 98.80, waterHa: 7.20, waterPct: 98.77, forestHa: 6160.39, forestPct: 91.55, totalBufferHa: 11251.55 }
  },
  {
    year: 2022,
    b250: { settlementHa: 539.50, settlementPct: 40.50, waterHa: 3.51, waterPct: 40.86, forestHa: 1452.65, forestPct: 22.96, totalBufferHa: 3164.40 },
    b500: { settlementHa: 879.16, settlementPct: 65.99, waterHa: 4.44, waterPct: 51.69, forestHa: 3119.78, forestPct: 49.31, totalBufferHa: 6139.24 },
    b1000: { settlementHa: 1191.69, settlementPct: 89.45, waterHa: 6.20, waterPct: 72.18, forestHa: 5049.09, forestPct: 79.80, totalBufferHa: 10410.09 }
  },
  {
    year: 2023,
    b250: { settlementHa: 837.84, settlementPct: 40.41, waterHa: 6.43, waterPct: 39.09, forestHa: 1351.00, forestPct: 24.24, totalBufferHa: 3368.37 },
    b500: { settlementHa: 1542.40, settlementPct: 74.40, waterHa: 9.25, waterPct: 56.23, forestHa: 3200.27, forestPct: 57.42, totalBufferHa: 6892.42 },
    b1000: { settlementHa: 2056.72, settlementPct: 99.21, waterHa: 15.66, waterPct: 95.20, forestHa: 5099.13, forestPct: 91.48, totalBufferHa: 11339.21 }
  },
  {
    year: 2024,
    b250: { settlementHa: 437.25, settlementPct: 39.54, waterHa: 6.57, waterPct: 43.65, forestHa: 1560.49, forestPct: 23.84, totalBufferHa: 3175.20 },
    b500: { settlementHa: 739.47, settlementPct: 66.87, waterHa: 8.10, waterPct: 53.82, forestHa: 3373.99, forestPct: 51.55, totalBufferHa: 6259.32 },
    b1000: { settlementHa: 1041.17, settlementPct: 94.15, waterHa: 12.93, waterPct: 85.91, forestHa: 5440.48, forestPct: 83.12, totalBufferHa: 10659.47 }
  },
  {
    year: 2025,
    b250: { settlementHa: 642.63, settlementPct: 55.16, waterHa: 7.59, waterPct: 68.44, forestHa: 2036.29, forestPct: 31.58, totalBufferHa: 3896.37 },
    b500: { settlementHa: 991.15, settlementPct: 85.07, waterHa: 10.23, waterPct: 92.25, forestHa: 4256.02, forestPct: 66.00, totalBufferHa: 7436.49 },
    b1000: { settlementHa: 1159.68, settlementPct: 99.54, waterHa: 11.09, waterPct: 100.00, forestHa: 6214.84, forestPct: 96.37, totalBufferHa: 11592.22 }
  },
  {
    year: 2026,
    b250: { settlementHa: 510.20, settlementPct: 46.15, waterHa: 4.73, waterPct: 50.53, forestHa: 1671.80, forestPct: 25.56, totalBufferHa: 3367.86 },
    b500: { settlementHa: 834.94, settlementPct: 75.53, waterHa: 5.75, waterPct: 61.43, forestHa: 3668.65, forestPct: 56.10, totalBufferHa: 6657.73 },
    b1000: { settlementHa: 1090.75, settlementPct: 98.67, waterHa: 8.70, waterPct: 92.95, forestHa: 5979.23, forestPct: 91.43, totalBufferHa: 11255.14 }
  }
];

export const SATELLITE_SPECIFICATIONS = {
  sensor: "Sentinel-2 MultiSpectral Instrument (MSI)",
  resolution: "10 m Ground Sampling Distance",
  crsProjected: "EPSG:32643 (UTM Zone 43N)",
  crsGeographic: "EPSG:4326 (WGS84)",
  temporalRange: "2021 – 2026 (Pre-Monsoon March–May)",
  rfMethodology: "Ojha et al. (2025) Stacked Spectral Ratios + 150-Tree RF",
  rfValidationAccuracy: "79.94%",
  rfKappa: "0.7030",
  unetStatus: "Prototype / Area-Calibrated Multi-Temporal Masks"
};
