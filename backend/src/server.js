import app from './app.js';

const PORT = process.env.PORT || 5000;

app.listen(PORT, () => {
  console.log(`MineOps REST API server running on port ${PORT} [${process.env.NODE_ENV || 'development'}]`);
  console.log(`Health check: http://localhost:${PORT}/api/health`);
  console.log(`Overview (2026): http://localhost:${PORT}/api/overview?year=2026`);
});
