import { Router } from 'express';
import path from 'path';
import fs from 'fs';
import { OUTPUTS_DIR } from '../services/dataReader.js';

const router = Router();

// Whitelist of downloadable subdirectories under outputs
const ALLOWED_SUBDIRS = [
  'classified',
  'maps',
  'polygons_rf_clean_2021-2026',
  'proximity_rf_clean_2021-2026',
  'reports'
];

/**
 * GET /api/download/*
 * Safely serves files from outputs directory
 */
router.get('/*', (req, res, next) => {
  try {
    const requestedPath = req.params[0];
    if (!requestedPath) {
      return res.status(400).json({ error: 'File path is required for download.' });
    }

    // Resolve path safely against OUTPUTS_DIR
    const resolvedPath = path.resolve(OUTPUTS_DIR, requestedPath);

    // Prevent directory traversal attacks
    if (!resolvedPath.startsWith(OUTPUTS_DIR)) {
      return res.status(403).json({ error: 'Access forbidden: Path traversal detected.' });
    }

    // Verify subpath is within allowed directories
    const relative = path.relative(OUTPUTS_DIR, resolvedPath);
    const topFolder = relative.split(path.sep)[0];
    if (!ALLOWED_SUBDIRS.includes(topFolder)) {
      return res.status(403).json({ error: 'Access forbidden: Directory not permitted for downloads.' });
    }

    if (!fs.existsSync(resolvedPath)) {
      return res.status(404).json({ error: 'Requested file not found.' });
    }

    const stat = fs.statSync(resolvedPath);
    if (!stat.isFile()) {
      return res.status(400).json({ error: 'Requested resource is not a file.' });
    }

    // Send the file
    res.download(resolvedPath);
  } catch (err) {
    next(err);
  }
});

export default router;
