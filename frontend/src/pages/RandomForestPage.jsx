import React, { useState } from "react";
import InteractiveMap from "../components/InteractiveMap";
import { Trees, Filter, Layers, CheckCircle, AlertCircle, Info } from "lucide-react";
import { GENUINE_RF_METRICS, SATELLITE_SPECIFICATIONS } from "../data/placeholderData";
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, 
  CartesianGrid, Legend, LineChart, Line 
} from "recharts";

export default function RandomForestPage({ selectedYear, setSelectedYear }) {
  const [selectedFeature, setSelectedFeature] = useState(null);
  const [activeLayers, setActiveLayers] = useState({
    mine: true,
    settlement: true,
    forest: true,
    water: true
  });

  const currentStats = GENUINE_RF_METRICS.find((d) => d.year === selectedYear) || GENUINE_RF_METRICS[0];

  const toggleLayer = (layerName) => {
    setActiveLayers((prev) => ({ ...prev, [layerName]: !prev[layerName] }));
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Random Forest Land-Cover Classification</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Ojha et al. (2025) Stacked Mineral Ratios &bull; Mutually Exclusive Classes &bull; Zero Inter-Class Overlaps
          </p>
        </div>

        {/* Year Selector */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500 font-medium">Epoch:</span>
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
            <span className="text-2xl font-bold text-slate-900">{currentStats.mineHa}</span>
            <span className="text-xs font-medium text-slate-500">ha</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1">{((currentStats.mineHa / currentStats.totalAreaHa) * 100).toFixed(1)}% AOI share</p>
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
            <span className="text-2xl font-bold text-slate-900">{currentStats.settlementHa}</span>
            <span className="text-xs font-medium text-slate-500">ha</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1">{((currentStats.settlementHa / currentStats.totalAreaHa) * 100).toFixed(1)}% AOI share</p>
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
            <span className="text-2xl font-bold text-slate-900">{currentStats.forestHa}</span>
            <span className="text-xs font-medium text-slate-500">ha</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1">{((currentStats.forestHa / currentStats.totalAreaHa) * 100).toFixed(1)}% AOI share</p>
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
            <span className="text-2xl font-bold text-slate-900">{currentStats.waterHa}</span>
            <span className="text-xs font-medium text-slate-500">ha</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1">{((currentStats.waterHa / currentStats.totalAreaHa) * 100).toFixed(2)}% AOI share</p>
        </div>
      </div>

      {/* Main Map with Clickable Polygon Inspection */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-8">
          <InteractiveMap
            height="540px"
            activeYear={selectedYear}
            activeClassFilter={activeLayers}
            onSelectFeature={(feat) => setSelectedFeature(feat)}
          />
        </div>

        {/* Right Inspection & Temporal Dynamics Panel */}
        <div className="lg:col-span-4 space-y-4">
          {/* Feature Inspector */}
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
            <h3 className="text-xs font-semibold text-slate-800 uppercase tracking-wide mb-2 flex items-center gap-1.5">
              <Info className="w-4 h-4 text-teal-600" /> Feature Inspector
            </h3>
            {selectedFeature ? (
              <div className="space-y-2 text-xs bg-slate-50 p-3 rounded-lg border border-slate-100">
                <div className="flex justify-between font-bold text-slate-900 border-b pb-1">
                  <span>ID:</span>
                  <span className="font-mono text-teal-700">{selectedFeature.id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Class:</span>
                  <span className="font-semibold text-slate-800">{selectedFeature.class_name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Area:</span>
                  <span className="font-bold text-slate-900">{selectedFeature.area_ha} ha</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Projection:</span>
                  <span className="font-mono text-[10px] text-slate-600">EPSG:32643 (UTM 43N)</span>
                </div>
              </div>
            ) : (
              <p className="text-xs text-slate-500 italic p-3 bg-slate-50 rounded-lg">
                Click any polygon on the map to inspect its component ID, exact area, and classification attributes.
              </p>
            )}
          </div>

          {/* Temporal Land-Cover Allocation Chart */}
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
            <h3 className="text-xs font-semibold text-slate-800 uppercase tracking-wide mb-1">
              Multi-Temporal Land-Cover Trends
            </h3>
            <p className="text-[11px] text-slate-500 mb-2">Area (ha) across all 6 epochs</p>
            <div className="h-44 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={GENUINE_RF_METRICS} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                  <XAxis dataKey="year" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip formatter={(val) => [`${val} ha`]} />
                  <Line type="monotone" dataKey="mineHa" name="Mine/Bare" stroke="#E74C3C" strokeWidth={2} dot={{ r: 3 }} />
                  <Line type="monotone" dataKey="settlementHa" name="Settlement" stroke="#F39C12" strokeWidth={2} dot={{ r: 3 }} />
                  <Line type="monotone" dataKey="waterHa" name="Water" stroke="#2980B9" strokeWidth={2} dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
