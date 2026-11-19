import React, { useState, useEffect } from "react";
import InteractiveMap from "../components/InteractiveMap";
import { Filter, Layers, CheckCircle, AlertCircle, Loader2 } from "lucide-react";
import { SATELLITE_SPECIFICATIONS } from "../data/placeholderData";
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, 
  CartesianGrid, Legend 
} from "recharts";
import api from "../services/api";

export default function RandomForestPage({ selectedYear, setSelectedYear }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [activeLayers, setActiveLayers] = useState({
    mine: true,
    settlement: true,
    forest: true,
    water: true
  });

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    api.getRf(selectedYear)
      .then((res) => {
        if (isMounted) {
          setData(res);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          console.error("RF API error:", err);
          setError(err.message);
          setLoading(false);
        }
      });

    return () => { isMounted = false; };
  }, [selectedYear]);

  const toggleLayer = (layerName) => {
    setActiveLayers((prev) => ({ ...prev, [layerName]: !prev[layerName] }));
  };

  const totalAreaHa = data?.total_area_ha || 7955.83;
  const classAreas = data?.class_areas || [];

  const mineObj = classAreas.find((c) => c.class_id === 0) || { area_ha: 0 };
  const settlementObj = classAreas.find((c) => c.class_id === 1) || { area_ha: 0 };
  const forestObj = classAreas.find((c) => c.class_id === 2) || { area_ha: 0 };
  const waterObj = classAreas.find((c) => c.class_id === 3) || { area_ha: 0 };

  const barChartData = [
    { name: "Mine/Bare", area_ha: mineObj.area_ha, fill: "#E74C3C" },
    { name: "Settlement", area_ha: settlementObj.area_ha, fill: "#F39C12" },
    { name: "Forest", area_ha: forestObj.area_ha, fill: "#27AE60" },
    { name: "Water", area_ha: waterObj.area_ha, fill: "#2980B9" }
  ];

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Random Forest Land-Cover Classification</h2>
          <p className="text-xs text-slate-500 mt-0.5 flex items-center gap-2">
            <span>Ojha et al. (2025) Stacked Mineral Ratios &bull; Mutually Exclusive Classes &bull; Zero Inter-Class Overlaps</span>
            {loading && <Loader2 className="w-3.5 h-3.5 animate-spin text-teal-600 inline" />}
          </p>
        </div>

        {/* Year Selector */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500 font-medium">Year:</span>
          <select
            value={selectedYear}
            onChange={(e) => setSelectedYear(Number(e.target.value))}
            className="text-xs bg-white border border-slate-200 rounded-md px-3 py-1.5 font-semibold text-slate-800 shadow-2xs cursor-pointer"
          >
            {[2021, 2022, 2023, 2024, 2025, 2026].map((yr) => (
              <option key={yr} value={yr}>Sentinel-2 {yr}</option>
            ))}
          </select>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg flex items-center gap-2 text-rose-700 text-xs">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>Failed to load RF API data: {error}</span>
        </div>
      )}

      {/* Layer Toggles & Class Statistics Banner */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Mine/Bare */}
        <div 
          onClick={() => toggleLayer("mine")}
          className={`border rounded-xl p-4 shadow-xs cursor-pointer transition-all ${
            activeLayers.mine ? "bg-white border-l-4 border-l-[#E74C3C] border-slate-200" : "bg-slate-50 border-slate-200 opacity-60"
          }`}
        >
          <div className="flex items-center justify-between text-xs">
            <span className="font-semibold text-slate-500 uppercase">Class 0: Mine / Bare</span>
            <input type="checkbox" checked={activeLayers.mine} readOnly className="w-3.5 h-3.5 rounded text-rose-600" />
          </div>
          <div className="flex items-baseline gap-1 mt-1.5">
            <span className="text-2xl font-bold text-slate-900">{mineObj.area_ha.toFixed(2)}</span>
            <span className="text-xs font-medium text-slate-500">ha</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1">{((mineObj.area_ha / totalAreaHa) * 100).toFixed(1)}% AOI share</p>
        </div>

        {/* Settlement */}
        <div 
          onClick={() => toggleLayer("settlement")}
          className={`border rounded-xl p-4 shadow-xs cursor-pointer transition-all ${
            activeLayers.settlement ? "bg-white border-l-4 border-l-[#F39C12] border-slate-200" : "bg-slate-50 border-slate-200 opacity-60"
          }`}
        >
          <div className="flex items-center justify-between text-xs">
            <span className="font-semibold text-slate-500 uppercase">Class 1: Settlement</span>
            <input type="checkbox" checked={activeLayers.settlement} readOnly className="w-3.5 h-3.5 rounded text-amber-600" />
          </div>
          <div className="flex items-baseline gap-1 mt-1.5">
            <span className="text-2xl font-bold text-slate-900">{settlementObj.area_ha.toFixed(2)}</span>
            <span className="text-xs font-medium text-slate-500">ha</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1">{((settlementObj.area_ha / totalAreaHa) * 100).toFixed(1)}% AOI share</p>
        </div>

        {/* Forest */}
        <div 
          onClick={() => toggleLayer("forest")}
          className={`border rounded-xl p-4 shadow-xs cursor-pointer transition-all ${
            activeLayers.forest ? "bg-white border-l-4 border-l-[#27AE60] border-slate-200" : "bg-slate-50 border-slate-200 opacity-60"
          }`}
        >
          <div className="flex items-center justify-between text-xs">
            <span className="font-semibold text-slate-500 uppercase">Class 2: Forest</span>
            <input type="checkbox" checked={activeLayers.forest} readOnly className="w-3.5 h-3.5 rounded text-emerald-600" />
          </div>
          <div className="flex items-baseline gap-1 mt-1.5">
            <span className="text-2xl font-bold text-slate-900">{forestObj.area_ha.toFixed(2)}</span>
            <span className="text-xs font-medium text-slate-500">ha</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1">{((forestObj.area_ha / totalAreaHa) * 100).toFixed(1)}% AOI share</p>
        </div>

        {/* Water */}
        <div 
          onClick={() => toggleLayer("water")}
          className={`border rounded-xl p-4 shadow-xs cursor-pointer transition-all ${
            activeLayers.water ? "bg-white border-l-4 border-l-[#2980B9] border-slate-200" : "bg-slate-50 border-slate-200 opacity-60"
          }`}
        >
          <div className="flex items-center justify-between text-xs">
            <span className="font-semibold text-slate-500 uppercase">Class 3: Water</span>
            <input type="checkbox" checked={activeLayers.water} readOnly className="w-3.5 h-3.5 rounded text-sky-600" />
          </div>
          <div className="flex items-baseline gap-1 mt-1.5">
            <span className="text-2xl font-bold text-slate-900">{waterObj.area_ha.toFixed(2)}</span>
            <span className="text-xs font-medium text-slate-500">ha</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1">{((waterObj.area_ha / totalAreaHa) * 100).toFixed(1)}% AOI share</p>
        </div>
      </div>

      {/* Main Map + Right Side Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <InteractiveMap
            height="550px"
            activeYear={selectedYear}
            activeClassFilter={activeLayers}
            showAoiBoundary={true}
            geojsonData={data?.geojson}
          />
        </div>

        <div className="space-y-4">
          {/* Area Breakdown Chart */}
          <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
            <h3 className="text-xs font-semibold text-slate-800 uppercase tracking-wide mb-2">
              Class Breakdown (ha)
            </h3>
            <p className="text-[11px] text-slate-500 mb-3">Live values from backend API</p>
            <div className="h-44 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={barChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                  <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip formatter={(val) => [`${val.toFixed(1)} ha`, "Area"]} />
                  <Bar dataKey="area_ha" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
