import React, { useState, useEffect } from "react";
import InteractiveMap from "../components/InteractiveMap";
import { CheckCircle2, Layers, Loader2, AlertCircle } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import api from "../services/api";

export default function UnetPage({ selectedYear, setSelectedYear }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    api.getUnet(selectedYear)
      .then((res) => {
        if (isMounted) {
          setData(res);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          console.error("U-Net API error:", err);
          setError(err.message);
          setLoading(false);
        }
      });

    return () => { isMounted = false; };
  }, [selectedYear]);

  const currentExpansion = data?.expansion_data || { area_hectares: 114.6, expansion_ha: -10.13 };
  const allYears = data?.all_years_expansion || [];
  const maskMeta = data?.mask_metadata;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">U-Net Deep Learning Mining Detection</h2>
          <p className="text-xs text-slate-500 mt-0.5 flex items-center gap-2">
            <span>ResNet-34 10-Band Segmentation Architecture &bull; Multi-Temporal Boundary Extraction</span>
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
              <option key={yr} value={yr}>U-Net {yr}</option>
            ))}
          </select>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg flex items-center gap-2 text-rose-700 text-xs">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>Failed to load U-Net API data: {error}</span>
        </div>
      )}

      {/* Top Metric Cards (Driven by backend GET /api/unet/:year) */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
          <p className="text-xs font-semibold text-slate-500 uppercase">Predicted Mine Footprint</p>
          <div className="flex items-baseline gap-1 mt-1.5">
            <span className="text-2xl font-bold text-slate-900">{currentExpansion.area_hectares?.toFixed(2) ?? "0.00"}</span>
            <span className="text-xs font-medium text-slate-500">ha</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Calibrated target for epoch {selectedYear}</p>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
          <p className="text-xs font-semibold text-slate-500 uppercase">Annual Expansion / Contraction</p>
          <div className="flex items-baseline gap-1 mt-1.5">
            <span className={`text-2xl font-bold ${currentExpansion.expansion_ha >= 0 ? "text-teal-700" : "text-amber-600"}`}>
              {currentExpansion.expansion_ha > 0 ? `+${currentExpansion.expansion_ha.toFixed(2)}` : currentExpansion.expansion_ha?.toFixed(2)}
            </span>
            <span className="text-xs font-medium text-slate-500">ha/year</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Net shift compared to previous year</p>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
          <p className="text-xs font-semibold text-slate-500 uppercase">Model Input Channels</p>
          <div className="flex items-baseline gap-1 mt-1.5">
            <span className="text-2xl font-bold text-slate-900">10</span>
            <span className="text-xs font-medium text-slate-500">bands</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1">B2, B3, B4, B5, B6, B7, B8, B8A, B11, B12 (Sentinel-2)</p>
        </div>
      </div>

      {/* Main Map + Right Side U-Net Trend */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <InteractiveMap
            height="520px"
            activeYear={selectedYear}
            showUnetOverlay={true}
            showAoiBoundary={true}
            geojsonData={data?.geojson}
          />
        </div>

        <div className="space-y-4">
          
          {/* 6-Year Trend Chart Driven by all_years_expansion */}
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
            <h3 className="text-xs font-semibold text-slate-800 uppercase tracking-wide mb-1">
              Multi-Temporal Expansion Trend
            </h3>
            <p className="text-[11px] text-slate-500 mb-3">
              Source: <code className="font-mono text-[10px]">outputs/reports/unet_expansion.json</code>
            </p>
            <div className="h-44 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={allYears} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                  <XAxis dataKey="year" tick={{ fontSize: 10 }} />
                  <YAxis domain={['auto', 'auto']} tick={{ fontSize: 10 }} />
                  <Tooltip formatter={(value) => [`${value} ha`, 'Mine Area']} />
                  <Line 
                    type="monotone" 
                    dataKey="area_hectares" 
                    stroke="#D97706" 
                    strokeWidth={2.5} 
                    dot={{ r: 4, fill: "#D97706" }} 
                    activeDot={{ r: 6 }} 
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
