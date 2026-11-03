import React, { useState, useEffect } from "react";
import {
  Droplets,
  CloudSun,
  Layers,
  Sparkles,
  Clock,
  Calendar,
  AlertTriangle,
  CheckCircle,
  HelpCircle,
  Cpu,
  ArrowRight,
  Info,
  Check,
  ChevronRight,
  Sprout,
  MapPin,
  RefreshCw,
} from "lucide-react";
import { api } from "../services/api";
import {
  PredictionRequest,
  PredictionResponse,
  CropInfo,
  SoilInfo,
  IrrigationMethodInfo,
} from "../types";
import { SearchableSelect, SelectOption } from "./SearchableSelect";

interface PredictionViewProps {
  onNavigateToShap?: (data: PredictionRequest) => void;
}

export const PredictionView: React.FC<PredictionViewProps> = ({ onNavigateToShap }) => {
  // Form State
  const [formData, setFormData] = useState<PredictionRequest>({
    crop_type: "Wheat",
    growth_stage: "Mid-season",
    area: 2.0,
    area_unit: "hectares",
    soil_type: "Loamy",
    soil_moisture_pct: 26.0,
    soil_ph: 6.8,
    temperature_c: 26.8,
    humidity_pct: 54.0,
    wind_speed_kmh: 11.5,
    rainfall_mm: 0.0,
    solar_radiation: 18.0,
    et0_mm: 3.8,
    irrigation_method: "Drip",
    model_name: "xgboost",
  });

  // Catalogs
  const [crops, setCrops] = useState<CropInfo[]>([]);
  const [soils, setSoils] = useState<SoilInfo[]>([]);
  const [methods, setMethods] = useState<IrrigationMethodInfo[]>([]);
  const [locations, setLocations] = useState<Record<string, any>>({});
  const [selectedLocation, setSelectedLocation] = useState<string>("Bengaluru");
  const [weatherSource, setWeatherSource] = useState<string | null>(null);
  const [weatherError, setWeatherError] = useState<string | null>(null);

  // Submission & Results
  const [loading, setLoading] = useState(false);
  const [weatherLoading, setWeatherLoading] = useState(false);
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Load catalogs and initial prediction on mount
  useEffect(() => {
    const fetchMetadataAndInitial = async () => {
      try {
        const [cList, sList, mList, locRes] = await Promise.all([
          api.getCrops(),
          api.getSoils(),
          api.getIrrigationMethods(),
          api.getPresetLocations(),
        ]);
        setCrops(cList);
        setSoils(sList);
        setMethods(mList);

        const locMap = locRes.locations || {};
        setLocations(locMap);

        // Fetch live weather for initial location (Bengaluru or Devanahalli)
        const initialLoc = locMap["Bengaluru"] || locMap["Devanahalli"] || Object.values(locMap)[0];
        if (initialLoc) {
          const locName = locMap["Bengaluru"] ? "Bengaluru" : Object.keys(locMap)[0];
          setSelectedLocation(locName);
          try {
            const w = await api.getCurrentWeather(initialLoc.lat, initialLoc.lon, locName);
            setFormData((prev) => ({
              ...prev,
              temperature_c: w.temperature_c,
              humidity_pct: w.humidity_pct,
              wind_speed_kmh: w.wind_speed_kmh,
              rainfall_mm: w.rainfall_mm,
              solar_radiation: w.solar_radiation,
              et0_mm: w.et0_mm,
            }));
            setWeatherSource(w.source);
          } catch {
            // keep default
          }
        }

        // Compute initial prediction
        const initialRes = await api.predict(formData);
        setResult(initialRes);
      } catch (err) {
        console.warn("Could not load initial data:", err);
      }
    };
    fetchMetadataAndInitial();
  }, []);

  const handleChange = (field: keyof PredictionRequest, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleFetchWeatherForLocation = async (locName: string) => {
    const loc = locations[locName];
    if (!loc) return;
    try {
      setWeatherLoading(true);
      setWeatherError(null);
      const w = await api.getCurrentWeather(loc.lat, loc.lon, locName);
      setFormData((prev) => ({
        ...prev,
        temperature_c: w.temperature_c,
        humidity_pct: w.humidity_pct,
        wind_speed_kmh: w.wind_speed_kmh,
        rainfall_mm: w.rainfall_mm,
        solar_radiation: w.solar_radiation,
        et0_mm: w.et0_mm,
      }));
      setWeatherSource(w.source);
    } catch (err: any) {
      setWeatherError(err.message || "Failed to retrieve live weather.");
    } finally {
      setWeatherLoading(false);
    }
  };

  const handleLocationSelect = (locName: string) => {
    setSelectedLocation(locName);
    handleFetchWeatherForLocation(locName);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError(null);
      const res = await api.predict(formData);
      setResult(res);
    } catch (err: any) {
      setError(err.message || "Prediction execution failed");
    } finally {
      setLoading(false);
    }
  };

  const selectedCrop = crops.find((c) => c.name === formData.crop_type);
  const selectedSoil = soils.find((s) => s.name === formData.soil_type);

  // Dynamic Kc & ETc calculation
  const getCurrentKc = () => {
    if (!selectedCrop) return 0.85;
    const stage = formData.growth_stage.toLowerCase();
    if (stage.includes("init")) return selectedCrop.kc_initial;
    if (stage.includes("mid")) return selectedCrop.kc_mid;
    if (stage.includes("late")) return selectedCrop.kc_late;
    return (selectedCrop.kc_initial + selectedCrop.kc_mid) / 2.0;
  };

  const currentKc = getCurrentKc();
  const estimatedEtc = ((formData.et0_mm || 4.0) * currentKc).toFixed(2);

  // Options for searchable selects
  const cropOptions: SelectOption[] = crops.map((c) => ({
    value: c.name,
    label: c.name,
    category: c.category || "General",
    sublabel: `Root: ${c.root_depth_meters}m • ${c.typical_yield_season_days}d cycle`,
    badge: `Mid-Kc: ${c.kc_mid.toFixed(2)}`,
  }));

  const locationOptions: SelectOption[] = Object.entries(locations).map(([name, data]) => {
    const isKarnataka =
      data.state === "Karnataka" ||
      [
        "Bengaluru",
        "Devanahalli",
        "Mysuru",
        "Mandya",
        "Hassan",
        "Tumakuru",
        "Belagavi",
        "Hubballi",
        "Vijayapura",
        "Kalaburagi",
      ].some((k) => name.includes(k));

    return {
      value: name,
      label: name,
      category: isKarnataka ? "Karnataka" : "Other Indian States",
      sublabel: `${data.lat.toFixed(2)}°N, ${data.lon.toFixed(2)}°E`,
      badge: data.climate ? data.climate.replace(/_/g, " ") : undefined,
    };
  });

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Title */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-emerald-800 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
            Agronomic ML Engine
          </span>
          <h1 className="text-2xl font-black text-slate-900 mt-2">
            Crop Irrigation Water Prediction
          </h1>
          <p className="text-sm text-slate-600 mt-1">
            Configure plot parameters to compute precise volumetric irrigation requirement in{" "}
            <strong className="text-emerald-700">Litres</strong>, cubic meters, and depth.
          </p>
        </div>
        <button
          type="button"
          onClick={() => handleFetchWeatherForLocation(selectedLocation)}
          disabled={weatherLoading}
          className="inline-flex items-center gap-2 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-300 font-semibold px-4 py-2 rounded-xl text-xs transition-colors self-start md:self-auto shadow-sm"
        >
          <CloudSun className={`w-4 h-4 text-emerald-600 ${weatherLoading ? "animate-spin" : ""}`} />
          {weatherLoading ? "Fetching..." : `Sync Weather for ${selectedLocation}`}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded-xl text-red-800 text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0 text-red-500" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Grid: Form Left, Result Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Form Container (7 Cols) */}
        <form onSubmit={handleSubmit} className="lg:col-span-7 space-y-6">
          {/* Card 1: Crop & Land Parameters */}
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-5">
            <div className="flex items-center gap-2 text-slate-900 font-bold border-b border-slate-100 pb-3">
              <span className="w-6 h-6 rounded-lg bg-emerald-100 text-emerald-800 flex items-center justify-center text-xs font-bold">
                1
              </span>
              <h3>Crop & Farm Specifications</h3>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Crop Type - Searchable Dropdown */}
              <div>
                <SearchableSelect
                  label="Crop Variety (Searchable)"
                  options={cropOptions}
                  value={formData.crop_type}
                  onChange={(val) => handleChange("crop_type", val)}
                  placeholder="Select crop..."
                  searchPlaceholder="Search 34 crops (e.g. Ragi, Rice, Cotton, Tomato)..."
                  icon={<Sprout className="w-4 h-4" />}
                />
                {selectedCrop && (
                  <div className="flex flex-wrap items-center gap-2 mt-2 text-[11px] text-slate-700 bg-slate-50 p-2 rounded-lg border border-slate-200">
                    <span className="font-semibold text-emerald-800">
                      Category: {selectedCrop.category}
                    </span>
                    <span>•</span>
                    <span>Root: <strong>{selectedCrop.root_depth_meters}m</strong></span>
                    <span>•</span>
                    <span>Stage Kc: <strong>{currentKc.toFixed(2)}</strong></span>
                    <span>•</span>
                    <span>ETc: <strong className="text-emerald-700">{estimatedEtc} mm/d</strong></span>
                  </div>
                )}
              </div>

              {/* Growth Stage */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Growth Stage
                </label>
                <select
                  value={formData.growth_stage}
                  onChange={(e) => handleChange("growth_stage", e.target.value)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2.5 text-sm text-slate-800 font-medium focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                >
                  <option value="Initial">Initial (Establishment)</option>
                  <option value="Vegetative">Vegetative (Canopy Expansion)</option>
                  <option value="Mid-season">Mid-season (Flowering & Peak Water)</option>
                  <option value="Late">Late (Maturation & Harvest)</option>
                </select>
              </div>

              {/* Farm Area */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Farm Size Area
                </label>
                <input
                  type="number"
                  step="0.1"
                  min="0.1"
                  max="10000"
                  value={formData.area}
                  onChange={(e) => handleChange("area", parseFloat(e.target.value) || 0)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2.5 text-sm text-slate-800 font-medium focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                  required
                />
              </div>

              {/* Area Unit */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Area Measurement Unit
                </label>
                <select
                  value={formData.area_unit}
                  onChange={(e) => handleChange("area_unit", e.target.value)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2.5 text-sm text-slate-800 font-medium focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                >
                  <option value="hectares">Hectares (ha = 10,000 m²)</option>
                  <option value="acres">Acres (1 ac ≈ 4,047 m²)</option>
                  <option value="sq_meters">Square Meters (m²)</option>
                </select>
              </div>
            </div>
          </div>

          {/* Card 2: Soil Properties */}
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-5">
            <div className="flex items-center gap-2 text-slate-900 font-bold border-b border-slate-100 pb-3">
              <span className="w-6 h-6 rounded-lg bg-emerald-100 text-emerald-800 flex items-center justify-center text-xs font-bold">
                2
              </span>
              <h3>Soil & Root Zone Hydrology</h3>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Soil Type */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Soil Classification
                </label>
                <select
                  value={formData.soil_type}
                  onChange={(e) => handleChange("soil_type", e.target.value)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2.5 text-sm text-slate-800 font-medium focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                >
                  {(soils.length > 0 ? soils.map((s) => s.name) : ["Sandy", "Sandy Loam", "Loamy", "Clay Loam", "Silty", "Clay"]).map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
                {selectedSoil && (
                  <p className="text-[11px] text-slate-500 mt-1">
                    FC: {selectedSoil.field_capacity_pct}% | Wilting Point: {selectedSoil.wilting_point_pct}%
                  </p>
                )}
              </div>

              {/* Soil pH */}
              <div>
                <div className="flex justify-between items-center mb-1">
                  <label className="text-xs font-semibold text-slate-700">Soil pH</label>
                  <span className="text-xs font-bold text-emerald-800">{formData.soil_ph}</span>
                </div>
                <input
                  type="range"
                  step="0.1"
                  min="4.5"
                  max="9.0"
                  value={formData.soil_ph || 6.8}
                  onChange={(e) => handleChange("soil_ph", parseFloat(e.target.value))}
                  className="w-full accent-emerald-600 cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-slate-600">
                  <span>Acidic (4.5)</span>
                  <span>Neutral (7.0)</span>
                  <span>Alkaline (9.0)</span>
                </div>
              </div>

              {/* Soil Moisture % Slider */}
              <div className="sm:col-span-2">
                <div className="flex justify-between items-center mb-1">
                  <label className="text-xs font-semibold text-slate-700">
                    Current Root-Zone Soil Moisture
                  </label>
                  <span
                    className={`text-xs font-extrabold px-2 py-0.5 rounded-full ${
                      formData.soil_moisture_pct < 20
                        ? "bg-red-100 text-red-700"
                        : formData.soil_moisture_pct < 32
                        ? "bg-amber-100 text-amber-700"
                        : "bg-emerald-100 text-emerald-700"
                    }`}
                  >
                    {formData.soil_moisture_pct}%
                  </span>
                </div>
                <input
                  type="range"
                  step="0.5"
                  min="5"
                  max="55"
                  value={formData.soil_moisture_pct}
                  onChange={(e) => handleChange("soil_moisture_pct", parseFloat(e.target.value))}
                  className="w-full accent-emerald-600 cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-slate-600 mt-0.5 font-medium">
                  <span>Dry (&lt;18%)</span>
                  <span>Optimal (22% - 35%)</span>
                  <span>Saturated (&gt;40%)</span>
                </div>
              </div>
            </div>
          </div>

          {/* Card 3: Weather & Delivery Method */}
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-5">
            <div className="flex items-center gap-2 text-slate-900 font-bold border-b border-slate-100 pb-3">
              <span className="w-6 h-6 rounded-lg bg-emerald-100 text-emerald-800 flex items-center justify-center text-xs font-bold">
                3
              </span>
              <h3>Microclimate & Irrigation System</h3>
            </div>

            {/* Location & Live Weather Sync Section */}
            <div className="bg-emerald-50/70 p-4 rounded-xl border border-emerald-200/80 space-y-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <MapPin className="w-4 h-4 text-emerald-700" />
                  <span className="text-xs font-bold text-emerald-950 uppercase tracking-wide">
                    Indian Agro-Meteorological Region
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => handleFetchWeatherForLocation(selectedLocation)}
                  disabled={weatherLoading}
                  className="inline-flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold px-3 py-1.5 rounded-lg text-xs transition-colors self-start sm:self-auto shadow-sm disabled:opacity-50"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${weatherLoading ? "animate-spin" : ""}`} />
                  {weatherLoading ? "Syncing..." : "Sync Open-Meteo"}
                </button>
              </div>

              <SearchableSelect
                options={locationOptions}
                value={selectedLocation}
                onChange={handleLocationSelect}
                placeholder="Select Indian farming region..."
                searchPlaceholder="Search 26 locations (Karnataka & other states)..."
                icon={<MapPin className="w-4 h-4" />}
              />

              {/* Status and Diagnostics */}
              <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] pt-1">
                <div className="flex items-center gap-2">
                  <span
                    className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full font-semibold ${
                      weatherSource === "open_meteo_live"
                        ? "bg-emerald-100 text-emerald-800 border border-emerald-300"
                        : "bg-amber-100 text-amber-800 border border-amber-300"
                    }`}
                  >
                    <span
                      className={`w-1.5 h-1.5 rounded-full ${
                        weatherSource === "open_meteo_live"
                          ? "bg-emerald-500 animate-pulse"
                          : "bg-amber-500"
                      }`}
                    />
                    {weatherSource === "open_meteo_live"
                      ? "Live Open-Meteo Feed"
                      : "FAO-56 Microclimate Engine"}
                  </span>
                  <span className="text-slate-600 font-medium">
                    {selectedLocation}
                  </span>
                </div>
                <span className="text-slate-600">
                  Solar Rad: <strong>{formData.solar_radiation || 18.0} MJ/m²/d</strong>
                </span>
              </div>

              {weatherError && (
                <div className="bg-red-50 border border-red-200 text-red-700 text-xs p-2 rounded-lg flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                  <span>{weatherError}</span>
                </div>
              )}
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Temp (°C)
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={formData.temperature_c}
                  onChange={(e) => handleChange("temperature_c", parseFloat(e.target.value) || 0)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-sm text-slate-800 font-medium"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Humidity (%)
                </label>
                <input
                  type="number"
                  step="1"
                  min="10"
                  max="100"
                  value={formData.humidity_pct}
                  onChange={(e) => handleChange("humidity_pct", parseFloat(e.target.value) || 0)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-sm text-slate-800 font-medium"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Wind (km/h)
                </label>
                <input
                  type="number"
                  step="0.5"
                  min="0"
                  value={formData.wind_speed_kmh}
                  onChange={(e) => handleChange("wind_speed_kmh", parseFloat(e.target.value) || 0)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-sm text-slate-800 font-medium"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Rainfall (mm)
                </label>
                <input
                  type="number"
                  step="0.5"
                  min="0"
                  value={formData.rainfall_mm}
                  onChange={(e) => handleChange("rainfall_mm", parseFloat(e.target.value) || 0)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-sm text-slate-800 font-medium"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Ref. ET₀ (mm/d)
                </label>
                <input
                  type="number"
                  step="0.1"
                  min="0.5"
                  value={formData.et0_mm || 4.5}
                  onChange={(e) => handleChange("et0_mm", parseFloat(e.target.value) || 0)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-sm text-slate-800 font-medium"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Delivery System
                </label>
                <select
                  value={formData.irrigation_method}
                  onChange={(e) => handleChange("irrigation_method", e.target.value)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-sm text-slate-800 font-medium"
                >
                  <option value="Drip">Drip (90% eff.)</option>
                  <option value="Sprinkler">Sprinkler (75% eff.)</option>
                  <option value="Surface/Flood">Surface / Flood (60% eff.)</option>
                </select>
              </div>
            </div>

            {/* Model Architecture Selector */}
            <div className="pt-2 border-t border-slate-100">
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Machine Learning Estimator
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {[
                  { id: "xgboost", name: "XGBoost", desc: "R²=0.96" },
                  { id: "ann", name: "ANN (MLP)", desc: "R²=0.98" },
                  { id: "lstm", name: "LSTM", desc: "R²=0.99" },
                  { id: "ensemble", name: "Ensemble", desc: "Blended" },
                ].map((m) => (
                  <button
                    key={m.id}
                    type="button"
                    onClick={() => handleChange("model_name", m.id)}
                    className={`py-2 px-3 rounded-xl border text-left transition-all ${
                      formData.model_name === m.id
                        ? "bg-emerald-600 text-white border-emerald-600 shadow-sm font-semibold"
                        : "bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100"
                    }`}
                  >
                    <div className="text-xs font-bold">{m.name}</div>
                    <div className={`text-[10px] ${formData.model_name === m.id ? "text-emerald-100" : "text-slate-600"}`}>
                      {m.desc}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-extrabold py-3.5 px-6 rounded-2xl shadow-lg transition-all flex items-center justify-center gap-2 text-base disabled:opacity-50"
          >
            {loading ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Computing Agronomic & ML Prediction...</span>
              </>
            ) : (
              <>
                <Droplets className="w-5 h-5" />
                <span>Calculate Water Requirement (Litres)</span>
                <ChevronRight className="w-5 h-5" />
              </>
            )}
          </button>
        </form>

        {/* Results Container (5 Cols) */}
        <div className="lg:col-span-5 space-y-6">
          {result ? (
            <div className="space-y-6 animate-fadeIn">
              {/* Primary Headline Result Card */}
              <div className="bg-gradient-to-br from-emerald-900 via-emerald-800 to-teal-950 rounded-3xl p-6 sm:p-7 text-white shadow-xl relative overflow-hidden border border-emerald-700/50">
                <div className="flex items-center justify-between">
                  <span className="text-xs uppercase tracking-wider font-semibold text-emerald-300">
                    Estimated Requirement
                  </span>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-black uppercase tracking-wide border ${
                      result.urgency_level === "Critical"
                        ? "bg-red-500/20 text-red-300 border-red-500/40"
                        : result.urgency_level === "High"
                        ? "bg-amber-500/20 text-amber-300 border-amber-500/40"
                        : result.urgency_level === "Moderate"
                        ? "bg-blue-500/20 text-blue-300 border-blue-500/40"
                        : "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                    }`}
                  >
                    {result.urgency_level} Urgency
                  </span>
                </div>

                {/* Main Headline: Litres */}
                <div className="mt-5">
                  <div className="text-3xl sm:text-4xl font-black text-white tracking-tight flex items-baseline gap-2">
                    <span>{result.water_requirement_litres.toLocaleString()}</span>
                    <span className="text-lg font-bold text-emerald-400">Litres</span>
                  </div>
                  <p className="text-xs text-emerald-200/90 mt-1">
                    Total volume for {result.area} {result.area_unit} ({result.area_sq_meters.toLocaleString()} m²)
                  </p>
                </div>

                {/* Submetrics: m3 and mm depth */}
                <div className="grid grid-cols-2 gap-3 mt-6 pt-5 border-t border-emerald-700/60">
                  <div className="bg-emerald-950/40 p-3 rounded-xl border border-emerald-700/40">
                    <span className="text-[10px] uppercase font-bold text-emerald-300 block">
                      Volume in Cubic Metres
                    </span>
                    <span className="text-lg font-extrabold text-white">
                      {result.water_requirement_m3.toLocaleString()} m³
                    </span>
                  </div>
                  <div className="bg-emerald-950/40 p-3 rounded-xl border border-emerald-700/40">
                    <span className="text-[10px] uppercase font-bold text-emerald-300 block">
                      Gross Depth (GIR)
                    </span>
                    <span className="text-lg font-extrabold text-white">
                      {result.gross_irrigation_requirement_mm.toFixed(1)} mm
                    </span>
                  </div>
                </div>

                {/* Model Predictions Mini-Comparison */}
                {result.model_predictions && (
                  <div className="mt-4 pt-4 border-t border-emerald-700/60">
                    <span className="text-[11px] font-semibold text-emerald-300 block mb-2">
                      Multi-Model Estimates (mm depth):
                    </span>
                    <div className="grid grid-cols-3 gap-2 text-center">
                      <div className="bg-emerald-950/60 p-2 rounded-lg text-xs">
                        <span className="block text-[10px] text-emerald-400 font-bold">XGBoost</span>
                        <span className="font-extrabold text-white">
                          {result.model_predictions.xgboost ?? "-"} mm
                        </span>
                      </div>
                      <div className="bg-emerald-950/60 p-2 rounded-lg text-xs">
                        <span className="block text-[10px] text-emerald-400 font-bold">ANN</span>
                        <span className="font-extrabold text-white">
                          {result.model_predictions.ann ?? "-"} mm
                        </span>
                      </div>
                      <div className="bg-emerald-950/60 p-2 rounded-lg text-xs">
                        <span className="block text-[10px] text-emerald-400 font-bold">LSTM</span>
                        <span className="font-extrabold text-white">
                          {result.model_predictions.lstm ?? "-"} mm
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Recommended Application Schedule */}
              <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4">
                <div className="flex items-center gap-2 text-slate-900 font-bold border-b border-slate-100 pb-3">
                  <Clock className="w-5 h-5 text-emerald-600" />
                  <h4>Irrigation Schedule Advisory</h4>
                </div>

                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div className="p-3 bg-slate-50 rounded-xl">
                    <span className="text-xs text-slate-500 block">Interval Frequency</span>
                    <span className="font-extrabold text-slate-800 text-base">
                      Every {result.recommended_schedule.frequency_days} day(s)
                    </span>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-xl">
                    <span className="text-xs text-slate-500 block">Duration per Run</span>
                    <span className="font-extrabold text-slate-800 text-base">
                      {result.recommended_schedule.duration_hours} hour(s)
                    </span>
                  </div>
                </div>

                <div className="p-3 bg-emerald-50 text-emerald-900 rounded-xl text-xs space-y-1">
                  <div className="font-bold flex items-center gap-1.5">
                    <Calendar className="w-3.5 h-3.5 text-emerald-700" />
                    Best Watering Window
                  </div>
                  <p>{result.recommended_schedule.best_time}</p>
                </div>

                {/* Agronomic Recommendations */}
                <div className="space-y-2 pt-2">
                  <h5 className="text-xs font-bold text-slate-700 uppercase">Field Notes:</h5>
                  <ul className="space-y-1.5 text-xs text-slate-600">
                    {result.recommendations.map((rec, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <Check className="w-3.5 h-3.5 text-emerald-600 mt-0.5 flex-shrink-0" />
                        <span>{rec}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* SHAP Link Button */}
                {onNavigateToShap && (
                  <button
                    type="button"
                    onClick={() => onNavigateToShap(formData)}
                    className="w-full text-xs font-bold bg-slate-100 hover:bg-slate-200 text-slate-800 py-2.5 px-4 rounded-xl flex items-center justify-center gap-1.5 transition-colors"
                  >
                    <Sparkles className="w-4 h-4 text-emerald-600" />
                    Inspect SHAP Feature Importance for this run &rarr;
                  </button>
                )}
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-3xl p-8 border border-slate-200 shadow-sm text-center flex flex-col items-center justify-center min-h-[460px] text-slate-400">
              <div className="w-16 h-16 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center mb-4">
                <Droplets className="w-8 h-8" />
              </div>
              <h3 className="font-bold text-slate-800 text-base">Awaiting Plot Parameters</h3>
              <p className="text-xs text-slate-500 max-w-xs mt-1">
                Fill out the farm details on the left and click "Calculate Water Requirement" to see the
                volumetric recommendation in Litres.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
