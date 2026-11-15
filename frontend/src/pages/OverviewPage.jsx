import React from "react";
import KpiCard from "../components/KpiCard";
import InteractiveMap from "../components/InteractiveMap";
import { Pickaxe, Trees, Droplets, Home, Layers, Calendar } from "lucide-react";
import { 
  GENUINE_RF_METRICS, 
  BUFFER_EXPOSURE_STATS, 
  SATELLITE_SPECIFICATIONS 
} from "../data/placeholderData";
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, 
  CartesianGrid, Legend, AreaChart, Area 
} from "recharts";

export default function OverviewPage({ selectedYear, setSelectedYear }) {
  const currentStats = GENUINE_RF_METRICS.find((d) => d.year === selectedYear) || GENUINE_RF_METRICS[GENUINE_RF_METRICS.length - 1];
  const currentBuffer = BUFFER_EXPOSURE_STATS.find((d) => d.year === selectedYear) || BUFFER_EXPOSURE_STATS[BUFFER_EXPOSURE_STATS.length - 1];

  return (
    <div className="space-y-6">
      {/* Top Header & Year Selector */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Executive GIS Overview</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Zawar Mining Belt &bull; Integrated Random Forest Classification &amp; Environmental Proximity (2021–2026)
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center bg-white border border-slate-200 rounded-lg p-1 shadow-2xs">
            <span className="text-xs text-slate-500 px-2.5 font-medium flex items-center gap-1">
              <Calendar className="w-3.5 h-3.5 text-slate-400" /> Epoch:
            </span>
            <div className="flex gap-1">
              {[2021, 2022, 2023, 2024, 2025, 2026].map((yr) => (
                <button
                  key={yr}
                  onClick={() => setSelectedYear(yr)}
                  className={`px-2.5 py-1 text-xs font-semibold rounded-md transition-colors cursor-pointer ${
                    selectedYear === yr
                      ? "bg-teal-600 text-white shadow-xs"
                      : "text-slate-600 hover:bg-slate-100"
                  }`}
                >
                  {yr}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* KPI Cards Row (Fully dynamic with selectedYear) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          title="Mine/Bare Footprint"
          value={currentStats.mineHa.toFixed(2)}
          unit="ha"
          subtitle={`${((currentStats.mineHa / currentStats.totalAreaHa) * 100).toFixed(1)}% of total study AOI`}
          trend={`${currentStats.componentCount} connected components`}
          trendType="neutral"
          icon={Pickaxe}
          badgeColor="bg-rose-50 text-rose-600"
        />
        <KpiCard
          title="Forest / Green Cover"
          value={currentStats.forestHa.toFixed(2)}
          unit="ha"
          subtitle={`${((currentStats.forestHa / currentStats.totalAreaHa) * 100).toFixed(1)}% landscape canopy`}
          trend={selectedYear === 2023 ? "5573.9 ha (peak clearance)" : "Dominant regional matrix"}
          trendType={selectedYear === 2023 ? "down" : "neutral"}
          icon={Trees}
          badgeColor="bg-emerald-50 text-emerald-600"
        />
        <KpiCard
          title="Distance to Water"
          value={currentStats.waterDistMedian.toFixed(1)}
          unit="m"
          subtitle="Median boundary setback"
          trend={`${currentStats.waterDistMean.toFixed(0)}m annual mean`}
          trendType="neutral"
          icon={Droplets}
          badgeColor="bg-sky-50 text-sky-600"
        />
        <KpiCard
          title="250m Buffer Exposure"
          value={currentBuffer.b250.settlementHa.toFixed(1)}
          unit="ha"
          subtitle={`${currentBuffer.b250.settlementPct.toFixed(1)}% settlement within 250m`}
          trend="Spatial buffer intersection"
          trendType="neutral"
          icon={Home}
          badgeColor="bg-amber-50 text-amber-600"
        />
      </div>

      {/* Main Map + Right Overview Cards Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Interactive Map Preview */}
        <div className="lg:col-span-2 space-y-4">
          <InteractiveMap 
            height="500px" 
            activeYear={selectedYear} 
            showBufferControls={true} 
            showAoiBoundary={true}
          />
        </div>

        {/* Right Summary Column */}
        <div className="space-y-4">
          {/* Quick Specifications */}
          <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
            <h3 className="text-xs font-semibold text-slate-800 uppercase tracking-wide mb-3 flex items-center gap-1.5">
              <Layers className="w-4 h-4 text-teal-600" /> Sensor &amp; Analysis Baseline
            </h3>
            <div className="space-y-2 text-xs text-slate-600">
              <div className="flex justify-between pb-1.5 border-b border-slate-100">
                <span className="text-slate-500">Sensor:</span>
                <span className="font-medium text-slate-900">{SATELLITE_SPECIFICATIONS.sensor}</span>
              </div>
              <div className="flex justify-between pb-1.5 border-b border-slate-100">
                <span className="text-slate-500">Spatial Grid:</span>
                <span className="font-medium text-slate-900">{SATELLITE_SPECIFICATIONS.resolution}</span>
              </div>
              <div className="flex justify-between pb-1.5 border-b border-slate-100">
                <span className="text-slate-500">Projected CRS:</span>
                <span className="font-mono text-slate-900 text-[11px]">{SATELLITE_SPECIFICATIONS.crsProjected}</span>
              </div>
              <div className="flex justify-between pb-1.5 border-b border-slate-100">
                <span className="text-slate-500">Classification Model:</span>
                <span className="font-medium text-slate-900">Random Forest (Ojha et al.)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Validation Accuracy:</span>
                <span className="font-semibold text-emerald-600">{SATELLITE_SPECIFICATIONS.rfValidationAccuracy}</span>
              </div>
            </div>
          </div>

          {/* Land Cover Proportion Chart */}
          <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
            <h3 className="text-xs font-semibold text-slate-800 uppercase tracking-wide mb-2">
              Land Cover Composition ({selectedYear})
            </h3>
            <p className="text-[11px] text-slate-500 mb-3">Area in hectares (Total AOI: 7,955.8 ha)</p>
            <div className="h-44 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={[currentStats]} layout="vertical" margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#E2E8F0" />
                  <XAxis type="number" tick={{ fontSize: 10 }} />
                  <YAxis type="category" dataKey="year" hide />
                  <Tooltip formatter={(value) => [`${value} ha`, 'Area']} />
                  <Bar dataKey="forestHa" name="Forest/Vegetation" fill="#27AE60" radius={[0, 4, 4, 0]} />
                  <Bar dataKey="settlementHa" name="Settlement" fill="#F39C12" radius={[0, 4, 4, 0]} />
                  <Bar dataKey="mineHa" name="Mine/Bare Land" fill="#E74C3C" radius={[0, 4, 4, 0]} />
                  <Bar dataKey="waterHa" name="Water Bodies" fill="#2980B9" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>

      {/* Multi-Year Temporal Area Dynamics */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-semibold text-slate-900">6-Year Multi-Temporal Surface Land-Cover Dynamics</h3>
            <p className="text-xs text-slate-500">2021–2026 Surface Area Tracking (Hectares) from Verified Multi-Class Vector Outputs</p>
          </div>
        </div>
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={GENUINE_RF_METRICS} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="colorMine" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#E74C3C" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#E74C3C" stopOpacity={0.0} />
                </linearGradient>
                <linearGradient id="colorForest" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#27AE60" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#27AE60" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
              <XAxis dataKey="year" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip formatter={(val) => [`${val} ha`]} />
              <Legend wrapperStyle={{ fontSize: "12px", paddingTop: "8px" }} />
              <Area type="monotone" dataKey="mineHa" name="Mine/Bare Area (ha)" stroke="#E74C3C" fillOpacity={1} fill="url(#colorMine)" strokeWidth={2} />
              <Area type="monotone" dataKey="forestHa" name="Forest/Vegetation (ha)" stroke="#27AE60" fillOpacity={1} fill="url(#colorForest)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}