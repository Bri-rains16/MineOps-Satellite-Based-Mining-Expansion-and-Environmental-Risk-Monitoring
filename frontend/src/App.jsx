import React, { useState } from "react";
import Sidebar from "./components/Sidebar";
import OverviewPage from "./pages/OverviewPage";
import RandomForestPage from "./pages/RandomForestPage";
import UnetPage from "./pages/UnetPage";
import ProximityAnalysisPage from "./pages/ProximityAnalysisPage";
import ReportsPage from "./pages/ReportsPage";
import { Search, Globe } from "lucide-react";

export default function App() {
  // 5 Active Navigation Pages:
  // 'overview' | 'random-forest' | 'unet' | 'proximity' | 'reports'
  const [activePage, setActivePage] = useState("overview");
  const [selectedYear, setSelectedYear] = useState(2026);

  const renderActivePage = () => {
    switch (activePage) {
      case "overview":
        return <OverviewPage selectedYear={selectedYear} setSelectedYear={setSelectedYear} />;
      case "random-forest":
        return <RandomForestPage selectedYear={selectedYear} setSelectedYear={setSelectedYear} />;
      case "unet":
        return <UnetPage selectedYear={selectedYear} setSelectedYear={setSelectedYear} />;
      case "proximity":
        return <ProximityAnalysisPage selectedYear={selectedYear} setSelectedYear={setSelectedYear} />;
      case "reports":
        return <ReportsPage />;
      default:
        return <OverviewPage selectedYear={selectedYear} setSelectedYear={setSelectedYear} />;
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 font-sans text-slate-800 antialiased">
      {/* Dark Navy Sidebar */}
      <Sidebar activePage={activePage} setActivePage={setActivePage} />

      {/* Main Workspace */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Top Operational Header */}
        <header className="h-16 bg-white border-b border-slate-200 px-8 flex items-center justify-between shrink-0 z-20">
          <div className="flex items-center gap-3">
            <span className="text-xs font-semibold uppercase tracking-wider text-teal-700 bg-teal-50 px-2.5 py-1 rounded-md border border-teal-100 flex items-center gap-1.5">
              <Globe className="w-3.5 h-3.5" /> AOI: Zawar Mines, Rajasthan
            </span>
            <span className="text-xs text-slate-400">&bull;</span>
            <span className="text-xs text-slate-500 font-mono">EPSG:32643 &bull; Sentinel-2 MSI</span>
          </div>

          <div className="flex items-center gap-4 text-xs">
            <div className="hidden sm:flex items-center gap-2 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-lg text-slate-500">
              <Search className="w-3.5 h-3.5 text-slate-400" />
              <span>Search coordinates or pit ID...</span>
            </div>

            <div className="flex items-center gap-2 pl-2 border-l border-slate-200">
              <span className="w-2 h-2 rounded-full bg-teal-500"></span>
              <span className="font-semibold text-slate-700">Epoch: {selectedYear}</span>
            </div>
          </div>
        </header>

        {/* Scrollable Page Body */}
        <main className="flex-1 overflow-y-auto p-8 bg-slate-50/70">
          <div className="max-w-7xl mx-auto">
            {renderActivePage()}
          </div>
        </main>
      </div>
    </div>
  );
}