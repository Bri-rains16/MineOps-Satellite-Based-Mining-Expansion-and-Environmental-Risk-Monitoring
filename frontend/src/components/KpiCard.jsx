import React from "react";
import { ArrowUpRight, ArrowDownRight, Minus } from "lucide-react";

export default function KpiCard({ title, value, unit, subtitle, trend, trendType, icon: Icon, badgeColor }) {
  return (
    <div className="bg-white border border-slate-200/80 rounded-xl p-4 shadow-xs flex flex-col justify-between hover:border-slate-300 transition-colors">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">{title}</p>
          <div className="flex items-baseline gap-1 mt-1.5">
            <span className="text-2xl font-bold text-slate-900 tracking-tight">{value}</span>
            {unit && <span className="text-xs font-medium text-slate-500">{unit}</span>}
          </div>
        </div>
        {Icon && (
          <div className={`p-2 rounded-lg ${badgeColor || "bg-teal-50 text-teal-600"}`}>
            <Icon className="w-4 h-4" />
          </div>
        )}
      </div>

      <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between text-xs">
        <span className="text-slate-500 text-[11px]">{subtitle}</span>
        {trend && (
          <span
            className={`flex items-center text-[11px] font-medium ${
              trendType === "up"
                ? "text-rose-600"
                : trendType === "down"
                ? "text-emerald-600"
                : "text-slate-500"
            }`}
          >
            {trendType === "up" && <ArrowUpRight className="w-3 h-3 mr-0.5" />}
            {trendType === "down" && <ArrowDownRight className="w-3 h-3 mr-0.5" />}
            {trendType === "neutral" && <Minus className="w-3 h-3 mr-0.5" />}
            {trend}
          </span>
        )}
      </div>
    </div>
  );
}
