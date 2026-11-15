import React from "react";
import InteractiveMap from "../components/InteractiveMap";
import { AlertTriangle, Layers } from "lucide-react";
import { UNET_TARGET_STATS } from "../data/placeholderData";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";

export default function UnetPage({ selectedYear, setSelectedYear }) {
  // Driven directly from outputs/reports/unet_expansion.json (via UNET_TARGET_STATS)
  const currentTarget = UNET_TARGET_STATS.find((d) => d.year === selectedYear) || UNET_TARGET_STATS[UNET_TARGET_STATS.length - 1];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">U-Net Deep Learning Mining Detection</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            ResNet-34 10-Band Segmentation Architecture &bull; Multi-Temporal Boundary Extraction
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
              <option key={yr} value={yr}>U-Net {yr}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Mandatory Scientific Transparency Banner */}
      <div className="bg-amber-50 border border-amber-200/90 rounded-xl p-4 flex items-start gap-3 shadow-xs">
        <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
        <div className="text-xs text-amber-900 space-y-1">
          <p className="font-bold">
            Methodological Notice: Area-Calibrated Prototype Masks
          </p>
          <p className="text-amber-800 leading-normal">
            The U-Net prediction GeoTIFFs (<code className="font-mono text-[11px] bg-amber-100/60 px-1 rounded">outputs/maps/unet_pred_YYYY.tif</code>) currently represent{" "}
            <strong>area-calibrated prototype masks</strong> calibrated against historical mining targets (<code className="font-mono text-[11px] bg-amber-100/60 px-1 rounded">outputs/reports/unet_expansion.json</code>).
            These represent calibrated prototype masks, not genuine field inference outputs. The ResNet-34 deep learning architecture is fully implemented, with weights pretrained on the LAMES benchmark.
          </p>
        </div>
      </div>

      {/* Top Metric Cards (Driven by outputs/reports/unet_expansion.json) */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
          <p className="text-xs font-semibold text-slate-500 uppercase">Calibrated Mine Footprint</p>
          <div className="flex items-baseline gap-1 mt-1.5">
            <span className="text-2xl font-bold text-slate-900">{currentTarget.areaHa.toFixed(2)}</span>
            <span className="text-xs font-medium text-slate-500">ha</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Calibrated target for epoch {selectedYear}</p>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
          <p className="text-xs font-semibold text-slate-500 uppercase">Annual Expansion / Contraction</p>
          <div className="flex items-baseline gap-1 mt-1.5">
            <span className={`text-2xl font-bold ${currentTarget.expansionHa >= 0 ? "text-teal-700" : "text-amber-600"}`}>
              {currentTarget.expansionHa > 0 ? `+${currentTarget.expansionHa.toFixed(2)}` : currentTarget.expansionHa.toFixed(2)}
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

      {/* Interactive Map + Expansion Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Interactive Leaflet Map for U-Net */}
        <div className="lg:col-span-7 space-y-3">
          <h3 className="text-xs font-semibold text-slate-800 uppercase tracking-wide flex items-center gap-1.5">
            <Layers className="w-4 h-4 text-teal-600" /> Spatial Boundary Extraction Viewer
          </h3>
          <InteractiveMap 
            height="500px" 
            activeYear={selectedYear} 
            showUnetOverlay={true} 
            showAoiBoundary={true} 
          />
        </div>

        {/* Right Demonstration Column */}
        <div className="lg:col-span-5 space-y-4">
          {/* Historical Expansion Curve */}
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
            <h3 className="text-xs font-semibold text-slate-800 uppercase tracking-wide mb-1">
              Calibrated Expansion Trend (2021–2026)
            </h3>
            <p className="text-[11px] text-slate-500 mb-2">
              Historical progression from single source: <code className="font-mono text-[10px]">outputs/reports/unet_expansion.json</code>
            </p>
            <div className="h-52 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={UNET_TARGET_STATS} margin={{ top: 10, right: 15, left: -10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                  <XAxis dataKey="year" tick={{ fontSize: 11 }} />
                  <YAxis domain={[90, 135]} tick={{ fontSize: 11 }} unit=" ha" />
                  <Tooltip formatter={(val) => [`${val} ha`, "Calibrated Area"]} />
                  <Line 
                    type="monotone" 
                    dataKey="areaHa" 
                    name="Calibrated Footprint" 
                    stroke="#E11D48" 
                    strokeWidth={2.5} 
                    dot={{ r: 4, fill: "#E11D48" }} 
                    activeDot={{ r: 6 }} 
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-2 text-[10px] text-slate-400 text-center font-mono">
              2021: 99.32 ha &rarr; 2025: 124.73 ha &rarr; 2026: 114.60 ha (-10.13 ha)
            </div>
          </div>

          {/* Architecture Overview */}
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
            <h4 className="text-xs font-bold text-slate-900 mb-2">ResNet-34 Feature Surgery</h4>
            <div className="space-y-1.5 text-xs text-slate-600">
              <p>
                First convolutional layer (<code className="font-mono text-[11px]">conv1</code>) expanded from 3 to 10 channels:
              </p>
              <ul className="list-disc list-inside space-y-0.5 text-slate-500 text-[11px] pl-1">
                <li>RGB channels (B4, B3, B2) initialized from pretrained ImageNet weights</li>
                <li>Additional 7 bands initialized using channel-averaged weights</li>
                <li>Output activation: Single sigmoid channel for binary mine delineation</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}