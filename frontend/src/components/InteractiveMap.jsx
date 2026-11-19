import React, { useState } from "react";
import { MapContainer, TileLayer, GeoJSON, Circle, Popup, ScaleControl } from "react-leaflet";
import { ZAWAR_AOI, COLOR_PALETTE } from "../data/placeholderData";
import actualPolygonsData from "../data/actual_polygons.json";
import aoiGeoJson from "../data/aoi.json";
import { Layers } from "lucide-react";

export default function InteractiveMap({
  height = "520px",
  activeYear = 2026,
  showBufferControls = false,
  showUnetOverlay = false,
  showAoiBoundary = true,
  externalBufferRadius = null,
  onBufferChange = null,
  activeClassFilter = { mine: true, settlement: true, forest: true, water: true },
  onSelectFeature = null,
  geojsonData = null,
  bufferLayerData = null
}) {
  const [baseLayer, setBaseLayer] = useState("satellite"); // 'satellite' | 'streets'
  const [internalBufferRadius, setInternalBufferRadius] = useState(500);
  const [displayAoi, setDisplayAoi] = useState(showAoiBoundary);

  const activeBuffer = externalBufferRadius !== null ? externalBufferRadius : internalBufferRadius;
  const handleBufferSelect = (radius) => {
    if (onBufferChange) {
      onBufferChange(radius);
    } else {
      setInternalBufferRadius(radius);
    }
  };

  // Extract actual polygons for active year (fallback when geojsonData is not supplied)
  const yearPolygons = actualPolygonsData[activeYear] || actualPolygonsData[2021] || [];

  const getStyleForFeature = (feature) => {
    const isWater = feature.class_id === 3;
    if (showUnetOverlay && !isWater) {
      return {
        color: COLOR_PALETTE.unetMask,
        fillColor: COLOR_PALETTE.unetMask,
        fillOpacity: 0.8,
        weight: 1.5
      };
    }
    return {
      color: isWater ? COLOR_PALETTE.water : COLOR_PALETTE.mine,
      fillColor: isWater ? COLOR_PALETTE.water : COLOR_PALETTE.mine,
      fillOpacity: isWater ? 0.75 : 0.7,
      weight: 1.5
    };
  };

  const getStyleForGeoJsonFeature = (feature) => {
    const props = feature?.properties || {};
    const classId = props.class_id;
    const className = (props.class_name || "").toLowerCase();
    const defaultColor = props.fill_color;

    // Handle binary mining segmentation (e.g. U-Net masks or mining polygons without RF class properties)
    const isMining = showUnetOverlay || classId === 0 || className.includes("mine") || props.component_id;
    if (isMining && (showUnetOverlay || !defaultColor)) {
      const fillColor = showUnetOverlay ? COLOR_PALETTE.unetMask : COLOR_PALETTE.mine;
      return {
        color: fillColor,
        fillColor: fillColor,
        fillOpacity: showUnetOverlay ? 0.8 : 0.7,
        weight: 1.5
      };
    }

    // Environmental feature classification matching (e.g., water, forest, settlement)
    if (defaultColor) {
      return {
        color: defaultColor,
        fillColor: defaultColor,
        fillOpacity: classId === 3 || className.includes("water") ? 0.75 : 0.65,
        weight: 1.5
      };
    }

    if (classId === 3 || className.includes("water")) {
      return { color: COLOR_PALETTE.water, fillColor: COLOR_PALETTE.water, fillOpacity: 0.75, weight: 1.5 };
    }
    if (classId === 2 || className.includes("forest") || className.includes("veg")) {
      return { color: COLOR_PALETTE.forest, fillColor: COLOR_PALETTE.forest, fillOpacity: 0.65, weight: 1.5 };
    }
    if (classId === 1 || className.includes("settle")) {
      return { color: COLOR_PALETTE.settlement, fillColor: COLOR_PALETTE.settlement, fillOpacity: 0.65, weight: 1.5 };
    }

    return {
      color: "#64748B",
      fillColor: "#64748B",
      fillOpacity: 0.6,
      weight: 1.5
    };
  };

  const filterGeoJsonFeature = (feature) => {
    const props = feature?.properties || {};
    const classId = props.class_id;
    const className = (props.class_name || "").toLowerCase();

    // If activeClassFilter is disabled or all true, allow all
    if (!activeClassFilter) return true;

    // If it's a binary mining layer (U-Net or mine components GeoJSON)
    if (classId === undefined && !className) {
      // Unspecified features default to mine visibility
      return activeClassFilter.mine ?? true;
    }

    if ((classId === 0 || className.includes("mine") || props.component_id) && !activeClassFilter.mine) return false;
    if ((classId === 1 || className.includes("settle")) && !activeClassFilter.settlement) return false;
    if ((classId === 2 || className.includes("forest") || className.includes("veg")) && !activeClassFilter.forest) return false;
    if ((classId === 3 || className.includes("water")) && !activeClassFilter.water) return false;

    return true;
  };

  return (
    <div className="relative rounded-xl border border-slate-200 overflow-hidden shadow-xs bg-slate-100 flex flex-col">
      {/* Top Map Header / Quick Controls */}
      <div className="bg-white/95 backdrop-blur-xs px-4 py-2.5 border-b border-slate-200 flex flex-wrap items-center justify-between gap-3 z-30">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-teal-500"></span>
          <h3 className="text-xs font-semibold text-slate-800">
            Zawar Interactive Map Viewer <span className="text-slate-400 font-normal">({activeYear})</span>
          </h3>
          {/* <span className="text-[10px] text-slate-500 bg-slate-100 px-2 py-0.5 rounded border border-slate-200 font-mono">
            EPSG:4326 Display / EPSG:32643 Projected
          </span> */}
        </div>

        {/* Layer & Basemap Toggles */}
        <div className="flex items-center gap-2 text-xs">
          <button
            onClick={() => setBaseLayer(baseLayer === "satellite" ? "streets" : "satellite")}
            className="px-2.5 py-1 rounded border border-slate-200 text-slate-600 hover:bg-slate-50 font-medium text-[11px] flex items-center gap-1.5 cursor-pointer"
          >
            <Layers className="w-3.5 h-3.5 text-slate-500" />
            {baseLayer === "satellite" ? "Street Basemap" : "Satellite Basemap"}
          </button>

          <label className="flex items-center gap-1 cursor-pointer text-[11px] text-slate-600 pl-2 border-l border-slate-200">
            <input
              type="checkbox"
              checked={displayAoi}
              onChange={(e) => setDisplayAoi(e.target.checked)}
              className="rounded text-teal-600 w-3 h-3 cursor-pointer"
            />
            <span className="font-medium text-slate-700">AOI Perimeter</span>
          </label>

          {showBufferControls && (
            <div className="flex items-center gap-1.5 pl-2 border-l border-slate-200">
              <span className="text-[10px] text-slate-400">Buffer:</span>
              {[250, 500, 1000].map((r) => (
                <button
                  key={r}
                  onClick={() => handleBufferSelect(r)}
                  className={`px-2 py-0.5 text-[10px] font-semibold rounded transition-colors cursor-pointer ${
                    activeBuffer === r
                      ? "bg-amber-600 text-white"
                      : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                  }`}
                >
                  {r}m
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Map Viewport */}
      <div style={{ height }} className="w-full relative z-10">
        <MapContainer
          center={ZAWAR_AOI.center}
          zoom={ZAWAR_AOI.zoom}
          style={{ height: "100%", width: "100%" }}
          scrollWheelZoom={true}
        >
          {baseLayer === "satellite" ? (
            <TileLayer
              attribution='&copy; <a href="https://www.esri.com/">Esri World Imagery</a>'
              url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
              maxZoom={18}
            />
          ) : (
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              maxZoom={18}
            />
          )}

          <ScaleControl position="bottomleft" metric={true} imperial={false} />

          {/* Polygon Buffer Zones — rendered BELOW mining polygons */}
          {showBufferControls && bufferLayerData && (() => {
            const feat = bufferLayerData.features && bufferLayerData.features.find(
              (f) => f.properties && f.properties.buffer_m === activeBuffer
            );
            if (!feat) return null;
            const fc = { type: "FeatureCollection", features: [feat] };
            return (
              <GeoJSON
                key={`buffer-polygon-${activeBuffer}-${activeYear}`}
                data={fc}
                style={() => ({
                  color: feat.properties.color || "#9B59B6",
                  fillColor: feat.properties.fillColor || "#9B59B6",
                  fillOpacity: feat.properties.fillOpacity != null ? feat.properties.fillOpacity : 0.07,
                  weight: feat.properties.weight != null ? feat.properties.weight : 1.8,
                  dashArray: feat.properties.dashArray || "8, 5",
                  opacity: feat.properties.opacity != null ? feat.properties.opacity : 0.8,
                })}
              >
                <Popup>
                  <div className="p-1 font-sans text-xs">
                    <p className="font-bold text-slate-900">{feat.properties.label}</p>
                    <p className="text-slate-500 text-[10px]">Year: {feat.properties.year}</p>
                    <div className="mt-1 text-slate-700">
                      Area: <span className="font-semibold">{feat.properties.area_ha && feat.properties.area_ha.toFixed(1)} ha</span>
                    </div>
                  </div>
                </Popup>
              </GeoJSON>
            );
          })()}

          {/* Actual Study AOI Boundary (data/zawar/aoi.geojson) */}
          {displayAoi && (
            <GeoJSON
              key="zawar-aoi-boundary"
              data={aoiGeoJson}
              style={{
                color: "#0D9488", // Teal boundary
                weight: 2,
                dashArray: "6, 6",
                fillColor: "#0D9488",
                fillOpacity: 0.02
              }}
            >
              <Popup>
                <div className="p-1 font-sans text-xs">
                  <p className="font-bold text-teal-800">Study Area of Interest (AOI)</p>
                  <p className="text-slate-600 text-[11px] mt-1">Zawar Lead-Zinc Mining Region</p>
                  <div className="mt-1 text-[10px] text-slate-500 font-mono">
                    Extent: 7,955.83 ha &bull; UTM 43N
                  </div>
                </div>
              </Popup>
            </GeoJSON>
          )}

          {/* Render Backend GeoJSON Layer when provided */}
          {geojsonData && (
            <GeoJSON
              key={`backend-geojson-${activeYear}-${showUnetOverlay}-${JSON.stringify(activeClassFilter)}`}
              data={geojsonData}
              style={getStyleForGeoJsonFeature}
              filter={filterGeoJsonFeature}
              onEachFeature={(feature, layer) => {
                const props = feature.properties || {};
                const name = props.class_name || `Class ${props.class_id}`;
                const area = props.area_ha != null ? `${Number(props.area_ha).toFixed(2)} ha` : "N/A";
                const epoch = props.year || activeYear;

                layer.bindPopup(`
                  <div class="p-1 font-sans text-xs">
                    <p class="font-bold text-slate-900">${name}</p>
                    <p class="text-slate-500 text-[10px]">Class ID: ${props.class_id ?? "N/A"}</p>
                    <div class="mt-2 space-y-1 text-slate-700">
                      <div class="flex justify-between gap-4">
                        <span>Area:</span>
                        <span class="font-semibold text-slate-900">${area}</span>
                      </div>
                      <div class="flex justify-between gap-4">
                        <span>CRS:</span>
                        <span class="font-mono text-[10px]">EPSG:32643 / WGS84</span>
                      </div>
                      <div class="flex justify-between gap-4">
                        <span>Epoch:</span>
                        <span class="font-medium text-teal-600">${epoch}</span>
                      </div>
                    </div>
                  </div>
                `);

                layer.on({
                  click: () => {
                    if (onSelectFeature) {
                      onSelectFeature({
                        id: `${name}_${epoch}`,
                        class_id: props.class_id,
                        class_name: name,
                        area_ha: props.area_ha,
                        geojson: feature.geometry
                      });
                    }
                  }
                });
              }}
            />
          )}

          {/* Render Extracted Component Polygons Fallback when geojsonData is not provided */}
          {!geojsonData && yearPolygons.map((poly) => {
            const isWater = poly.class_id === 3;
            if (isWater && !activeClassFilter.water) return null;
            if (!isWater && !activeClassFilter.mine) return null;

            // Approximate centroid point for buffer rendering
            const coords = poly.geojson.type === "Polygon" 
              ? poly.geojson.coordinates[0][0] 
              : poly.geojson.coordinates[0][0][0];
            const centerLatLon = [coords[1], coords[0]];

            return (
              <React.Fragment key={poly.id}>
                {/* Proximity Impact Buffers around major mine components */}
                {showBufferControls && !isWater && !bufferLayerData && (
                  <Circle
                    center={centerLatLon}
                    radius={activeBuffer}
                    pathOptions={{ 
                      color: activeBuffer === 250 ? "#F39C12" : activeBuffer === 500 ? "#9B59B6" : "#8E44AD", 
                      weight: 1.2, 
                      dashArray: "4, 4",
                      fillOpacity: activeBuffer === 250 ? 0.08 : 0.05 
                    }}
                  />
                )}

                {/* Actual Polygon Geometry */}
                <GeoJSON
                  key={`${poly.id}-${activeYear}-${showUnetOverlay}`}
                  data={poly.geojson}
                  style={getStyleForFeature(poly)}
                  eventHandlers={{
                    click: () => {
                      if (onSelectFeature) onSelectFeature(poly);
                    }
                  }}
                >
                  <Popup>
                    <div className="p-1 font-sans text-xs">
                      <p className="font-bold text-slate-900">{poly.id}</p>
                      <p className="text-slate-500 text-[10px]">{poly.class_name}</p>
                      <div className="mt-2 space-y-1 text-slate-700">
                        <div className="flex justify-between gap-4">
                          <span>Area:</span>
                          <span className="font-semibold text-slate-900">{poly.area_ha} ha</span>
                        </div>
                        <div className="flex justify-between gap-4">
                          <span>CRS:</span>
                          <span className="font-mono text-[10px]">EPSG:32643</span>
                        </div>
                        <div className="flex justify-between gap-4">
                          <span>Epoch:</span>
                          <span className="font-medium text-teal-600">{activeYear}</span>
                        </div>
                      </div>
                    </div>
                  </Popup>
                </GeoJSON>
              </React.Fragment>
            );
          })}
        </MapContainer>
      </div>

      {/* Map Legend Footer */}
      <div className="bg-white px-4 py-2 border-t border-slate-200 text-xs flex flex-wrap items-center justify-between gap-3 text-slate-600">
        <div className="flex items-center gap-4 text-[11px]">
          <span className="font-semibold text-slate-700">Layers:</span>
          {showUnetOverlay ? (
            <span className="flex items-center gap-1.5 font-medium text-rose-700">
              <span className="w-2.5 h-2.5 rounded-sm bg-[#E11D48]"></span> U-Net Prototype Mask (Binary 10m)
            </span>
          ) : (
            <>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-sm bg-[#E74C3C]"></span> Mine/Bare Land
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-sm bg-[#F39C12]"></span> Settlement Matrix
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-sm bg-[#27AE60]"></span> Forest/Vegetation
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-sm bg-[#2980B9]"></span> Water Bodies
              </span>
            </>
          )}
          {displayAoi && (
            <span className="flex items-center gap-1.5 text-teal-700 font-medium">
              <span className="w-2.5 h-0.5 bg-teal-600 border-b border-dashed border-teal-600"></span> AOI Boundary
            </span>
          )}
          {showBufferControls && (
            <span className="flex items-center gap-1.5 text-amber-700 font-medium">
              <span className="w-2 h-2 rounded-full border border-dashed border-amber-600"></span> {bufferLayerData ? `Polygon Buffer (${activeBuffer}m)` : `Mine Centroid Buffer (${activeBuffer}m)`}
            </span>
          )}
        </div>
        <div className="text-[11px] text-slate-400">
          {showBufferControls ? bufferLayerData ? "Dissolved polygon buffer • EPSG:4326 • Computed from RF Mine class" : "Centroid indicator • See GIS Plate for raster/polygon buffer" : "EPSG:4326 GeoJSON • Verified against 10m Sentinel-2"}
        </div>
      </div>
    </div>
  );
}