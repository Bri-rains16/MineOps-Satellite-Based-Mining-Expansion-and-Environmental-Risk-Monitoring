import React, { useState } from "react";
import InteractiveMap from "../components/InteractiveMap";
import { 
  ShieldAlert, Droplets, Home, Trees, 
  ArrowUpDown, Filter, Image as ImageIcon,
  ChevronLeft, ChevronRight
} from "lucide-react";
import { 
  BUFFER_EXPOSURE_STATS, 
  GENUINE_RF_METRICS 
} from "../data/placeholderData";
import componentsData from "../data/components_data.json";
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, 
  CartesianGrid, Legend 
} from "recharts";

export default function ProximityAnalysisPage({ selectedYear, setSelectedYear }) {
  const [activeBufferRadius, setActiveBufferRadius] = useState(500);
  const [componentFilter, setComponentFilter] = useState("all");
  const [sortField, setSortField] = useState("dist_water_m");
  const [sortAsc, setSortAsc] = useState(true);
  const [showGisMapModal, setShowGisMapModal] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 15;

  // Find genuine statistics for selected year
  const currentProximity = GENUINE_RF_METRICS.find((d) => d.year === selectedYear) || GENUINE_RF_METRICS[5];
  const currentBufferStats = BUFFER_EXPOSURE_STATS.find((d) => d.year === selectedYear) || BUFFER_EXPOSURE_STATS[5];

  // Component rows for the selected year (all records from CSV)
  const rawComponents = componentsData[selectedYear] || [];

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

  // Prepare Buffer Exposure Chart Data for all 6 years
  const bufferTrendData = BUFFER_EXPOSURE_STATS.map((b) => ({
    year: b.year.toString(),
    b250_settlement: b.b250.settlementPct,
    b500_settlement: b.b500.settlementPct,
    b1000_settlement: b.b1000.settlementPct,
    b250_water: b.b250.waterPct,
    b500_water: b.b500.waterPct,
    b1000_water: b.b1000.waterPct,
    b250_forest: b.b250.forestPct,
    b500_forest: b.b500.forestPct,
    b1000_forest: b.b1000.forestPct,
  }));

  const activeBufferKey = `b${activeBufferRadius}`;
  const currentSelectedBuffer = currentBufferStats[activeBufferKey] || currentBufferStats.b500;

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Environmental Proximity &amp; Buffer Exposure</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Boundary-to-boundary distance calculations and 250m / 500m / 1000m radial buffer exposure
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500">Epoch:</span>
            <select
              value={selectedYear}
              onChange={(e) => handleYearChange(Number(e.target.value))}
              className="text-xs bg-white border border-slate-200 rounded-md px-3 py-1.5 font-medium text-slate-800 shadow-2xs cursor-pointer"
            >
              {[2021, 2022, 2023, 2024, 2025, 2026].map((yr) => (
                <option key={yr} value={yr}>{yr}</option>
              ))}
            </select>
          </div>
          <button
            onClick={() => setShowGisMapModal(true)}
            className="flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-md bg-teal-50 border border-teal-200 text-teal-700 hover:bg-teal-100 transition-colors cursor-pointer"
          >
            <ImageIcon className="w-3.5 h-3.5" /> View GIS Plate ({selectedYear})
          </button>
        </div>
      </div>

      {/* Spatial Proximity Distance Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Water */}
        <div className="bg-white border-l-4 border-l-[#2980B9] border border-slate-200 rounded-xl p-4 shadow-xs">
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold text-slate-500 uppercase">Spatial Proximity to Water</p>
            <Droplets className="w-4 h-4 text-sky-600" />
          </div>
          <div className="flex items-baseline gap-1 mt-1.5">
            <span className="text-2xl font-bold text-slate-900">{currentProximity.waterDistMedian.toFixed(1)}</span>
            <span className="text-xs font-medium text-slate-500">m median</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1">
            Mean separation: <strong className="text-slate-700">{currentProximity.waterDistMean.toFixed(1)} m</strong> across {rawComponents.length} pit components
          </p>
        </div>

        {/* Forest */}
        <div className="bg-white border-l-4 border-l-[#27AE60] border border-slate-200 rounded-xl p-4 shadow-xs">
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold text-slate-500 uppercase">Spatial Proximity to Forest</p>
            <Trees className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="flex items-baseline gap-1 mt-1.5">
            <span className="text-2xl font-bold text-slate-900">{currentProximity.forestDistMedian.toFixed(1)}</span>
            <span className="text-xs font-medium text-slate-500">m median</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1">
            Mean separation: <strong className="text-slate-700">{currentProximity.forestDistMean.toFixed(1)} m</strong> (perimeter boundary contact)
          </p>
        </div>

        {/* Settlement */}
        <div className="bg-white border-l-4 border-l-[#F39C12] border border-slate-200 rounded-xl p-4 shadow-xs">
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold text-slate-500 uppercase">Spatial Proximity to Settlement</p>
            <Home className="w-4 h-4 text-amber-600" />
          </div>
          <div className="flex items-baseline gap-1 mt-1.5">
            <span className="text-2xl font-bold text-slate-900">{currentProximity.settlementDistMedian.toFixed(1)}</span>
            <span className="text-xs font-medium text-slate-500">m median</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1">
            Mean separation: <strong className="text-slate-700">{currentProximity.settlementDistMean.toFixed(1)} m</strong> adjacent to built settlements
          </p>
        </div>
      </div>

      {/* Main Spatial Map with Buffer Overlay Controls */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-8">
          <InteractiveMap 
            height="520px" 
            activeYear={selectedYear} 
            showBufferControls={true} 
            showAoiBoundary={true}
            externalBufferRadius={activeBufferRadius}
            onBufferChange={setActiveBufferRadius}
          />
        </div>

        {/* Right Buffer Exposure Details */}
        <div className="lg:col-span-4 space-y-4">
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
            <h3 className="text-xs font-semibold text-slate-900 uppercase tracking-wide mb-3 flex items-center gap-1.5">
              <ShieldAlert className="w-4 h-4 text-teal-600" /> Radial Buffer Exposure ({selectedYear})
            </h3>

            {/* Buffer Selector Tabs */}
            <div className="flex gap-1.5 p-1 bg-slate-100 rounded-lg mb-4">
              {[250, 500, 1000].map((radius) => (
                <button
                  key={radius}
                  onClick={() => setActiveBufferRadius(radius)}
                  className={`flex-1 py-1.5 text-xs font-semibold rounded-md transition-colors cursor-pointer ${
                    activeBufferRadius === radius
                      ? "bg-white text-slate-900 shadow-xs"
                      : "text-slate-500 hover:text-slate-800"
                  }`}
                >
                  {radius}m Buffer
                </button>
              ))}
            </div>

            {/* Exposure Metrics for Selected Buffer */}
            <div className="space-y-3">
              <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
                <div className="flex justify-between items-center text-xs mb-1">
                  <span className="font-medium text-slate-700">Settlement in Buffer:</span>
                  <span className="font-bold text-amber-600">
                    {currentSelectedBuffer.settlementPct}%
                  </span>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-1.5">
                  <div
                    className="bg-amber-500 h-1.5 rounded-full"
                    style={{
                      width: `${currentSelectedBuffer.settlementPct}%`
                    }}
                  ></div>
                </div>
                <p className="text-[10px] text-slate-400 mt-1">Area exposed: {currentSelectedBuffer.settlementHa} ha</p>
              </div>

              <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
                <div className="flex justify-between items-center text-xs mb-1">
                  <span className="font-medium text-slate-700">Water in Buffer:</span>
                  <span className="font-bold text-sky-600">
                    {currentSelectedBuffer.waterPct}%
                  </span>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-1.5">
                  <div
                    className="bg-sky-500 h-1.5 rounded-full"
                    style={{
                      width: `${currentSelectedBuffer.waterPct}%`
                    }}
                  ></div>
                </div>
                <p className="text-[10px] text-slate-400 mt-1">Area exposed: {currentSelectedBuffer.waterHa} ha</p>
              </div>

              <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
                <div className="flex justify-between items-center text-xs mb-1">
                  <span className="font-medium text-slate-700">Forest in Buffer:</span>
                  <span className="font-bold text-emerald-600">
                    {currentSelectedBuffer.forestPct}%
                  </span>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-1.5">
                  <div
                    className="bg-emerald-500 h-1.5 rounded-full"
                    style={{
                      width: `${currentSelectedBuffer.forestPct}%`
                    }}
                  ></div>
                </div>
                <p className="text-[10px] text-slate-400 mt-1">Area exposed: {currentSelectedBuffer.forestHa} ha</p>
              </div>
            </div>

            <div className="mt-4 p-2.5 rounded-lg bg-teal-50/60 border border-teal-100 text-[11px] text-teal-800">
              <p className="font-medium">Methodology &amp; Terminology:</p>
              <p className="text-[10px] text-teal-700 mt-0.5 leading-normal">
                Values reflect <strong>spatial buffer exposure</strong> calculated using metric Euclidean buffers in <strong>EPSG:32643</strong> around active mine components. Buffer intersection indicates geographic proximity, not direct physical impact.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Buffer Exposure Chart */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 mb-4 border-b border-slate-100 gap-2">
          <div>
            <h3 className="text-sm font-bold text-slate-900">Multi-Temporal Buffer Exposure Trends (2021–2026)</h3>
            <p className="text-xs text-slate-500">Environmental land-cover exposure across 250m, 500m, and 1000m buffer zones</p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400">Target buffer:</span>
            <div className="inline-flex rounded-md shadow-2xs">
              {[250, 500, 1000].map((r) => (
                <button
                  key={r}
                  onClick={() => setActiveBufferRadius(r)}
                  className={`px-2.5 py-1 text-xs font-medium border first:rounded-l-md last:rounded-r-md cursor-pointer ${
                    activeBufferRadius === r
                      ? "bg-teal-600 text-white border-teal-600"
                      : "bg-white text-slate-700 border-slate-200 hover:bg-slate-50"
                  }`}
                >
                  {r}m
                </button>
              ))}
            </div>
          </div>
        </div>
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={bufferTrendData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
              <XAxis dataKey="year" tick={{ fontSize: 11, fill: "#64748B" }} tickLine={false} />
              <YAxis unit="%" tick={{ fontSize: 11, fill: "#64748B" }} tickLine={false} domain={[0, 100]} />
              <Tooltip 
                contentStyle={{ borderRadius: '8px', fontSize: '11px', border: '1px solid #E2E8F0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                formatter={(val) => [`${val}%`, '']}
              />
              <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
              <Bar 
                dataKey={`b${activeBufferRadius}_settlement`} 
                name={`Settlement Exposure (${activeBufferRadius}m)`} 
                fill="#F39C12" 
                radius={[4, 4, 0, 0]} 
              />
              <Bar 
                dataKey={`b${activeBufferRadius}_water`} 
                name={`Water Body Exposure (${activeBufferRadius}m)`} 
                fill="#2980B9" 
                radius={[4, 4, 0, 0]} 
              />
              <Bar 
                dataKey={`b${activeBufferRadius}_forest`} 
                name={`Forest Canopy Exposure (${activeBufferRadius}m)`} 
                fill="#27AE60" 
                radius={[4, 4, 0, 0]} 
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Component-Level Proximity Table */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
        <div className="p-4 border-b border-slate-100 flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div>
            <h3 className="text-sm font-bold text-slate-900">
              Component-Level Spatial Proximity Table ({selectedYear})
            </h3>
            <p className="text-xs text-slate-500">
              Contiguous mine pit components extracted from clean vector outputs &bull; Showing {paginatedComponents.length} of {totalRecords} records (Total in year: {rawComponents.length})
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={componentFilter}
              onChange={(e) => handleFilterChange(e.target.value)}
              className="text-xs bg-slate-50 border border-slate-200 rounded-md px-2.5 py-1 text-slate-700 font-medium"
            >
              <option value="all">All Pit Components ({rawComponents.length})</option>
              <option value="immediate">High Proximity: Water &le; 100m</option>
              <option value="medium">Medium Proximity: Water 101–300m</option>
              <option value="safe">Low Proximity: Water &gt; 300m</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50/80 text-slate-600 border-b border-slate-100 font-semibold">
              <tr>
                <th className="py-2.5 px-4 cursor-pointer select-none" onClick={() => handleSort("component_id")}>
                  <div className="flex items-center gap-1">
                    Component ID <ArrowUpDown className="w-3 h-3 text-slate-400" />
                  </div>
                </th>
                <th className="py-2.5 px-4 cursor-pointer select-none" onClick={() => handleSort("area_ha")}>
                  <div className="flex items-center gap-1">
                    Pit Area (ha) <ArrowUpDown className="w-3 h-3 text-slate-400" />
                  </div>
                </th>
                <th className="py-2.5 px-4 cursor-pointer select-none" onClick={() => handleSort("dist_water_m")}>
                  <div className="flex items-center gap-1">
                    Dist to Water (m) <ArrowUpDown className="w-3 h-3 text-slate-400" />
                  </div>
                </th>
                <th className="py-2.5 px-4 cursor-pointer select-none" onClick={() => handleSort("dist_forest_m")}>
                  <div className="flex items-center gap-1">
                    Dist to Forest (m) <ArrowUpDown className="w-3 h-3 text-slate-400" />
                  </div>
                </th>
                <th className="py-2.5 px-4 cursor-pointer select-none" onClick={() => handleSort("dist_settlement_m")}>
                  <div className="flex items-center gap-1">
                    Dist to Settlement (m) <ArrowUpDown className="w-3 h-3 text-slate-400" />
                  </div>
                </th>
                <th className="py-2.5 px-4 text-center">Proximity Category</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono text-[11px] text-slate-700">
              {paginatedComponents.map((comp) => {
                const isWaterClose = comp.dist_water_m <= 100;
                return (
                  <tr key={comp.component_id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-2 px-4 font-semibold text-slate-900 font-sans">
                      {comp.component_id}
                    </td>
                    <td className="py-2 px-4">
                      {comp.area_ha.toFixed(2)}
                    </td>
                    <td className={`py-2 px-4 font-semibold ${isWaterClose ? "text-rose-600 bg-rose-50/50" : "text-sky-700"}`}>
                      {comp.dist_water_m.toFixed(1)} m
                    </td>
                    <td className="py-2 px-4 text-emerald-700">
                      {comp.dist_forest_m.toFixed(1)} m
                    </td>
                    <td className="py-2 px-4 text-amber-700">
                      {comp.dist_settlement_m.toFixed(1)} m
                    </td>
                    <td className="py-2 px-4 text-center font-sans">
                      {isWaterClose ? (
                        <span className="inline-block px-2 py-0.5 rounded text-[10px] font-semibold bg-rose-100 text-rose-700">
                          Immediate Adjacency
                        </span>
                      ) : comp.dist_water_m <= 300 ? (
                        <span className="inline-block px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-100 text-amber-700">
                          Moderate Setback
                        </span>
                      ) : (
                        <span className="inline-block px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-100 text-emerald-700">
                          Low Proximity
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
              {paginatedComponents.length === 0 && (
                <tr>
                  <td colSpan={6} className="py-6 text-center text-slate-400 font-sans text-xs">
                    No components match the selected proximity filter.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="p-3 bg-slate-50 border-t border-slate-100 flex items-center justify-between text-xs text-slate-600">
          <div>
            Showing <span className="font-semibold">{Math.min((safePage - 1) * pageSize + 1, totalRecords)}</span> to{" "}
            <span className="font-semibold">{Math.min(safePage * pageSize, totalRecords)}</span> of{" "}
            <span className="font-semibold">{totalRecords}</span> filtered items
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={safePage === 1}
              className="p-1.5 rounded border border-slate-200 bg-white disabled:opacity-40 hover:bg-slate-100 transition-colors cursor-pointer disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
            </button>
            <span className="px-2 text-slate-500">
              Page {safePage} of {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={safePage === totalPages}
              className="p-1.5 rounded border border-slate-200 bg-white disabled:opacity-40 hover:bg-slate-100 transition-colors cursor-pointer disabled:cursor-not-allowed"
            >
              <ChevronRight className="w-3.5 h-3.5" />
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