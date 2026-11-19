import React, { useState, useEffect } from "react";
import KpiCard from "../components/KpiCard";
import InteractiveMap from "../components/InteractiveMap";
import { Pickaxe, Trees, Droplets, Home, Layers, Calendar, Loader2, AlertCircle } from "lucide-react";
import { SATELLITE_SPECIFICATIONS } from "../data/placeholderData";
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, 
  CartesianGrid, Legend 
} from "recharts";
import api from "../services/api";

export default function OverviewPage({ selectedYear, setSelectedYear }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    api.getOverview(selectedYear)
      .then((res) => {
        if (isMounted) {
          setData(res);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          console.error("Overview API error:", err);
          setError(err.message);
          setLoading(false);
        }
      });

    return () => { isMounted = false; };
  }, [selectedYear]);

  // Derived metrics from backend API
  const totalAoiHa = data?.total_aoi_area_ha || 7955.83;
  const mineHa = data?.class_areas?.mine_ha ?? 0;
  const forestHa = data?.class_areas?.forest_ha ?? 0;
  const settlementHa = data?.class_areas?.settlement_ha ?? 0;
  const waterHa = data?.class_areas?.water_ha ?? 0;
  const componentCount = data?.component_count ?? 0;

  const waterDistMedian = data?.proximity_distances?.water?.median_m ?? 0;
  const waterDistMean = data?.proximity_distances?.water?.mean_m ?? 0;

  // 250m Buffer exposure for settlement
  const b250 = data?.buffer_exposure?.find((b) => b.buffer_radius_m === 250);
  const settlementExposedHa = b250?.settlement?.exposed_ha ?? 0;
  const settlementExposurePct = b250?.settlement?.exposure_pct ?? 0;

  const chartData = [
    {
      year: selectedYear,
      forestHa,
      settlementHa,
      mineHa,
      waterHa
    }
  ];

  return (
    <div className="space-y-6">
      {/* Top Header & Year Selector */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Executive GIS Overview</h2>
          <p className="text-xs text-slate-500 mt-0.5 flex items-center gap-2">
            <span>Zawar Mining Belt &bull; Integrated Random Forest Classification &amp; Environmental Proximity (2021–2026)</span>
            {loading && <Loader2 className="w-3.5 h-3.5 animate-spin text-teal-600 inline" />}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center bg-white border border-slate-200 rounded-lg p-1 shadow-2xs">
            <span className="text-xs text-slate-500 px-2.5 font-medium flex items-center gap-1">
              <Calendar className="w-3.5 h-3.5 text-slate-400" /> Year:
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

      {error && (
        <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg flex items-center gap-2 text-rose-700 text-xs">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>Failed to connect to backend: {error}</span>
        </div>
      )}

      {/* KPI Cards Row (Driven by GET /api/overview) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          title="Mine/Bare Footprint"
          value={mineHa.toFixed(2)}
          unit="ha"
          subtitle={`${((mineHa / totalAoiHa) * 100).toFixed(1)}% of total study AOI`}
          trend={`${componentCount} connected components`}
          trendType="neutral"
          icon={Pickaxe}
          badgeColor="bg-rose-50 text-rose-600"
        />
        <KpiCard
          title="Forest / Green Cover"
          value={forestHa.toFixed(2)}
          unit="ha"
          subtitle={`${((forestHa / totalAoiHa) * 100).toFixed(1)}% landscape canopy`}
          trend={selectedYear === 2023 ? "5573.9 ha (peak clearance)" : "Dominant regional matrix"}
          trendType={selectedYear === 2023 ? "down" : "neutral"}
          icon={Trees}
          badgeColor="bg-emerald-50 text-emerald-600"
        />
        <KpiCard
          title="Distance to Water"
          value={waterDistMedian.toFixed(1)}
          unit="m"
          subtitle="Median boundary setback"
          trend={`${waterDistMean.toFixed(0)}m annual mean`}
          trendType="neutral"
          icon={Droplets}
          badgeColor="bg-sky-50 text-sky-600"
        />
        <KpiCard
          title="250m Buffer Exposure"
          value={settlementExposedHa.toFixed(1)}
          unit="ha"
          subtitle={`${settlementExposurePct.toFixed(1)}% settlement within 250m`}
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
            bufferLayerData={data?.buffer_geojson}
          />
        </div>

        {/* Right Summary Column */}
        <div className="space-y-4">


          {/* Land Cover Proportion Chart */}
          <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
            <h3 className="text-xs font-semibold text-slate-800 uppercase tracking-wide mb-2">
              Land Cover Composition ({selectedYear})
            </h3>
            <p className="text-[11px] text-slate-500 mb-3">Area in hectares (Total AOI: {totalAoiHa.toLocaleString()} ha)</p>
            <div className="h-44 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} layout="vertical" margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
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
            <div className="grid grid-cols-2 gap-2 mt-3 text-[11px] text-slate-600 pt-3 border-t border-slate-100">
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-xs bg-[#27AE60]"></span> Forest: {forestHa.toFixed(1)} ha
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-xs bg-[#F39C12]"></span> Settlement: {settlementHa.toFixed(1)} ha
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-xs bg-[#E74C3C]"></span> Mine/Bare: {mineHa.toFixed(1)} ha
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-xs bg-[#2980B9]"></span> Water: {waterHa.toFixed(1)} ha
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
