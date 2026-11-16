import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import apiRouter from './routes/api.js';
import downloadRouter from './routes/download.js';

dotenv.config();

const app = express();

// Middleware
app.use(cors());
app.use(express.json());

// Request logging in development
if (process.env.NODE_ENV !== 'test') {
  app.use((req, res, next) => {
    console.log(`[${new Date().toISOString()}] ${req.method} ${req.url}`);
    next();
  });
}

// Routes
app.use('/api', apiRouter);
app.use('/api/download', downloadRouter);

// 404 Handler for undefined routes
app.use((req, res) => {
  res.status(404).json({ error: `Route not found: ${req.method} ${req.originalUrl}` });
});

// Centralized error handling middleware
app.use((err, req, res, next) => {
  const statusCode = err.statusCode || 500;
  console.error(`Error processing ${req.method} ${req.url}:`, err.message);
  
  res.status(statusCode).json({
    error: err.message || 'Internal Server Error',
    statusCode
  });
});

export default app;
