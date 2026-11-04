import React, { useState } from "react";
import {
  Wifi,
  WifiOff,
  Database,
  Sliders,
  ChevronDown,
  RefreshCw,
  Check,
  AlertTriangle,
} from "lucide-react";
import { DataSourceMode } from "../services/networkManager";
import { useNetworkStatus } from "../hooks/useNetworkStatus";

export interface DataSourceBadgeProps {
  onModeChange?: (mode: DataSourceMode) => void;
  className?: string;
}

export const DataSourceBadge: React.FC<DataSourceBadgeProps> = ({ onModeChange, className = "" }) => {
  const { isOnline, isOpenMeteoReachable, mode, offlineReason, setMode, switchToLive } = useNetworkStatus();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [checking, setChecking] = useState(false);

  const handleSelectMode = async (targetMode: DataSourceMode) => {
    setDropdownOpen(false);
    if (targetMode === "LIVE_OPEN_METEO") {
      setChecking(true);
      await switchToLive();
      setChecking(false);
    } else {
      setMode(targetMode);
    }
    if (onModeChange) onModeChange(targetMode);
  };

  const getBadgeStyle = () => {
    switch (mode) {
      case "LIVE_OPEN_METEO":
        return "bg-emerald-50 text-emerald-800 border-emerald-300 hover:bg-emerald-100";
      case "OFFLINE_DATASET":
        return "bg-amber-50 text-amber-900 border-amber-300 hover:bg-amber-100";
      case "MANUAL_INPUT":
        return "bg-indigo-50 text-indigo-900 border-indigo-300 hover:bg-indigo-100";
    }
  };

  const getDotStyle = () => {
    switch (mode) {
      case "LIVE_OPEN_METEO":
        return "bg-emerald-500 animate-pulse";
      case "OFFLINE_DATASET":
        return "bg-amber-500";
      case "MANUAL_INPUT":
        return "bg-indigo-500";
    }
  };

  const getLabel = () => {
    switch (mode) {
      case "LIVE_OPEN_METEO":
        return "LIVE OPEN-METEO";
      case "OFFLINE_DATASET":
        return "OFFLINE DATASET";
      case "MANUAL_INPUT":
        return "MANUAL INPUT";
    }
  };

  return (
    <div className={`relative inline-block ${className}`}>
      <button
        type="button"
        onClick={() => setDropdownOpen((prev) => !prev)}
        className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider border shadow-sm transition-all ${getBadgeStyle()}`}
        title="Click to inspect or change meteorological data source"
      >
        <span className={`w-2 h-2 rounded-full ${getDotStyle()}`} />
        <span>{getLabel()}</span>
        <ChevronDown className="w-3 h-3 text-slate-500" />
      </button>

      {dropdownOpen && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setDropdownOpen(false)} />
          <div className="absolute right-0 mt-2 w-72 bg-white rounded-2xl shadow-xl border border-slate-200 p-3 z-50 animate-fadeIn space-y-2">
            <div className="px-2 py-1 border-b border-slate-100">
              <span className="text-[10px] font-black uppercase text-slate-400 block tracking-wider">
                Meteorological Data Source
              </span>
              <div className="flex items-center gap-2 mt-1 text-xs text-slate-600">
                <span className={`w-2 h-2 rounded-full ${isOnline ? "bg-emerald-500" : "bg-red-500"}`} />
                <span>{isOnline ? "Internet Connected" : "Device Disconnected (Offline)"}</span>
              </div>
            </div>

            {/* Mode 1: Live Open-Meteo */}
            <button
              type="button"
              onClick={() => handleSelectMode("LIVE_OPEN_METEO")}
              disabled={checking}
              className={`w-full text-left p-2.5 rounded-xl border transition-all flex items-start gap-2.5 ${
                mode === "LIVE_OPEN_METEO"
                  ? "bg-emerald-50 border-emerald-300 text-emerald-950 font-bold"
                  : "bg-white border-transparent hover:bg-slate-50 text-slate-700"
              }`}
            >
              <Wifi className={`w-4 h-4 mt-0.5 ${mode === "LIVE_OPEN_METEO" ? "text-emerald-600" : "text-slate-400"}`} />
              <div className="flex-1">
                <div className="text-xs font-black flex items-center justify-between">
                  <span>LIVE OPEN-METEO</span>
                  {mode === "LIVE_OPEN_METEO" && <Check className="w-3.5 h-3.5 text-emerald-600" />}
                </div>
                <p className="text-[11px] text-slate-500 font-normal">
                  Real-time weather & ET₀ via GPS or regional hub from Open-Meteo API.
                </p>
              </div>
            </button>

            {/* Mode 2: Offline Dataset */}
            <button
              type="button"
              onClick={() => handleSelectMode("OFFLINE_DATASET")}
              className={`w-full text-left p-2.5 rounded-xl border transition-all flex items-start gap-2.5 ${
                mode === "OFFLINE_DATASET"
                  ? "bg-amber-50 border-amber-300 text-amber-950 font-bold"
                  : "bg-white border-transparent hover:bg-slate-50 text-slate-700"
              }`}
            >
              <Database className={`w-4 h-4 mt-0.5 ${mode === "OFFLINE_DATASET" ? "text-amber-600" : "text-slate-400"}`} />
              <div className="flex-1">
                <div className="text-xs font-black flex items-center justify-between">
                  <span>OFFLINE DATASET</span>
                  {mode === "OFFLINE_DATASET" && <Check className="w-3.5 h-3.5 text-amber-600" />}
                </div>
                <p className="text-[11px] text-slate-500 font-normal">
                  5,000 verified FAO-56 benchmark records packaged locally. 100% offline.
                </p>
              </div>
            </button>

            {/* Mode 3: Manual Input */}
            <button
              type="button"
              onClick={() => handleSelectMode("MANUAL_INPUT")}
              className={`w-full text-left p-2.5 rounded-xl border transition-all flex items-start gap-2.5 ${
                mode === "MANUAL_INPUT"
                  ? "bg-indigo-50 border-indigo-300 text-indigo-950 font-bold"
                  : "bg-white border-transparent hover:bg-slate-50 text-slate-700"
              }`}
            >
              <Sliders className={`w-4 h-4 mt-0.5 ${mode === "MANUAL_INPUT" ? "text-indigo-600" : "text-slate-400"}`} />
              <div className="flex-1">
                <div className="text-xs font-black flex items-center justify-between">
                  <span>MANUAL INPUT</span>
                  {mode === "MANUAL_INPUT" && <Check className="w-3.5 h-3.5 text-indigo-600" />}
                </div>
                <p className="text-[11px] text-slate-500 font-normal">
                  Enter custom weather observations and soil readings manually.
                </p>
              </div>
            </button>

            {offlineReason && (
              <div className="bg-slate-50 p-2 rounded-lg text-[10px] text-slate-600 border border-slate-200">
                <strong>Current Diagnostic:</strong> {offlineReason}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};
