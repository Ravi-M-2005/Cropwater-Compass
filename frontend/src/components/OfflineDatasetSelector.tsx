import React, { useState, useMemo } from "react";
import {
  Database,
  Search,
  Filter,
  Calendar,
  MapPin,
  Sprout,
  Droplets,
  Thermometer,
  Wind,
  Sun,
  CloudRain,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Sliders,
  Wifi,
  X,
  ChevronDown,
  Layers,
} from "lucide-react";
import { OFFLINE_DATASET, OfflineDatasetRecord } from "../data/offlineDataset";
import { SearchableSelect, SelectOption } from "./SearchableSelect";

export interface OfflineDatasetSelectorProps {
  onSelectRecord: (record: OfflineDatasetRecord) => void;
  selectedRecordId?: string | null;
  initialCrop?: string;
  initialLocation?: string;
  initialSoil?: string;
  onSwitchToLive?: () => void;
  onSwitchToManual?: () => void;
  offlineReason?: string | null;
}

export const OfflineDatasetSelector: React.FC<OfflineDatasetSelectorProps> = ({
  onSelectRecord,
  selectedRecordId,
  initialCrop,
  initialLocation,
  initialSoil,
  onSwitchToLive,
  onSwitchToManual,
  offlineReason,
}) => {
  const [filterCrop, setFilterCrop] = useState<string>(initialCrop || "");
  const [filterState, setFilterState] = useState<string>("");
  const [filterLocation, setFilterLocation] = useState<string>(initialLocation || "");
  const [filterSoil, setFilterSoil] = useState<string>(initialSoil || "");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [sortBy, setSortBy] = useState<"date" | "temp" | "et0" | "rainfall">("date");

  // Extract unique filter lists from actual dataset
  const availableCrops = useMemo(() => {
    return Array.from(new Set(OFFLINE_DATASET.map((r) => r.crop_type))).sort();
  }, []);

  const availableStates = useMemo(() => {
    return Array.from(new Set(OFFLINE_DATASET.map((r) => r.state))).sort();
  }, []);

  const availableLocations = useMemo(() => {
    return Array.from(new Set(OFFLINE_DATASET.map((r) => r.location))).sort();
  }, []);

  const availableSoils = useMemo(() => {
    return Array.from(new Set(OFFLINE_DATASET.map((r) => r.soil_type))).sort();
  }, []);

  // Filter records
  const filteredRecords = useMemo(() => {
    return OFFLINE_DATASET.filter((rec) => {
      if (filterCrop && rec.crop_type !== filterCrop) return false;
      if (filterState && rec.state !== filterState) return false;
      if (filterLocation && rec.location !== filterLocation) return false;
      if (filterSoil && rec.soil_type !== filterSoil) return false;
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        const match =
          rec.id.toLowerCase().includes(q) ||
          rec.crop_type.toLowerCase().includes(q) ||
          rec.location.toLowerCase().includes(q) ||
          rec.state.toLowerCase().includes(q) ||
          rec.soil_type.toLowerCase().includes(q) ||
          rec.growth_stage.toLowerCase().includes(q);
        if (!match) return false;
      }
      return true;
    }).sort((a, b) => {
      if (sortBy === "temp") return b.temperature_c - a.temperature_c;
      if (sortBy === "et0") return b.et0_mm - a.et0_mm;
      if (sortBy === "rainfall") return b.rainfall_mm - a.rainfall_mm;
      return b.date.localeCompare(a.date);
    });
  }, [filterCrop, filterState, filterLocation, filterSoil, searchQuery, sortBy]);

  const currentlySelected = useMemo(() => {
    return OFFLINE_DATASET.find((r) => r.id === selectedRecordId) || null;
  }, [selectedRecordId]);

  const clearAllFilters = () => {
    setFilterCrop("");
    setFilterState("");
    setFilterLocation("");
    setFilterSoil("");
    setSearchQuery("");
  };

  return (
    <div className="bg-amber-50/40 rounded-2xl border-2 border-amber-300 p-5 space-y-5 animate-fadeIn">
      {/* Header and Live Mode Toggle */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-amber-200 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-black uppercase tracking-wider bg-amber-500 text-white shadow-sm">
              <Database className="w-3.5 h-3.5" />
              OFFLINE DATASET MODE
            </span>
            <span className="text-xs font-semibold text-amber-900">
              5,000 Verified FAO-56 Benchmark Records
            </span>
          </div>
          <p className="text-xs text-amber-800 mt-1">
            {offlineReason || "Internet or Open-Meteo API is currently unreachable. You can select an authentic historical farm record below or enter values manually."}
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto flex-shrink-0">
          {onSwitchToLive && (
            <button
              type="button"
              onClick={onSwitchToLive}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white shadow-sm transition-all"
            >
              <Wifi className="w-3.5 h-3.5" />
              Switch to Live Mode
            </button>
          )}

          {onSwitchToManual && (
            <button
              type="button"
              onClick={onSwitchToManual}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 shadow-sm transition-all"
            >
              <Sliders className="w-3.5 h-3.5 text-slate-500" />
              Manual Input
            </button>
          )}
        </div>
      </div>

      {/* Selected Record Highlights Banner */}
      {currentlySelected && (
        <div className="bg-white rounded-xl p-4 border border-amber-300 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span className="text-xs font-black uppercase text-emerald-800">
                Active Offline Record: {currentlySelected.id}
              </span>
              <span className="text-xs text-slate-500">
                • Observed on <strong>{currentlySelected.date}</strong>
              </span>
            </div>
            <div className="text-sm font-black text-slate-900 flex items-center gap-2">
              <span>{currentlySelected.crop_type}</span>
              <span className="text-xs font-medium text-slate-500">({currentlySelected.growth_stage} stage)</span>
              <span>•</span>
              <span>{currentlySelected.location}, {currentlySelected.state}</span>
              <span>•</span>
              <span className="text-xs font-semibold text-slate-600">{currentlySelected.soil_type}</span>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3 text-xs bg-amber-50/80 px-3 py-2 rounded-lg border border-amber-200">
            <div>
              <span className="text-[10px] text-slate-500 block">Air Temp</span>
              <strong>{currentlySelected.temperature_c}°C</strong>
            </div>
            <div>
              <span className="text-[10px] text-slate-500 block">Humidity</span>
              <strong>{currentlySelected.humidity_pct}%</strong>
            </div>
            <div>
              <span className="text-[10px] text-slate-500 block">Wind</span>
              <strong>{currentlySelected.wind_speed_kmh} km/h</strong>
            </div>
            <div>
              <span className="text-[10px] text-slate-500 block">Rainfall</span>
              <strong>{currentlySelected.rainfall_mm} mm</strong>
            </div>
            <div>
              <span className="text-[10px] text-slate-500 block">Ref. ET₀</span>
              <strong className="text-emerald-700">{currentlySelected.et0_mm} mm/d</strong>
            </div>
          </div>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="bg-white rounded-xl p-4 border border-amber-200 shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold text-slate-800 uppercase tracking-wide flex items-center gap-1.5">
            <Filter className="w-3.5 h-3.5 text-amber-600" />
            Filter Offline Dataset
          </span>
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500">
              {filteredRecords.length.toLocaleString()} matching records
            </span>
            {(filterCrop || filterState || filterLocation || filterSoil || searchQuery) && (
              <button
                type="button"
                onClick={clearAllFilters}
                className="text-xs font-bold text-amber-700 hover:text-amber-900 underline flex items-center gap-1"
              >
                <X className="w-3 h-3" />
                Reset Filters
              </button>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-2.5">
          {/* Search text */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-3" />
            <input
              type="text"
              placeholder="Search ID, crop, town..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-8 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-amber-500"
            />
          </div>

          {/* Crop Filter */}
          <select
            value={filterCrop}
            onChange={(e) => setFilterCrop(e.target.value)}
            className="bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-amber-500"
          >
            <option value="">All 34 Crops</option>
            {availableCrops.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>

          {/* State Filter */}
          <select
            value={filterState}
            onChange={(e) => {
              setFilterState(e.target.value);
              setFilterLocation(""); // reset district when state changes
            }}
            className="bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-amber-500"
          >
            <option value="">All Indian States</option>
            {availableStates.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>

          {/* District / Location Filter */}
          <select
            value={filterLocation}
            onChange={(e) => setFilterLocation(e.target.value)}
            className="bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-amber-500"
          >
            <option value="">All 26 Locations</option>
            {availableLocations
              .filter((loc) => !filterState || OFFLINE_DATASET.some((r) => r.location === loc && r.state === filterState))
              .map((loc) => (
                <option key={loc} value={loc}>{loc}</option>
              ))}
          </select>

          {/* Soil Filter */}
          <select
            value={filterSoil}
            onChange={(e) => setFilterSoil(e.target.value)}
            className="bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-amber-500"
          >
            <option value="">All Soil Types</option>
            {availableSoils.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Records List / Empty Notice */}
      {filteredRecords.length === 0 ? (
        <div className="bg-white rounded-xl p-8 border border-amber-200 text-center space-y-3">
          <div className="w-12 h-12 rounded-full bg-amber-100 text-amber-700 flex items-center justify-center mx-auto">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <h4 className="font-bold text-slate-900 text-base">No Matching Dataset Record Found</h4>
          <p className="text-xs text-slate-600 max-w-md mx-auto">
            No historical records match the specific combination of <strong>{filterCrop || "crop"}</strong> and{" "}
            <strong>{filterLocation || filterState || "location"}</strong>. You can reset filters or enter weather parameters manually.
          </p>
          <div className="flex justify-center gap-3 pt-2">
            <button
              type="button"
              onClick={clearAllFilters}
              className="text-xs font-bold bg-amber-100 hover:bg-amber-200 text-amber-900 px-4 py-2 rounded-xl transition-colors"
            >
              Reset Filters
            </button>
            {onSwitchToManual && (
              <button
                type="button"
                onClick={onSwitchToManual}
                className="text-xs font-bold bg-slate-900 hover:bg-slate-800 text-white px-4 py-2 rounded-xl transition-colors"
              >
                Switch to Manual Input
              </button>
            )}
          </div>
        </div>
      ) : (
        <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
          {filteredRecords.slice(0, 50).map((rec) => {
            const isSelected = selectedRecordId === rec.id;
            return (
              <div
                key={rec.id}
                onClick={() => onSelectRecord(rec)}
                className={`p-3.5 rounded-xl border transition-all cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
                  isSelected
                    ? "bg-emerald-50 border-emerald-500 shadow-sm ring-2 ring-emerald-500/20"
                    : "bg-white border-slate-200 hover:border-amber-300 hover:bg-amber-50/20"
                }`}
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-[11px] font-bold text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">
                      {rec.id}
                    </span>
                    <span className="font-bold text-slate-900 text-sm">{rec.crop_type}</span>
                    <span className="text-xs text-slate-500">({rec.growth_stage})</span>
                    <span className="text-xs text-slate-400">•</span>
                    <span className="text-xs font-medium text-slate-700">{rec.location}, {rec.state}</span>
                  </div>
                  <div className="flex items-center gap-2 text-[11px] text-slate-500">
                    <span>Soil: <strong>{rec.soil_type}</strong> ({rec.soil_moisture_pct}%)</span>
                    <span>•</span>
                    <span>Date: <strong>{rec.date}</strong></span>
                    <span>•</span>
                    <span>Delivery: <strong>{rec.irrigation_method}</strong></span>
                  </div>
                </div>

                <div className="flex items-center gap-3 self-end sm:self-auto flex-shrink-0">
                  <div className="grid grid-cols-4 gap-2 text-right text-xs">
                    <div>
                      <span className="text-[10px] text-slate-400 block">Temp</span>
                      <span className="font-bold text-slate-800">{rec.temperature_c}°C</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 block">Hum</span>
                      <span className="font-bold text-slate-800">{rec.humidity_pct}%</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 block">Rain</span>
                      <span className="font-bold text-slate-800">{rec.rainfall_mm}mm</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 block">ET₀</span>
                      <span className="font-extrabold text-emerald-700">{rec.et0_mm}</span>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectRecord(rec);
                    }}
                    className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-colors ${
                      isSelected
                        ? "bg-emerald-600 text-white"
                        : "bg-slate-100 hover:bg-emerald-100 hover:text-emerald-800 text-slate-700"
                    }`}
                  >
                    {isSelected ? "Selected" : "Select"}
                  </button>
                </div>
              </div>
            );
          })}
          {filteredRecords.length > 50 && (
            <p className="text-[11px] text-slate-500 text-center pt-1 italic">
              Showing first 50 of {filteredRecords.length.toLocaleString()} matching records. Use the search and filters above to refine.
            </p>
          )}
        </div>
      )}
    </div>
  );
};
