import React, { useState, useEffect } from "react";
import {
  History,
  Search,
  Filter,
  Trash2,
  Eye,
  Calendar,
  Clock,
  Droplets,
  Layers,
  RefreshCw,
  X,
  AlertTriangle,
} from "lucide-react";
import { api } from "../services/api";
import { PredictionResponse } from "../types";

export const HistoryView: React.FC = () => {
  const [history, setHistory] = useState<PredictionResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedCrop, setSelectedCrop] = useState("");
  const [selectedSoil, setSelectedSoil] = useState("");
  const [availableCrops, setAvailableCrops] = useState<string[]>([]);

  // Modal State
  const [selectedRecord, setSelectedRecord] = useState<PredictionResponse | null>(null);

  useEffect(() => {
    api.getCrops()
      .then((crops) => {
        if (crops && crops.length > 0) {
          const names = Array.from(new Set(crops.map((c) => c.name))).sort();
          setAvailableCrops(names);
        }
      })
      .catch((err) => console.error("Failed to load crops metadata:", err));
  }, []);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      const data = await api.getHistory(100, 0, selectedCrop || undefined, selectedSoil || undefined);
      setHistory(data);
    } catch (err) {
      console.error("Failed to load history:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [selectedCrop, selectedSoil]);

  const handleDelete = async (id?: string) => {
    if (!id) return;
    if (window.confirm("Are you sure you want to delete this prediction entry?")) {
      try {
        await api.deleteHistoryItem(id);
        setHistory((prev) => prev.filter((item) => item.id !== id));
      } catch (err: any) {
        alert("Failed to delete: " + err.message);
      }
    }
  };

  const handleClearAll = async () => {
    if (window.confirm("Are you sure you want to delete ALL historical predictions? This cannot be undone.")) {
      try {
        await api.clearHistory();
        setHistory([]);
      } catch (err: any) {
        alert("Failed to clear history: " + err.message);
      }
    }
  };

  const filteredHistory = history.filter((item) => {
    const q = search.toLowerCase();
    return (
      item.crop_type.toLowerCase().includes(q) ||
      item.soil_type.toLowerCase().includes(q) ||
      item.growth_stage.toLowerCase().includes(q) ||
      item.model_used.toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-emerald-800 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
            Audit Trail
          </span>
          <h1 className="text-2xl font-black text-slate-900 mt-2">
            Prediction History & Logs
          </h1>
          <p className="text-sm text-slate-600 mt-1">
            Search, filter, inspect, and export previous irrigation runs saved in SQLite.
          </p>
        </div>
        <div className="flex items-center gap-2 self-start sm:self-auto">
          <button
            onClick={fetchHistory}
            className="p-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-600"
            title="Refresh logs"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
          {history.length > 0 && (
            <button
              onClick={handleClearAll}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold bg-red-50 text-red-700 hover:bg-red-100 border border-red-200 transition-colors"
            >
              <Trash2 className="w-3.5 h-3.5" />
              Clear History
            </button>
          )}
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm flex flex-col md:flex-row gap-3">
        <div className="flex-1 relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
          <input
            type="text"
            placeholder="Search by crop, soil, stage, or model..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 font-medium focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
        </div>

        <div className="flex gap-2">
          <select
            value={selectedCrop}
            onChange={(e) => setSelectedCrop(e.target.value)}
            className="bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs font-semibold text-slate-700 focus:outline-none"
          >
            <option value="">All Crops</option>
            {(availableCrops.length > 0
              ? availableCrops
              : [
                  "Banana", "Barley", "Black Gram", "Brinjal", "Cabbage", "Carrot", "Cauliflower",
                  "Chickpea", "Chilli", "Cotton", "Field Pea", "Finger Millet (Ragi)", "Grapes",
                  "Green Gram", "Groundnut", "Lentil", "Maize", "Mango", "Mustard", "Onion",
                  "Papaya", "Pearl Millet (Bajra)", "Pigeon Pea (Toor Dal)", "Pomegranate",
                  "Potato", "Rice (Paddy)", "Sorghum (Jowar)", "Soybean", "Sugarcane", "Sunflower",
                  "Tobacco", "Tomato", "Watermelon", "Wheat"
                ]
            ).map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>

          <select
            value={selectedSoil}
            onChange={(e) => setSelectedSoil(e.target.value)}
            className="bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs font-semibold text-slate-700 focus:outline-none"
          >
            <option value="">All Soils</option>
            {["Sandy", "Sandy Loam", "Loamy", "Clay Loam", "Silty", "Clay"].map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* History Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-600 text-xs uppercase font-semibold border-b border-slate-100">
              <tr>
                <th className="px-6 py-3.5">Timestamp</th>
                <th className="px-6 py-3.5">Crop & Stage</th>
                <th className="px-6 py-3.5">Area</th>
                <th className="px-6 py-3.5">Soil & Moisture</th>
                <th className="px-6 py-3.5">Water Needed (Litres)</th>
                <th className="px-6 py-3.5">Urgency</th>
                <th className="px-6 py-3.5">Model</th>
                <th className="px-6 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700 text-xs">
              {filteredHistory.length > 0 ? (
                filteredHistory.map((item, idx) => (
                  <tr key={item.id || idx} className="hover:bg-slate-50/60 transition-colors">
                    <td className="px-6 py-4 font-mono text-slate-500">
                      {item.timestamp ? item.timestamp.replace("T", " ").substring(0, 16) : "Recent"}
                    </td>
                    <td className="px-6 py-4">
                      <span className="font-bold text-slate-900 block">{item.crop_type}</span>
                      <span className="text-[11px] text-slate-500">{item.growth_stage}</span>
                    </td>
                    <td className="px-6 py-4">
                      {item.area} {item.area_unit}
                    </td>
                    <td className="px-6 py-4">
                      <span>{item.soil_type}</span>
                      <span className="text-slate-500 block text-[11px]">
                        {item.soil_moisture_pct}% moisture
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="font-black text-emerald-800 text-sm">
                        {item.water_requirement_litres.toLocaleString()} L
                      </span>
                      <span className="text-slate-500 block text-[11px]">
                        ({item.water_requirement_mm.toFixed(1)} mm depth)
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`inline-block px-2 py-0.5 rounded-full text-[11px] font-semibold border ${
                          item.urgency_level === "Critical"
                            ? "bg-red-50 text-red-700 border-red-200"
                            : item.urgency_level === "High"
                            ? "bg-amber-50 text-amber-700 border-amber-200"
                            : item.urgency_level === "Moderate"
                            ? "bg-blue-50 text-blue-700 border-blue-200"
                            : "bg-emerald-50 text-emerald-700 border-emerald-200"
                        }`}
                      >
                        {item.urgency_level}
                      </span>
                    </td>
                    <td className="px-6 py-4 font-medium uppercase text-slate-600">
                      {item.model_used}
                    </td>
                    <td className="px-6 py-4 text-right space-x-2">
                      <button
                        onClick={() => setSelectedRecord(item)}
                        className="p-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700"
                        title="View Details"
                      >
                        <Eye className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => handleDelete(item.id)}
                        className="p-1.5 rounded-lg bg-red-50 hover:bg-red-100 text-red-600"
                        title="Delete Entry"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={8} className="px-6 py-12 text-center text-slate-400">
                    {loading ? "Loading prediction audit logs..." : "No matching historical records found."}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Details Modal */}
      {selectedRecord && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl relative border border-slate-200 max-h-[90vh] overflow-y-auto">
            <button
              onClick={() => setSelectedRecord(null)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 p-1"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-2 mb-4">
              <span className="w-3 h-3 rounded-full bg-emerald-500" />
              <h3 className="font-black text-slate-900 text-lg">
                {selectedRecord.crop_type} – Plot Evaluation
              </h3>
            </div>

            <div className="bg-emerald-950 text-white p-5 rounded-2xl mb-4">
              <span className="text-xs uppercase font-bold text-emerald-300 block">
                Total Recommended Water
              </span>
              <div className="text-3xl font-black mt-1">
                {selectedRecord.water_requirement_litres.toLocaleString()}{" "}
                <span className="text-base text-emerald-400">Litres</span>
              </div>
              <p className="text-xs text-emerald-200 mt-1">
                {selectedRecord.water_requirement_m3.toLocaleString()} m³ volume across{" "}
                {selectedRecord.area} {selectedRecord.area_unit}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs mb-4">
              <div className="bg-slate-50 p-3 rounded-xl">
                <span className="text-slate-500 block">Growth Stage</span>
                <span className="font-bold text-slate-800">{selectedRecord.growth_stage}</span>
              </div>
              <div className="bg-slate-50 p-3 rounded-xl">
                <span className="text-slate-500 block">Soil Profile</span>
                <span className="font-bold text-slate-800">
                  {selectedRecord.soil_type} ({selectedRecord.soil_moisture_pct}% moisture)
                </span>
              </div>
              <div className="bg-slate-50 p-3 rounded-xl">
                <span className="text-slate-500 block">Gross Depth (GIR)</span>
                <span className="font-bold text-slate-800">
                  {selectedRecord.gross_irrigation_requirement_mm.toFixed(1)} mm
                </span>
              </div>
              <div className="bg-slate-50 p-3 rounded-xl">
                <span className="text-slate-500 block">Model Architecture</span>
                <span className="font-bold text-slate-800 uppercase">
                  {selectedRecord.model_used}
                </span>
              </div>
            </div>

            {selectedRecord.recommended_schedule && (
              <div className="p-4 bg-slate-50 rounded-xl text-xs space-y-1 mb-4">
                <span className="font-bold text-slate-800 block">Irrigation Schedule:</span>
                <p>
                  Interval: Every {selectedRecord.recommended_schedule.frequency_days} day(s) for{" "}
                  {selectedRecord.recommended_schedule.duration_hours} hour(s).
                </p>
                <p className="text-emerald-700 font-semibold">
                  Window: {selectedRecord.recommended_schedule.best_time}
                </p>
              </div>
            )}

            <button
              onClick={() => setSelectedRecord(null)}
              className="w-full bg-slate-900 text-white font-bold py-2.5 rounded-xl text-xs hover:bg-slate-800"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
