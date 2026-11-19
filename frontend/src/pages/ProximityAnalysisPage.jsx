import React, { useState, useEffect } from "react";
import InteractiveMap from "../components/InteractiveMap";
import { 
  ShieldAlert, Droplets, Home, Trees, 
  ArrowUpDown, Filter, Image as ImageIcon,
  ChevronLeft, ChevronRight, Loader2, AlertCircle
} from "lucide-react";
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, 
  CartesianGrid, Legend 
} from "recharts";
import api from "../services/api";

export default function ProximityAnalysisPage({ selectedYear, setSelectedYear }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [activeBufferRadius, setActiveBufferRadius] = useState(500);
  const [componentFilter, setComponentFilter] = useState("all");
  const [sortField, setSortField] = useState("dist_water_m");
  const [sortAsc, setSortAsc] = useState(true);
  const [showGisMapModal, setShowGisMapModal] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 15;

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    api.getProximity(selectedYear)
      .then((res) => {
        if (isMounted) {
          setData(res);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          console.error("Proximity API error:", err);
          setError(err.message);
          setLoading(false);
        }
      });

    return () => { isMounted = false; };
  }, [selectedYear]);

  const summary = data?.summary || {};
  const rawComponents = data?.components || [];
  const bufferExposureRows = data?.buffer_exposure || [];

  // Filter components
  const filteredComponents = rawComponents.filter((comp) => {
    if (componentFilter === "immediate") return comp.dist_water_m <= 100;
    if (componentFilter === "medium") return comp.dist_water_m > 100 && comp.dist_water_m <= 300;
    if (componentFilter === "safe") return comp.dist_water_m > 300;
    return true;
  });

  // Sort components
  const sortedComponents = [...filteredComponents].sort((a, b) => {
    const valA = a[sortField] ?? 0;
    const valB = b[sortField] ?? 0;
    return sortAsc ? valA - valB : valB - valA;
  });

  // Pagination calculations
  const totalRecords = sortedComponents.length;
  const totalPages = Math.ceil(totalRecords / pageSize) || 1;
  const safePage = Math.min(currentPage, totalPages);
  const paginatedComponents = sortedComponents.slice((safePage - 1) * pageSize, safePage * pageSize);

  const handleSort = (field) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(true);
    }
  };

  const handleFilterChange = (val) => {
    setComponentFilter(val);
    setCurrentPage(1);
  };

  const handleYearChange = (yr) => {
    setSelectedYear(yr);
    setCurrentPage(1);
  };

  // Buffer Exposure Data for Selected Year
  const bufferChartData = bufferExposureRows.map((row) => ({
    radius: `${row.buffer_radius_m}m`,
    settlementPct: row.settlement_exposure_pct,
    forestPct: row.forest_exposure_pct,
    waterPct: row.water_exposure_pct
  }));

  const b500 = bufferExposureRows.find((b) => b.buffer_radius_m === 500) || {};

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Environmental Proximity &amp; Buffer Impact Analysis</h2>
          <p className="text-xs text-slate-500 mt-0.5 flex items-center gap-2">
            <span>Euclidean Boundary Setbacks &bull; 250m, 500m &amp; 1000m Radial Exposure Zones &bull; UTM 43N</span>
            {loading && <Loader2 className="w-3.5 h-3.5 animate-spin text-teal-600 inline" />}
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={() => setShowGisMapModal(true)}
            className="text-xs font-semibold px-3 py-1.5 rounded-lg border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 flex items-center gap-1.5 shadow-2xs transition-colors cursor-pointer"
          >
            <ImageIcon className="w-3.5 h-3.5 text-teal-600" /> View {selectedYear} GIS Plate
          </button>

          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500 font-medium">Year:</span>
            <select
              value={selectedYear}
              onChange={(e) => handleYearChange(Number(e.target.value))}
              className="text-xs bg-white border border-slate-200 rounded-md px-3 py-1.5 font-semibold text-slate-800 shadow-2xs cursor-pointer"
            >
              {[2021, 2022, 2023, 2024, 2025, 2026].map((yr) => (
                <option key={yr} value={yr}>{yr} Proximity</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg flex items-center gap-2 text-rose-700 text-xs">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>Failed to load Proximity API data: {error}</span>
        </div>
      )}

      {/* Proximity Summary Banner Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Distance to Water */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span className="font-semibold uppercase">Water Bodies</span>
            <Droplets className="w-4 h-4 text-sky-600" />
          </div>
          <div className="flex items-baseline gap-1 mt-1.5">
            <span className="text-2xl font-bold text-slate-900">{summary.dist_water_mean_m?.toFixed(0) ?? 0}</span>
            <span className="text-xs font-medium text-slate-500">m mean</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1">
            Median: {summary.dist_water_median_m?.toFixed(0) ?? 0} m | Min: {summary.dist_water_min_m?.toFixed(0) ?? 0} m
          </p>
        </div>

        {/* Distance to Settlement */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span className="font-semibold uppercase">Settlements</span>
            <Home className="w-4 h-4 text-amber-600" />
          </div>
          <div className="flex items-baseline gap-1 mt-1.5">
            <span className="text-2xl font-bold text-slate-900">{summary.dist_settlement_mean_m?.toFixed(1) ?? 0}</span>
            <span className="text-xs font-medium text-slate-500">m mean</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1">
            Median: {summary.dist_settlement_median_m?.toFixed(0) ?? 0} m | Min: {summary.dist_settlement_min_m?.toFixed(0) ?? 0} m
          </p>
        </div>

        {/* Distance to Forest */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span className="font-semibold uppercase">Forest / Greenery</span>
            <Trees className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="flex items-baseline gap-1 mt-1.5">
            <span className="text-2xl font-bold text-slate-900">{summary.dist_forest_mean_m?.toFixed(1) ?? 0}</span>
            <span className="text-xs font-medium text-slate-500">m mean</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1">
            Median: {summary.dist_forest_median_m?.toFixed(0) ?? 0} m | Min: {summary.dist_forest_min_m?.toFixed(0) ?? 0} m
          </p>
        </div>
      </div>

      {/* Main Map + Right Buffer Analysis Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <InteractiveMap
            height="520px"
            activeYear={selectedYear}
            showBufferControls={true}
            externalBufferRadius={activeBufferRadius}
            onBufferChange={setActiveBufferRadius}
            showAoiBoundary={true}
            bufferLayerData={data?.buffer_geojson}
          />
        </div>

        <div className="space-y-4">
          {/* Buffer Radius Selector */}
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
            <h3 className="text-xs font-semibold text-slate-800 uppercase tracking-wide mb-2 flex items-center gap-1.5">
              <ShieldAlert className="w-4 h-4 text-purple-600" /> Radial Buffer Exposure ({selectedYear})
            </h3>
            <p className="text-[11px] text-slate-500 mb-3">
              Percentage of regional class areas submerged inside the mine impact buffer
            </p>

            <div className="h-44 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={bufferChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                  <XAxis dataKey="radius" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 10 }} unit="%" />
                  <Tooltip formatter={(val) => [`${val.toFixed(1)}%`, "Exposed"]} />
                  <Bar dataKey="settlementPct" name="Settlement %" fill="#F39C12" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="forestPct" name="Forest %" fill="#27AE60" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="waterPct" name="Water %" fill="#2980B9" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="grid grid-cols-3 gap-1 mt-3 pt-3 border-t border-slate-100 text-center text-[10px] font-semibold text-slate-600">
              <div className="text-amber-700">Settlement</div>
              <div className="text-emerald-700">Forest</div>
              <div className="text-sky-700">Water</div>
            </div>
          </div>

          {/* Buffer Parameters Legend */}
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs text-xs space-y-2">
            <div className="flex justify-between pb-1 border-b border-slate-100">
              <span className="text-slate-500">Active Buffer:</span>
              <span className="font-semibold text-purple-700">{activeBufferRadius} m radius</span>
            </div>
            <div className="flex justify-between pb-1 border-b border-slate-100">
              <span className="text-slate-500">Mine Components:</span>
              <span className="font-semibold text-slate-900">{data?.component_count ?? 0} polygons</span>
            </div>
            <div className="flex justify-between pb-1 border-b border-slate-100">
              <span className="text-slate-500">Mine Footprint:</span>
              <span className="font-semibold text-slate-900">{summary.mine_bare_total_ha?.toFixed(2) ?? 0} ha</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Study Extent:</span>
              <span className="font-mono text-slate-900 text-[11px]">{summary.total_aoi_ha?.toFixed(2) ?? 7955.83} ha</span>
            </div>
          </div>
        </div>
      </div>

      {/* Component-Level Raw CSV Table from Backend */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
        <div className="p-4 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h3 className="text-sm font-bold text-slate-900">
              Contiguous Mining Components &bull; Epoch {selectedYear} ({totalRecords} records)
            </h3>
          </div>

          {/* Quick Category Filter */}
          <div className="flex items-center gap-2">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={componentFilter}
              onChange={(e) => handleFilterChange(e.target.value)}
              className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1 text-slate-700 font-medium"
            >
              <option value="all">All Setback Distances</option>
              <option value="immediate">&le; 100m to Water (High Risk)</option>
              <option value="medium">100m - 300m to Water (Moderate)</option>
              <option value="safe">&gt; 300m to Water (Low)</option>
            </select>
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50/80 text-slate-600 font-semibold border-b border-slate-100">
              <tr>
                <th className="py-2.5 px-4">Component ID</th>
                <th 
                  onClick={() => handleSort("area_ha")}
                  className="py-2.5 px-4 text-right cursor-pointer hover:bg-slate-100"
                >
                  Area (ha) <ArrowUpDown className="w-3 h-3 inline ml-0.5 text-slate-400" />
                </th>
                <th 
                  onClick={() => handleSort("dist_water_m")}
                  className="py-2.5 px-4 text-right cursor-pointer hover:bg-slate-100"
                >
                  Dist to Water (m) <ArrowUpDown className="w-3 h-3 inline ml-0.5 text-slate-400" />
                </th>
                <th 
                  onClick={() => handleSort("dist_settlement_m")}
                  className="py-2.5 px-4 text-right cursor-pointer hover:bg-slate-100"
                >
                  Dist to Settlement (m) <ArrowUpDown className="w-3 h-3 inline ml-0.5 text-slate-400" />
                </th>
                <th 
                  onClick={() => handleSort("dist_forest_m")}
                  className="py-2.5 px-4 text-right cursor-pointer hover:bg-slate-100"
                >
                  Dist to Forest (m) <ArrowUpDown className="w-3 h-3 inline ml-0.5 text-slate-400" />
                </th>
                <th className="py-2.5 px-4 text-center">Category</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono text-[11px] text-slate-700">
              {paginatedComponents.map((row) => (
                <tr key={row.component_id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-2 px-4 font-semibold text-slate-900 font-sans">{row.component_id}</td>
                  <td className="py-2 px-4 text-right">{Number(row.area_ha).toFixed(2)}</td>
                  <td className="py-2 px-4 text-right">
                    <span className={row.dist_water_m <= 100 ? "text-rose-600 font-bold" : "text-slate-800"}>
                      {Number(row.dist_water_m).toFixed(1)}
                    </span>
                  </td>
                  <td className="py-2 px-4 text-right">
                    <span className={row.dist_settlement_m === 0 ? "text-amber-600 font-bold" : "text-slate-800"}>
                      {Number(row.dist_settlement_m).toFixed(1)}
                    </span>
                  </td>
                  <td className="py-2 px-4 text-right">{Number(row.dist_forest_m).toFixed(1)}</td>
                  <td className="py-2 px-4 text-center font-sans">
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                      {row.category}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="p-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
          <div>
            Showing {(safePage - 1) * pageSize + 1} to {Math.min(safePage * pageSize, totalRecords)} of {totalRecords} entries
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setCurrentPage((p) => Math.max(p - 1, 1))}
              disabled={safePage === 1}
              className="p-1 rounded hover:bg-slate-100 disabled:opacity-40 cursor-pointer"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="px-2 font-medium">Page {safePage} of {totalPages}</span>
            <button
              onClick={() => setCurrentPage((p) => Math.min(p + 1, totalPages))}
              disabled={safePage === totalPages}
              className="p-1 rounded hover:bg-slate-100 disabled:opacity-40 cursor-pointer"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* GIS Plate Modal */}
      {showGisMapModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col shadow-2xl">
            <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
              <div>
                <h3 className="font-bold text-slate-900 text-sm">
                  Cartographic GIS Plate — Year {selectedYear}
                </h3>
                <p className="text-[11px] text-slate-500">
                  Publication-ready environmental proximity plate generated from clean polygons (EPSG:32643)
                </p>
              </div>
              <button
                onClick={() => setShowGisMapModal(false)}
                className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-slate-200 hover:bg-slate-300 text-slate-800 transition-colors cursor-pointer"
              >
                Close Plate
              </button>
            </div>
            <div className="p-4 overflow-y-auto flex items-center justify-center bg-slate-100">
              <img
                src={`/maps/clean_gis_map_${selectedYear}.png`}
                alt={`Clean GIS Plate ${selectedYear}`}
                className="max-h-[70vh] object-contain rounded-lg border border-slate-300 shadow-md"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
