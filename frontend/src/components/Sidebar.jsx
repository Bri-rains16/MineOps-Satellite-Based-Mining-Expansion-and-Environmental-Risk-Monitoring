import React from "react";
import { 
  LayoutDashboard, 
  Trees, 
  Pickaxe, 
  MapPin, 
  FileText 
} from "lucide-react";

// Exactly 5 final navigation pages
const NAV_ITEMS = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "random-forest", label: "Random Forest", icon: Trees },
  { id: "unet", label: "U-Net", icon: Pickaxe },
  { id: "proximity", label: "Proximity Analysis", icon: MapPin },
  { id: "reports", label: "Reports & Downloads", icon: FileText }
];

export default function Sidebar({ activePage, setActivePage }) {
  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col shrink-0 text-slate-300">
      {/* Brand Header */}
      <div className="h-16 px-6 flex items-center gap-3 border-b border-slate-800 bg-slate-950/40">
        <div className="w-8 h-8 rounded-md bg-teal-600 flex items-center justify-center text-white shadow-sm font-bold text-sm tracking-wide">
          MO
        </div>
        <div>
          <h1 className="font-semibold text-slate-100 text-sm tracking-tight flex items-center gap-1.5">
            MineOps <span className="text-[10px] px-1.5 py-0.5 rounded bg-teal-500/20 text-teal-400 font-mono font-normal">GIS</span>
          </h1>
          <p className="text-[11px] text-slate-400">Satellite Mining Monitor</p>
        </div>
      </div>

      {/* Target Site Badge */}
      <div className="px-4 py-3 mx-3 my-3 rounded-lg bg-slate-800/60 border border-slate-700/50">
        <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1">
          <span className="font-medium text-slate-300">Active AOI</span>
          {/* <span className="text-teal-400 font-mono text-[10px]">EPSG:32643</span> */}
        </div>
        <p className="text-xs font-medium text-slate-200 truncate">Zawar Mines, Udaipur</p>
        <p className="text-[10px] text-slate-400 mt-0.5">Sentinel-2 (10m Resolution)</p>
      </div>

      {/* 5-Item Navigation */}
      <nav className="flex-1 px-3 py-2 space-y-1">
        <p className="px-3 pb-2 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
          Analytical Modules
        </p>
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = activePage === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActivePage(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                isActive
                  ? "bg-teal-600/20 text-teal-300 border border-teal-500/30 shadow-sm"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? "text-teal-400" : "text-slate-400"}`} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* System Status Footer */}
      <div className="p-4 border-t border-slate-800 text-[11px] text-slate-400">
        <div className="flex items-center gap-2 mb-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span className="text-slate-300 font-medium">Analytical Pipeline</span>
        </div>
        <p className="text-[10px] text-slate-400">Multi-Temporal Range: 2021 – 2026</p>
      </div>
    </aside>
  );
}
