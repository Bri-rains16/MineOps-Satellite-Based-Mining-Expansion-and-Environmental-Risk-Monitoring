import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export const PROJECT_ROOT = path.resolve(__dirname, '../../../');
export const OUTPUTS_DIR = path.join(PROJECT_ROOT, 'outputs');

export const VALID_YEARS = [2021, 2022, 2023, 2024, 2025, 2026];

/**
 * Validates whether the given year is a valid MineOps year (2021-2026).
 * @param {string|number} yearInput 
 * @returns {{ valid: boolean, year?: number, error?: string }}
 */
export function validateYear(yearInput) {
  if (yearInput === undefined || yearInput === null || String(yearInput).trim() === '') {
    return { valid: false, error: 'Year parameter is required.' };
  }
  const year = Number(yearInput);
  if (!Number.isInteger(year)) {
    return { valid: false, error: 'Year must be a valid integer.' };
  }
  if (!VALID_YEARS.includes(year)) {
    return { 
      valid: false, 
      error: `Year ${year} is invalid. Supported years are ${VALID_YEARS.join(', ')}.` 
    };
  }
  return { valid: true, year };
}

/**
 * Parses simple CSV content into an array of objects.
 * Handles numbers and trimmed strings.
 * @param {string} csvText 
 * @returns {Array<Record<string, any>>}
 */
export function parseCSV(csvText) {
  if (typeof csvText !== 'string' || !csvText.trim()) {
    return [];
  }
  const lines = csvText.trim().split(/\r?\n/).filter(line => line.trim().length > 0);
  if (lines.length < 2) {
    return [];
  }
  const headers = lines[0].split(',').map(h => h.trim());
  
  return lines.slice(1).map(line => {
    const values = line.split(',').map(v => v.trim());
    const row = {};
    headers.forEach((header, idx) => {
      const rawVal = values[idx] !== undefined ? values[idx] : '';
      if (rawVal === '') {
        row[header] = null;
      } else if (!isNaN(Number(rawVal))) {
        row[header] = Number(rawVal);
      } else {
        row[header] = rawVal;
      }
    });
    return row;
  });
}

/**
 * Safely reads and parses a JSON file.
 * @param {string} filePath 
 * @returns {any}
 */
export function readJSONFile(filePath) {
  if (!fs.existsSync(filePath)) {
    const error = new Error(`File not found: ${path.basename(filePath)}`);
    error.statusCode = 404;
    throw error;
  }
  const raw = fs.readFileSync(filePath, 'utf8');
  try {
    return JSON.parse(raw);
  } catch (err) {
    const error = new Error(`Malformed JSON in file: ${path.basename(filePath)}`);
    error.statusCode = 500;
    throw error;
  }
}

/**
 * Safely reads and parses a CSV file.
 * @param {string} filePath 
 * @returns {Array<Record<string, any>>}
 */
export function readCSVFile(filePath) {
  if (!fs.existsSync(filePath)) {
    const error = new Error(`File not found: ${path.basename(filePath)}`);
    error.statusCode = 404;
    throw error;
  }
  const raw = fs.readFileSync(filePath, 'utf8');
  return parseCSV(raw);
}
