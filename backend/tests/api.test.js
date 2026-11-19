import assert from 'assert';
import app from '../src/app.js';
import http from 'http';

// Helper to make local requests to the express app using Node http
function request(server, method, path) {
  return new Promise((resolve, reject) => {
    const address = server.address();
    const options = {
      hostname: '127.0.0.1',
      port: address.port,
      path: path,
      method: method
    };

    const req = http.request(options, (res) => {
      let body = '';
      res.on('data', (chunk) => { body += chunk; });
      res.on('end', () => {
        let json = null;
        try {
          json = JSON.parse(body);
        } catch (e) {
          json = body;
        }
        resolve({
          status: res.statusCode,
          headers: res.headers,
          body: json
        });
      });
    });

    req.on('error', (err) => reject(err));
    req.end();
  });
}

async function runTests() {
  console.log('--- Starting MineOps Backend API Tests ---');
  process.env.NODE_ENV = 'test';

  const server = app.listen(0); // Random free port

  try {
    // 1. Health check
    console.log('\n[TEST] 1. GET /api/health');
    const healthRes = await request(server, 'GET', '/api/health');
    assert.strictEqual(healthRes.status, 200);
    assert.strictEqual(healthRes.body.status, 'ok');
    assert.strictEqual(healthRes.body.service, 'mineops-backend-api');
    console.log('✓ /api/health passed');

    // 2. Overview endpoint (2021 & 2026)
    console.log('\n[TEST] 2. GET /api/overview?year=2021');
    const ov2021Res = await request(server, 'GET', '/api/overview?year=2021');
    assert.strictEqual(ov2021Res.status, 200);
    assert.strictEqual(ov2021Res.body.year, 2021);
    assert.strictEqual(ov2021Res.body.total_aoi_area_ha, 7955.83);
    assert.strictEqual(ov2021Res.body.class_areas.mine_ha, 310.26);
    assert.strictEqual(ov2021Res.body.buffer_exposure.length, 3);
    assert.strictEqual(ov2021Res.body.buffer_exposure[0].buffer_radius_m, 250);
    console.log('✓ /api/overview?year=2021 passed');

    console.log('\n[TEST] 3. GET /api/overview (Default to 2026)');
    const ovDefaultRes = await request(server, 'GET', '/api/overview');
    assert.strictEqual(ovDefaultRes.status, 200);
    assert.strictEqual(ovDefaultRes.body.year, 2026);
    assert.strictEqual(ovDefaultRes.body.total_aoi_area_ha, 7955.83);
    assert.strictEqual(ovDefaultRes.body.class_areas.mine_ha, 301.14);
    assert.strictEqual(ovDefaultRes.body.buffer_exposure.length, 3);
    assert.strictEqual(ovDefaultRes.body.buffer_exposure[0].buffer_radius_m, 250);
    assert.strictEqual(ovDefaultRes.body.buffer_exposure[0].settlement.exposed_ha, 510.2);
    console.log('✓ /api/overview (default 2026) passed');

    // 4. Random Forest endpoint (2021 & 2026)
    console.log('\n[TEST] 4. GET /api/rf/2021');
    const rf2021Res = await request(server, 'GET', '/api/rf/2021');
    assert.strictEqual(rf2021Res.status, 200);
    assert.strictEqual(rf2021Res.body.year, 2021);
    assert.strictEqual(rf2021Res.body.geojson.type, 'FeatureCollection');
    assert.ok(Array.isArray(rf2021Res.body.geojson.features));
    assert.ok(rf2021Res.body.geojson.features.length > 0);
    assert.strictEqual(rf2021Res.body.class_areas.length, 4);
    console.log(`✓ /api/rf/2021 passed (features count: ${rf2021Res.body.geojson.features.length})`);

    console.log('\n[TEST] 5. GET /api/rf/2026');
    const rf2026Res = await request(server, 'GET', '/api/rf/2026');
    assert.strictEqual(rf2026Res.status, 200);
    assert.strictEqual(rf2026Res.body.year, 2026);
    assert.strictEqual(rf2026Res.body.geojson.type, 'FeatureCollection');
    assert.ok(rf2026Res.body.geojson.features.length > 0);
    assert.strictEqual(rf2026Res.body.metadata.resolution_m, 10);
    console.log(`✓ /api/rf/2026 passed (features count: ${rf2026Res.body.geojson.features.length})`);

    // 6. U-Net endpoint (2021 & 2026)
    console.log('\n[TEST] 6. GET /api/unet/2021');
    const unet2021Res = await request(server, 'GET', '/api/unet/2021');
    assert.strictEqual(unet2021Res.status, 200);
    assert.strictEqual(unet2021Res.body.year, 2021);
    assert.strictEqual(unet2021Res.body.model_status.type, 'fine-tuned/deep-learning');
    assert.strictEqual(unet2021Res.body.model_status.is_genuine_inference, true);
    assert.strictEqual(unet2021Res.body.mask_metadata.filename, 'unet_pred_2021.tif');
    assert.strictEqual(unet2021Res.body.mask_metadata.available, true);
    assert.strictEqual(unet2021Res.body.expansion_data.area_hectares, 94.38);
    console.log('✓ /api/unet/2021 passed');

    console.log('\n[TEST] 7. GET /api/unet/2026');
    const unet2026Res = await request(server, 'GET', '/api/unet/2026');
    assert.strictEqual(unet2026Res.status, 200);
    assert.strictEqual(unet2026Res.body.year, 2026);
    assert.strictEqual(unet2026Res.body.model_status.is_genuine_inference, true);
    assert.strictEqual(unet2026Res.body.expansion_data.area_hectares, 117.51);
    assert.strictEqual(unet2026Res.body.expansion_data.expansion_ha, -14.67);
    console.log('✓ /api/unet/2026 passed');

    // 8. Proximity endpoint (2021 & 2026)
    console.log('\n[TEST] 8. GET /api/proximity/2021');
    const prox2021Res = await request(server, 'GET', '/api/proximity/2021');
    assert.strictEqual(prox2021Res.status, 200);
    assert.strictEqual(prox2021Res.body.year, 2021);
    assert.strictEqual(prox2021Res.body.component_count, 98);
    assert.strictEqual(prox2021Res.body.components.length, 98);
    assert.strictEqual(prox2021Res.body.buffer_exposure.length, 3);
    console.log('✓ /api/proximity/2021 passed (98 component records verified)');

    console.log('\n[TEST] 9. GET /api/proximity/2026');
    const prox2026Res = await request(server, 'GET', '/api/proximity/2026');
    assert.strictEqual(prox2026Res.status, 200);
    assert.strictEqual(prox2026Res.body.year, 2026);
    assert.strictEqual(prox2026Res.body.component_count, 81);
    assert.strictEqual(prox2026Res.body.components.length, 81);
    assert.strictEqual(prox2026Res.body.buffer_exposure.length, 3);
    console.log('✓ /api/proximity/2026 passed (81 component records verified)');

    // 9. Error handling: Invalid Year (400)
    console.log('\n[TEST] 10. GET /api/rf/2099 (Invalid year -> 400)');
    const errYearRes = await request(server, 'GET', '/api/rf/2099');
    assert.strictEqual(errYearRes.status, 400);
    assert.ok(errYearRes.body.error.includes('invalid'));
    console.log('✓ Invalid year 400 handled correctly');

    console.log('\n[TEST] 11. GET /api/overview?year=abc (Non-integer year -> 400)');
    const errNonIntRes = await request(server, 'GET', '/api/overview?year=abc');
    assert.strictEqual(errNonIntRes.status, 400);
    assert.ok(errNonIntRes.body.error.includes('valid integer'));
    console.log('✓ Non-integer year 400 handled correctly');

    // 10. Error handling: Route Not Found (404)
    console.log('\n[TEST] 12. GET /api/nonexistent-route (404)');
    const notFoundRes = await request(server, 'GET', '/api/nonexistent-route');
    assert.strictEqual(notFoundRes.status, 404);
    assert.ok(notFoundRes.body.error.includes('Route not found'));
    console.log('✓ Route not found 404 handled correctly');

    // 11. Download route testing
    console.log('\n[TEST] 13. GET /api/download/reports/unet_expansion.json');
    const downloadRes = await request(server, 'GET', '/api/download/reports/unet_expansion.json');
    assert.strictEqual(downloadRes.status, 200);
    assert.ok(Array.isArray(downloadRes.body));
    console.log('✓ Download route works for authorized outputs');

    console.log('\n[TEST] 14. GET /api/download/../../package.json (Path traversal attempt -> 403)');
    const traversalRes = await request(server, 'GET', '/api/download/../../package.json');
    assert.strictEqual(traversalRes.status, 403);
    console.log('✓ Path traversal blocked with 403 Forbidden');

    console.log('\n[TEST] 15. GET /api/download/reports/nonexistent_file.png (Missing file -> 404)');
    const missingFileRes = await request(server, 'GET', '/api/download/reports/nonexistent_file.png');
    assert.strictEqual(missingFileRes.status, 404);
    console.log('✓ Missing download file handled with 404');

    console.log('\n=============================================');
    console.log('ALL BACKEND API TESTS PASSED SUCCESSFULLY! ✅');
    console.log('=============================================');

  } finally {
    server.close();
  }
}

runTests().catch(err => {
  console.error('Test execution failed:', err);
  process.exit(1);
});
