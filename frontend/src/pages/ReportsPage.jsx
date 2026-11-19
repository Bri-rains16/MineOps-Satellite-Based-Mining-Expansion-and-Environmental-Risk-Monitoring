import React from "react";
import {
  Database, Layers, ShieldCheck, ArrowDownToLine
} from "lucide-react";
import api from "../services/api";

export default function ReportsPage() {
  const handleFeaturedDownload = (relPath, filename) => {
    const downloadUrl = api.getDownloadUrl(relPath);
    const link = document.createElement("a");
    link.href = downloadUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="pb-2 border-b border-slate-200">
        <h2 className="text-xl font-bold text-slate-900 tracking-tight">Reports &amp; Verified Output Exports</h2>
        <p className="text-xs text-slate-500 mt-0.5">
          Curated primary project exports and analytical outputs verified by the backend
        </p>
      </div>

      {/* Featured Primary Exports Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs flex flex-col justify-between">
          <div>
            <div className="w-9 h-9 rounded-lg bg-teal-50 text-teal-600 flex items-center justify-center mb-3">
              <Database className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-bold text-slate-900">RF Clean Proximity Summary</h3>
          </div>
          <button
            onClick={() => handleFeaturedDownload("proximity_rf_clean_2021-2026/proximity_clean_summary.csv", "proximity_clean_summary.csv")}
            className="mt-4 w-full py-2 px-3 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold flex items-center justify-center gap-2 transition-colors cursor-pointer"
          >
            <ArrowDownToLine className="w-3.5 h-3.5" /> Download CSV
          </button>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs flex flex-col justify-between">
          <div>
            <div className="w-9 h-9 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center mb-3">
              <Layers className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-bold text-slate-900">Clean RF Polygon Vectors (2026)</h3>
          </div>
          <button
            onClick={() => handleFeaturedDownload("polygons_rf_clean_2021-2026/zawar_all_classes_clean_2026.geojson", "zawar_all_classes_clean_2026.geojson")}
            className="mt-4 w-full py-2 px-3 rounded-lg bg-teal-600 hover:bg-teal-500 text-white text-xs font-semibold flex items-center justify-center gap-2 transition-colors cursor-pointer"
          >
            <ArrowDownToLine className="w-3.5 h-3.5" /> Download GeoJSON
          </button>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs flex flex-col justify-between">
          <div>
            <div className="w-9 h-9 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center mb-3">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-bold text-slate-900">U-Net Historical Expansion JSON</h3>
          </div>
          <button
            onClick={() => handleFeaturedDownload("reports/unet_expansion.json", "unet_expansion.json")}
            className="mt-4 w-full py-2 px-3 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold flex items-center justify-center gap-2 transition-colors cursor-pointer"
          >
            <ArrowDownToLine className="w-3.5 h-3.5" /> Download JSON
          </button>
        </div>
      </div>
    </div>
  );
}
