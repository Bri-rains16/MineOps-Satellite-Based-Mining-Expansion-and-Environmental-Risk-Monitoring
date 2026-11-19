import { Router } from 'express';
import { validateYear } from '../services/dataReader.js';
import {
  getOverviewData,
  getRfData,
  getUnetData,
  getProximityData
} from '../services/mineopsService.js';

const router = Router();

  // GET /api/health
router.get('/health', (req, res) => {
  res.status(200).json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    service: 'mineops-backend-api',
    uptime_seconds: Math.floor(process.uptime())
  });
});

//   GET /api/overview?year=2026
router.get('/overview', (req, res, next) => {
  try {
    const rawYear = req.query.year !== undefined ? req.query.year : 2026;
    const { valid, year, error } = validateYear(rawYear);
    if (!valid) {
      return res.status(400).json({ error: error });
    }
    const data = getOverviewData(year);
    res.status(200).json(data);
  } catch (err) {
    next(err);
  }
});


//  GET /api/rf/:year

router.get('/rf/:year', (req, res, next) => {
  try {
    const { valid, year, error } = validateYear(req.params.year);
    if (!valid) {
      return res.status(400).json({ error: error });
    }
    const data = getRfData(year);
    res.status(200).json(data);
  } catch (err) {
    next(err);
  }
});

//  GET /api/unet/:year

router.get('/unet/:year', (req, res, next) => {
  try {
    const { valid, year, error } = validateYear(req.params.year);
    if (!valid) {
      return res.status(400).json({ error: error });
    }
    const data = getUnetData(year);
    res.status(200).json(data);
  } catch (err) {
    next(err);
  }
});

//  GET /api/proximity/:year
router.get('/proximity/:year', (req, res, next) => {
  try {
    const { valid, year, error } = validateYear(req.params.year);
    if (!valid) {
      return res.status(400).json({ error: error });
    }
    const data = getProximityData(year);
    res.status(200).json(data);
  } catch (err) {
    next(err);
  }
});

export default router;
