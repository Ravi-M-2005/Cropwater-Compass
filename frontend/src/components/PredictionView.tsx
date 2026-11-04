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
  LocateFixed,
  Navigation,
  Compass,
  Database,
  Wifi,
  Sliders,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  FileText,
} from "lucide-react";
import { api } from "../services/api";
import {
  PredictionRequest,
  PredictionResponse,
  CropInfo,
  SoilInfo,
  IrrigationMethodInfo,
  WeatherData,
  SoilPropertiesResponse,
} from "../types";
import { SearchableSelect, SelectOption } from "./SearchableSelect";
import { useGeolocation } from "../hooks/useGeolocation";
import { useNetworkStatus } from "../hooks/useNetworkStatus";
import { OfflineDatasetSelector } from "./OfflineDatasetSelector";
import { OfflineDatasetRecord, OFFLINE_DATASET } from "../data/offlineDataset";
import { calculateOfflineIrrigation } from "../services/offlineIrrigationEngine";
import { DataSourceBadge } from "./DataSourceBadge";

interface PredictionViewProps {
  onNavigateToShap?: (data: PredictionRequest) => void;
}

export const PredictionView: React.FC<PredictionViewProps> = ({ onNavigateToShap }) => {
  // Network & Data Source Status
  const {
    isOnline,
    isOpenMeteoReachable,
    mode,
    offlineReason,
    switchToLive,
    switchToOffline,
    switchToManual,
  } = useNetworkStatus();

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
  const [lastWeatherUpdate, setLastWeatherUpdate] = useState<string | null>(null);
  const [weatherError, setWeatherError] = useState<string | null>(null);
  const [isGpsActive, setIsGpsActive] = useState<boolean>(false);
  const [currentCoords, setCurrentCoords] = useState<{ lat: number; lon: number } | null>(null);

  // ISRIC SoilGrids 250m State
  const [soilDepthInterval, setSoilDepthInterval] = useState<string>("0-5cm");
  const [soilGridsData, setSoilGridsData] = useState<SoilPropertiesResponse | null>(null);
  const [soilLoading, setSoilLoading] = useState<boolean>(false);
  const [showSoilDetails, setShowSoilDetails] = useState<boolean>(false);

  // Selected Offline Record
  const [selectedOfflineRecord, setSelectedOfflineRecord] = useState<OfflineDatasetRecord | null>(null);

  // Submission & Results
  const [loading, setLoading] = useState(false);
  const [weatherLoading, setWeatherLoading] = useState(false);
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // GPS Geolocation Hook
  const {
    coords: gpsCoords,
    loading: gpsLoading,
    error: gpsError,
    permissionDenied,
    detectLocation,
  } = useGeolocation(false);

  // Helper to select an offline dataset record and immediately calculate irrigation demand
  const handleSelectOfflineRecord = (rec: OfflineDatasetRecord) => {
    setSelectedOfflineRecord(rec);
    const updatedForm: PredictionRequest = {
      ...formData,
      crop_type: rec.crop_type,
      growth_stage: rec.growth_stage,
      soil_type: rec.soil_type,
      soil_moisture_pct: rec.soil_moisture_pct,
      soil_ph: rec.soil_ph,
      temperature_c: rec.temperature_c,
      humidity_pct: rec.humidity_pct,
      wind_speed_kmh: rec.wind_speed_kmh,
      rainfall_mm: rec.rainfall_mm,
      solar_radiation: rec.solar_radiation,
      et0_mm: rec.et0_mm,
      irrigation_method: rec.irrigation_method,
    };
    setFormData(updatedForm);
    setSelectedLocation(rec.location);
    setIsGpsActive(false);
    setWeatherSource("offline_dataset");
    setLastWeatherUpdate(`${rec.date} (Offline Record #${rec.id})`);

    // Automatic offline irrigation calculation
    const offlineRes = calculateOfflineIrrigation(updatedForm);
    setResult(offlineRes);
  };

  // Helper to fetch authentic ISRIC SoilGrids 250m properties
  const fetchSoilGrids = async (lat: number, lon: number, depth: string = soilDepthInterval): Promise<SoilPropertiesResponse | null> => {
    if (!navigator.onLine) return null;
    try {
      setSoilLoading(true);
      const res = await api.getSoilProperties(lat, lon, depth);
      setSoilGridsData(res);
      return res;
    } catch (sErr) {
      console.warn("SoilGrids fetch notice:", sErr);
      return null;
    } finally {
      setSoilLoading(false);
    }
  };

  const handleDepthIntervalChange = async (newDepth: string) => {
    setSoilDepthInterval(newDepth);
    setFormData((prev) => ({ ...prev, soil_depth_interval: newDepth }));
    if (currentCoords) {
      const soilRes = await fetchSoilGrids(currentCoords.lat, currentCoords.lon, newDepth);
      if (soilRes && soilRes.is_available) {
        setFormData((prev) => ({
          ...prev,
          soil_type: soilRes.cropwater_soil_type || prev.soil_type,
          sand_pct: soilRes.properties?.sand?.converted_value,
          silt_pct: soilRes.properties?.silt?.converted_value,
          clay_pct: soilRes.properties?.clay?.converted_value,
          volumetric_water_content_fc_pct: soilRes.field_capacity_pct,
          volumetric_water_content_wp_pct: soilRes.wilting_point_pct,
          awc_volumetric_pct: soilRes.available_water_capacity_mm_per_m ? soilRes.available_water_capacity_mm_per_m / 10.0 : undefined,
          soil_ph: soilRes.properties?.phh2o?.converted_value ?? prev.soil_ph,
        }));
      }
    }
  };

  // Helper to sync weather given coordinates
  const syncWeatherFromCoords = async (lat: number, lon: number, cityName?: string) => {
    try {
      setWeatherLoading(true);
      setWeatherError(null);
      setCurrentCoords({ lat, lon });

      // Run weather fetch and SoilGrids fetch in parallel
      const weatherPromise = api.getCurrentWeather(lat, lon, cityName);
      const soilPromise = fetchSoilGrids(lat, lon, soilDepthInterval);

      const [w, soilRes] = await Promise.all([weatherPromise, soilPromise]);

      setFormData((prev) => ({
        ...prev,
        latitude: lat,
        longitude: lon,
        temperature_c: w.temperature_c,
        humidity_pct: w.humidity_pct,
        wind_speed_kmh: w.wind_speed_kmh,
        rainfall_mm: w.rainfall_mm,
        solar_radiation: w.solar_radiation,
        et0_mm: w.et0_mm,
        soil_type: (soilRes && soilRes.is_available && soilRes.cropwater_soil_type) ? soilRes.cropwater_soil_type : prev.soil_type,
        sand_pct: soilRes?.properties?.sand?.converted_value,
        silt_pct: soilRes?.properties?.silt?.converted_value,
        clay_pct: soilRes?.properties?.clay?.converted_value,
        volumetric_water_content_fc_pct: soilRes?.field_capacity_pct,
        volumetric_water_content_wp_pct: soilRes?.wilting_point_pct,
        awc_volumetric_pct: soilRes?.available_water_capacity_mm_per_m ? soilRes.available_water_capacity_mm_per_m / 10.0 : undefined,
        soil_source: (soilRes && soilRes.is_available) ? "isric_soilgrids_250m" : "manual",
        soil_depth_interval: soilDepthInterval,
        soil_ph: soilRes?.properties?.phh2o?.converted_value ?? prev.soil_ph,
      }));
      setWeatherSource(w.source);
      setLastWeatherUpdate(w.last_updated || "Just now");

      // Run automatic irrigation prediction with the updated weather parameters
      const updatedReq: PredictionRequest = {
        ...formData,
        latitude: lat,
        longitude: lon,
        temperature_c: w.temperature_c,
        humidity_pct: w.humidity_pct,
        wind_speed_kmh: w.wind_speed_kmh,
        rainfall_mm: w.rainfall_mm,
        solar_radiation: w.solar_radiation,
        et0_mm: w.et0_mm,
        soil_type: (soilRes && soilRes.is_available && soilRes.cropwater_soil_type) ? soilRes.cropwater_soil_type : formData.soil_type,
        sand_pct: soilRes?.properties?.sand?.converted_value,
        silt_pct: soilRes?.properties?.silt?.converted_value,
        clay_pct: soilRes?.properties?.clay?.converted_value,
        volumetric_water_content_fc_pct: soilRes?.field_capacity_pct,
        volumetric_water_content_wp_pct: soilRes?.wilting_point_pct,
        soil_source: (soilRes && soilRes.is_available) ? "isric_soilgrids_250m" : "manual",
        soil_depth_interval: soilDepthInterval,
      };
      try {
        const predRes = await api.predict(updatedReq);
        setResult(predRes);
      } catch (pErr) {
        console.warn("Prediction recalculation error, executing offline fallback:", pErr);
        const offRes = calculateOfflineIrrigation(updatedReq);
        setResult(offRes);
      }
    } catch (err: any) {
      console.warn("Live weather fetch failed; triggering offline mode:", err);
      setWeatherError(err.message || "Failed to retrieve real-time weather from Open-Meteo.");
      switchToOffline("Open-Meteo meteorological API unreachable. Automatically switched to offline benchmark dataset.");
      const match = OFFLINE_DATASET.find((r) => r.location === cityName) || OFFLINE_DATASET[0];
      handleSelectOfflineRecord(match);
    } finally {
      setWeatherLoading(false);
    }
  };

  // Load catalogs and attempt automatic GPS detection on mount
  useEffect(() => {
    const fetchMetadataAndInitial = async () => {
      let locMap: Record<string, any> = {};
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
        locMap = locRes.locations || {};
        setLocations(locMap);
      } catch (err) {
        console.warn("Could not load initial metadata from network; using offline catalog:", err);
      }

      // If user is already offline or in OFFLINE_DATASET mode, load a default offline record
      if (!navigator.onLine || mode === "OFFLINE_DATASET") {
        const defaultRec = OFFLINE_DATASET[0];
        handleSelectOfflineRecord(defaultRec);
        return;
      }

      // Try GPS auto-detection first if online
      const detected = await detectLocation();
      if (detected) {
        setIsGpsActive(true);
        setSelectedLocation("Current Farm Location (GPS)");
        await syncWeatherFromCoords(detected.latitude, detected.longitude, "Current Farm Location (GPS)");
      } else {
        // Fallback to preset location (Bengaluru or first preset)
        setIsGpsActive(false);
        const defaultName = locMap["Bengaluru"] ? "Bengaluru" : Object.keys(locMap)[0] || "Punjab, India";
        const defaultLoc = locMap[defaultName] || { lat: 12.9716, lon: 77.5946 };
        setSelectedLocation(defaultName);
        await syncWeatherFromCoords(defaultLoc.lat, defaultLoc.lon, defaultName);
      }
    };
    fetchMetadataAndInitial();
  }, [detectLocation]);

  // When switching into OFFLINE_DATASET mode dynamically, ensure a matching record is active
  useEffect(() => {
    if (mode === "OFFLINE_DATASET" && !selectedOfflineRecord) {
      const match =
        OFFLINE_DATASET.find((r) => r.crop_type === formData.crop_type && r.location === selectedLocation) ||
        OFFLINE_DATASET.find((r) => r.crop_type === formData.crop_type) ||
        OFFLINE_DATASET.find((r) => r.location === selectedLocation) ||
        OFFLINE_DATASET[0];
      handleSelectOfflineRecord(match);
    }
  }, [mode]);

  const handleChange = (field: keyof PredictionRequest, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  // User manually triggers "Detect My Location" button
  const handleDetectGpsClick = async () => {
    if (!navigator.onLine) {
      alert("Device is currently offline. GPS live weather requires an internet connection to reach Open-Meteo. Please select an offline dataset record.");
      return;
    }
    const detected = await detectLocation();
    if (detected) {
      setIsGpsActive(true);
      setSelectedLocation("Current Farm Location (GPS)");
      await syncWeatherFromCoords(detected.latitude, detected.longitude, "Current Farm Location (GPS)");
    }
  };

  // User selects an Indian preset location
  const handleLocationSelect = (locName: string) => {
    setSelectedLocation(locName);
    setIsGpsActive(false);
    if (mode === "OFFLINE_DATASET") {
      const match = OFFLINE_DATASET.find((r) => r.location === locName) || OFFLINE_DATASET[0];
      handleSelectOfflineRecord(match);
      return;
    }
    const loc = locations[locName];
    if (loc) {
      syncWeatherFromCoords(loc.lat, loc.lon, locName);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Input Validation (Reviewer Feedback Part A)
    const validationErrors: string[] = [];
    if (!formData.crop_type) validationErrors.push("Crop variety is required.");
    if (!formData.growth_stage) validationErrors.push("Crop growth stage is required.");
    if (!formData.soil_type) validationErrors.push("Soil classification is required.");
    if (formData.area <= 0 || isNaN(formData.area)) {
      validationErrors.push("Farm area must be strictly greater than 0.");
    }
    if (formData.rainfall_mm < 0 || isNaN(formData.rainfall_mm)) {
      validationErrors.push("Rainfall cannot be negative.");
    }
    if (formData.soil_moisture_pct < 0 || formData.soil_moisture_pct > 100 || isNaN(formData.soil_moisture_pct)) {
      validationErrors.push("Soil moisture percentage must be between 0% and 100%.");
    }
    if (formData.soil_ph !== undefined && (formData.soil_ph < 3.0 || formData.soil_ph > 11.0)) {
      validationErrors.push("Soil pH must be between 3.0 and 11.0.");
    }
    if (formData.temperature_c < -20.0 || formData.temperature_c > 60.0 || isNaN(formData.temperature_c)) {
      validationErrors.push("Air temperature must be between -20°C and 60°C.");
    }
    if (formData.humidity_pct < 0 || formData.humidity_pct > 100 || isNaN(formData.humidity_pct)) {
      validationErrors.push("Relative humidity must be between 0% and 100%.");
    }
    if (formData.wind_speed_kmh < 0 || isNaN(formData.wind_speed_kmh)) {
      validationErrors.push("Wind speed cannot be negative.");
    }

    if (validationErrors.length > 0) {
      setError(`Validation Error: ${validationErrors.join(" ")}`);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const res = await api.predict(formData);
      setResult(res);
    } catch (err: any) {
      console.warn("api.predict failed; executing verified local FAO-56 irrigation engine:", err);
      const offlineRes = calculateOfflineIrrigation(formData);
      setResult(offlineRes);
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
      {/* Title & Top Action Bar */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-emerald-800 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
              Precision Water Prescription Engine
            </span>
            <DataSourceBadge />
          </div>
          <h1 className="text-2xl font-black text-slate-900 mt-2">
            Calculate Cropwater Requirement
          </h1>
          <p className="text-sm text-slate-600 mt-1">
            Automated GPS farm detection, live Open-Meteo weather parameters, verified offline dataset fallback, and FAO-56 volumetric scheduling.
          </p>
        </div>

        {/* Action Controls: GPS Quick Action & Data Source Mode Switcher */}
        <div className="flex flex-wrap items-center gap-2 self-start md:self-auto">
          {mode === "LIVE_OPEN_METEO" && (
            <button
              type="button"
              onClick={handleDetectGpsClick}
              disabled={gpsLoading || weatherLoading}
              className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all shadow-sm ${
                isGpsActive
                  ? "bg-emerald-600 text-white hover:bg-emerald-500 shadow-emerald-200"
                  : "bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-300"
              }`}
              title="Automatically detect location via browser GPS"
            >
              <LocateFixed className={`w-4 h-4 ${gpsLoading ? "animate-spin text-emerald-400" : ""}`} />
              <span>{gpsLoading ? "Acquiring GPS..." : isGpsActive ? "GPS Active" : "Detect My Location"}</span>
            </button>
          )}

          {/* Mode Switcher Toggle Pill */}
          <div className="flex items-center bg-slate-100 p-1 rounded-xl text-xs font-bold">
            <button
              type="button"
              onClick={switchToLive}
              className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
                mode === "LIVE_OPEN_METEO"
                  ? "bg-white text-emerald-800 shadow-sm"
                  : "text-slate-600 hover:text-slate-900"
              }`}
              title="Switch to Live Open-Meteo weather observations"
            >
              <Wifi className="w-3.5 h-3.5" />
              <span>Live</span>
            </button>
            <button
              type="button"
              onClick={() => switchToOffline()}
              className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
                mode === "OFFLINE_DATASET"
                  ? "bg-white text-amber-900 shadow-sm"
                  : "text-slate-600 hover:text-slate-900"
              }`}
              title="Switch to 5,000-sample verified offline benchmark dataset"
            >
              <Database className="w-3.5 h-3.5" />
              <span>Offline Dataset</span>
            </button>
            <button
              type="button"
              onClick={switchToManual}
              className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
                mode === "MANUAL_INPUT"
                  ? "bg-white text-blue-900 shadow-sm"
                  : "text-slate-600 hover:text-slate-900"
              }`}
              title="Switch to manual parameter entry"
            >
              <Sliders className="w-3.5 h-3.5" />
              <span>Manual</span>
            </button>
          </div>
        </div>
      </div>

      {/* Offline Dataset Selector when in OFFLINE_DATASET mode */}
      {mode === "OFFLINE_DATASET" && (
        <OfflineDatasetSelector
          onSelectRecord={handleSelectOfflineRecord}
          selectedRecordId={selectedOfflineRecord?.id}
          initialCrop={formData.crop_type}
          initialLocation={selectedLocation}
          initialSoil={formData.soil_type}
          onSwitchToLive={switchToLive}
          onSwitchToManual={switchToManual}
          offlineReason={offlineReason}
        />
      )}

      {/* Selected Benchmark Record Summary Bar */}
      {mode === "OFFLINE_DATASET" && selectedOfflineRecord && (
        <div className="bg-amber-50 border border-amber-300 rounded-2xl p-4 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs text-amber-950">
          <div className="flex items-start sm:items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-amber-200 text-amber-900 flex items-center justify-center font-bold flex-shrink-0">
              <Database className="w-4 h-4" />
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2 font-bold text-sm">
                <span>Active Historical Record: {selectedOfflineRecord.id}</span>
                <span className="bg-amber-200 text-amber-900 text-[11px] px-2 py-0.5 rounded-full font-mono font-medium">
                  Observed on {selectedOfflineRecord.date}
                </span>
                <span className="bg-emerald-100 text-emerald-800 text-[10px] px-2 py-0.5 rounded-md font-semibold border border-emerald-300">
                  Calculated Offline
                </span>
              </div>
              <p className="text-amber-800 text-xs mt-0.5">
                Location: <strong>{selectedOfflineRecord.location}, {selectedOfflineRecord.state}</strong> • Crop: <strong>{selectedOfflineRecord.crop_type}</strong> ({selectedOfflineRecord.growth_stage}) • Soil: <strong>{selectedOfflineRecord.soil_type}</strong> • Moisture: <strong>{selectedOfflineRecord.soil_moisture_pct}%</strong>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 self-start sm:self-auto flex-shrink-0">
            <span className="text-[11px] bg-white text-amber-900 font-bold px-3 py-1 rounded-xl border border-amber-300 shadow-xs">
              ET₀: {selectedOfflineRecord.et0_mm} mm/d
            </span>
            <span className="text-[11px] bg-white text-emerald-800 font-bold px-3 py-1 rounded-xl border border-emerald-300 shadow-xs">
              Rainfall: {selectedOfflineRecord.rainfall_mm} mm
            </span>
          </div>
        </div>
      )}

      {/* GPS Fallback / Permission Notice Banner if GPS was denied or failed */}
      {gpsError && !isGpsActive && mode === "LIVE_OPEN_METEO" && (
        <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded-xl text-blue-900 text-xs sm:text-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <Navigation className="w-4 h-4 flex-shrink-0 text-blue-600" />
            <span>
              <strong>GPS Notice:</strong> {gpsError} You can choose from the 26 Indian farming regions below or click <strong>Detect My Location</strong> to retry.
            </span>
          </div>
          <button
            type="button"
            onClick={handleDetectGpsClick}
            className="text-xs font-bold bg-blue-200 hover:bg-blue-300 text-blue-900 px-3 py-1.5 rounded-lg transition-colors self-start sm:self-auto flex-shrink-0"
          >
            Retry GPS Detection
          </button>
        </div>
      )}

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

          {/* Card 2: Soil Properties & ISRIC SoilGrids 250m */}
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-5">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2 text-slate-900 font-bold">
                <span className="w-6 h-6 rounded-lg bg-emerald-100 text-emerald-800 flex items-center justify-center text-xs font-bold">
                  2
                </span>
                <h3>Soil & ISRIC SoilGrids 250m Hydrology</h3>
              </div>

              {/* SoilGrids Live Badge & Depth Selector */}
              <div className="flex flex-wrap items-center gap-2 self-start sm:self-auto">
                <span
                  className={`text-[11px] font-bold px-2.5 py-1 rounded-full border flex items-center gap-1.5 ${
                    soilGridsData?.is_available
                      ? "bg-emerald-50 text-emerald-800 border-emerald-300"
                      : "bg-slate-100 text-slate-700 border-slate-300"
                  }`}
                >
                  <span
                    className={`w-2 h-2 rounded-full ${
                      soilGridsData?.is_available
                        ? "bg-emerald-500 animate-pulse"
                        : "bg-slate-400"
                    }`}
                  />
                  <span>
                    {soilGridsData?.is_available
                      ? "ISRIC SoilGrids 250m Active"
                      : "Manual Soil Baseline"}
                  </span>
                </span>

                {/* Depth Interval Selector */}
                <div className="flex items-center gap-1 text-xs">
                  <span className="text-[11px] text-slate-500 font-medium">Depth:</span>
                  <select
                    value={soilDepthInterval}
                    onChange={(e) => handleDepthIntervalChange(e.target.value)}
                    disabled={soilLoading}
                    className="bg-slate-50 border border-slate-300 rounded-lg px-2 py-1 text-xs text-slate-800 font-semibold focus:ring-1 focus:ring-emerald-500"
                    title="Standard ISRIC SoilGrids depth intervals"
                  >
                    <option value="0-5cm">0-5 cm (Topsoil)</option>
                    <option value="5-15cm">5-15 cm</option>
                    <option value="15-30cm">15-30 cm (Root Zone)</option>
                    <option value="30-60cm">30-60 cm (Subsoil)</option>
                    <option value="60-100cm">60-100 cm</option>
                    <option value="100-200cm">100-200 cm (Deep)</option>
                  </select>
                </div>

                {currentCoords && (
                  <button
                    type="button"
                    onClick={() => handleDepthIntervalChange(soilDepthInterval)}
                    disabled={soilLoading}
                    className="p-1 text-slate-500 hover:text-emerald-700 rounded-md transition-colors"
                    title="Refresh SoilGrids layers"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${soilLoading ? "animate-spin text-emerald-600" : ""}`} />
                  </button>
                )}
              </div>
            </div>

            {/* Derived USDA Soil Texture Triangle Classification Banner */}
            {soilGridsData?.is_available && (
              <div className="bg-emerald-50/70 border border-emerald-200 rounded-xl p-3.5 text-xs text-emerald-950 space-y-2">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1.5 font-bold">
                  <div className="flex items-center gap-2">
                    <span className="bg-emerald-200 text-emerald-900 text-[10px] font-black uppercase px-2 py-0.5 rounded-md">
                      USDA Triangle
                    </span>
                    <span className="text-sm text-emerald-900">
                      Derived Texture: <strong>{soilGridsData.derived_usda_texture}</strong>
                    </span>
                    <span className="text-slate-600 font-normal">
                      &rarr; Mapped to: <strong>{soilGridsData.cropwater_soil_type}</strong>
                    </span>
                  </div>
                  <span className="text-[11px] font-mono text-emerald-800">
                    Depth: {soilDepthInterval} • 250m Resolution
                  </span>
                </div>

                {/* Key Soil Composition & Hydrology Values */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 font-mono text-[11px]">
                  <div className="bg-white/80 p-2 rounded-lg border border-emerald-200/60">
                    <span className="text-[10px] text-slate-500 font-sans block uppercase font-bold">Clay Fraction</span>
                    <span className="font-bold text-slate-800">{soilGridsData.properties?.clay?.converted_value ?? "-"}%</span>
                    <span className="text-[9px] text-slate-400 font-sans block">(&lt; 2 µm)</span>
                  </div>
                  <div className="bg-white/80 p-2 rounded-lg border border-emerald-200/60">
                    <span className="text-[10px] text-slate-500 font-sans block uppercase font-bold">Sand Fraction</span>
                    <span className="font-bold text-slate-800">{soilGridsData.properties?.sand?.converted_value ?? "-"}%</span>
                    <span className="text-[9px] text-slate-400 font-sans block">(50–2000 µm)</span>
                  </div>
                  <div className="bg-white/80 p-2 rounded-lg border border-emerald-200/60">
                    <span className="text-[10px] text-slate-500 font-sans block uppercase font-bold">Field Capacity (FC)</span>
                    <span className="font-bold text-emerald-800">{soilGridsData.field_capacity_pct}%</span>
                    <span className="text-[9px] text-slate-400 font-sans block">33 kPa suction</span>
                  </div>
                  <div className="bg-white/80 p-2 rounded-lg border border-emerald-200/60">
                    <span className="text-[10px] text-slate-500 font-sans block uppercase font-bold">Available Water (AWC)</span>
                    <span className="font-bold text-emerald-800">{soilGridsData.available_water_capacity_mm_per_m} mm/m</span>
                    <span className="text-[9px] text-slate-400 font-sans block">FC - PWP balance</span>
                  </div>
                </div>

                {/* Toggle for 13 SoilGrids Properties Table */}
                <div className="pt-1 flex items-center justify-between">
                  <button
                    type="button"
                    onClick={() => setShowSoilDetails(!showSoilDetails)}
                    className="text-[11px] font-bold text-emerald-800 hover:text-emerald-950 flex items-center gap-1 transition-colors"
                  >
                    <span>{showSoilDetails ? "Hide Detailed SoilGrids Layers" : "View All 13 SoilGrids Physical Properties & Units"}</span>
                    {showSoilDetails ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                  </button>
                  <span className="text-[10px] text-slate-500 italic">
                    ISRIC SoilGrids 2.0 (CC BY 4.0)
                  </span>
                </div>

                {showSoilDetails && (
                  <div className="mt-2 pt-2 border-t border-emerald-200/80 overflow-x-auto animate-fadeIn">
                    <table className="w-full text-left text-[11px] border-collapse">
                      <thead>
                        <tr className="border-b border-emerald-200 text-slate-600 font-bold">
                          <th className="py-1 px-2">Layer / Property</th>
                          <th className="py-1 px-2">Raw Value (ISRIC)</th>
                          <th className="py-1 px-2">Converted Standard</th>
                          <th className="py-1 px-2">Description</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-emerald-100 font-mono text-slate-800">
                        {Object.entries(soilGridsData.properties).map(([propKey, propItem]: [string, any]) => (
                          <tr key={propKey} className="hover:bg-white/60">
                            <td className="py-1 px-2 font-sans font-semibold text-slate-900">{propItem.display_name}</td>
                            <td className="py-1 px-2 text-slate-600">{propItem.raw_value} {propItem.raw_units}</td>
                            <td className="py-1 px-2 font-bold text-emerald-900">{propItem.converted_value} {propItem.target_units}</td>
                            <td className="py-1 px-2 font-sans text-[10px] text-slate-500">{propItem.description}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

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
                  {soils.map((s) => (
                    <option key={s.name} value={s.name}>
                      {s.name} (AWC: {s.available_water_capacity_mm_per_m} mm/m)
                    </option>
                  ))}
                </select>
                {selectedSoil && (
                  <p className="text-[11px] text-slate-500 mt-1.5 italic">
                    {selectedSoil.description}
                  </p>
                )}
              </div>

              {/* Soil pH Slider */}
              <div>
                <div className="flex justify-between items-center mb-1">
                  <label className="text-xs font-semibold text-slate-700">Soil pH</label>
                  <span className="text-xs font-bold text-slate-800 bg-slate-100 px-2 py-0.5 rounded">
                    {formData.soil_ph || 6.8}
                  </span>
                </div>
                <input
                  type="range"
                  step="0.1"
                  min="3.0"
                  max="11.0"
                  value={formData.soil_ph || 6.8}
                  onChange={(e) => handleChange("soil_ph", parseFloat(e.target.value))}
                  className="w-full accent-emerald-600 cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-slate-600">
                  <span>Acidic (3.0)</span>
                  <span>Neutral (7.0)</span>
                  <span>Alkaline (11.0)</span>
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
                  min="0"
                  max="100"
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

            {/* Location & Microclimate Data Section */}
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <MapPin className={`w-4 h-4 ${isGpsActive ? "text-emerald-600" : mode === "OFFLINE_DATASET" ? "text-amber-600" : "text-emerald-700"}`} />
                  <span className="text-xs font-bold text-slate-900 uppercase tracking-wide">
                    {mode === "LIVE_OPEN_METEO"
                      ? isGpsActive
                        ? "Live Farm GPS Location"
                        : "Indian Agro-Meteorological Region"
                      : mode === "OFFLINE_DATASET"
                      ? "Offline Historical Meteorological Record"
                      : "Manual Farm Microclimate Parameters"}
                  </span>
                </div>

                {mode === "LIVE_OPEN_METEO" && (
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={handleDetectGpsClick}
                      disabled={gpsLoading || weatherLoading}
                      className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all shadow-sm ${
                        isGpsActive
                          ? "bg-emerald-600 text-white hover:bg-emerald-700"
                          : "bg-emerald-100 hover:bg-emerald-200 text-emerald-800"
                      }`}
                    >
                      <LocateFixed className={`w-3.5 h-3.5 ${gpsLoading ? "animate-spin" : ""}`} />
                      <span>{gpsLoading ? "Detecting GPS..." : isGpsActive ? "GPS Active" : "Detect Location"}</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => {
                        if (currentCoords) {
                          syncWeatherFromCoords(currentCoords.lat, currentCoords.lon, selectedLocation);
                        } else {
                          const loc = locations[selectedLocation];
                          if (loc) syncWeatherFromCoords(loc.lat, loc.lon, selectedLocation);
                        }
                      }}
                      disabled={weatherLoading}
                      className="inline-flex items-center gap-1.5 bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold px-2.5 py-1.5 rounded-lg text-xs transition-colors shadow-sm disabled:opacity-50"
                      title="Refresh Open-Meteo weather parameters"
                    >
                      <RefreshCw className={`w-3.5 h-3.5 ${weatherLoading ? "animate-spin" : ""}`} />
                      <span>{weatherLoading ? "Syncing..." : "Sync Weather"}</span>
                    </button>
                  </div>
                )}
              </div>

              {/* Searchable Select for Preset Locations when in LIVE mode */}
              {mode === "LIVE_OPEN_METEO" && (
                <div>
                  <SearchableSelect
                    options={locationOptions}
                    value={isGpsActive ? "" : selectedLocation}
                    onChange={handleLocationSelect}
                    placeholder={isGpsActive ? "Using Device GPS (or switch to manual preset)" : "Select Indian farming region..."}
                    searchPlaceholder="Search 26 locations (Karnataka & other states)..."
                    icon={<MapPin className="w-4 h-4" />}
                  />
                </div>
              )}

              {/* Status and Diagnostics */}
              <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] pt-1">
                <div className="flex items-center gap-2">
                  <span
                    className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full font-semibold ${
                      mode === "LIVE_OPEN_METEO"
                        ? "bg-emerald-100 text-emerald-800 border border-emerald-300"
                        : mode === "OFFLINE_DATASET"
                        ? "bg-amber-100 text-amber-800 border border-amber-300"
                        : "bg-blue-100 text-blue-800 border border-blue-300"
                    }`}
                  >
                    <span
                      className={`w-1.5 h-1.5 rounded-full ${
                        mode === "LIVE_OPEN_METEO"
                          ? "bg-emerald-500 animate-pulse"
                          : mode === "OFFLINE_DATASET"
                          ? "bg-amber-500"
                          : "bg-blue-500"
                      }`}
                    />
                    {mode === "LIVE_OPEN_METEO"
                      ? "LIVE OPEN-METEO"
                      : mode === "OFFLINE_DATASET"
                      ? `OFFLINE DATASET (${selectedOfflineRecord?.id || "5,000 Records"})`
                      : "MANUAL INPUT"}
                  </span>

                  {mode === "LIVE_OPEN_METEO" && currentCoords && (
                    <span className="font-mono text-slate-700 bg-white px-2 py-0.5 rounded border border-slate-200">
                      {currentCoords.lat.toFixed(4)}°N, {currentCoords.lon.toFixed(4)}°E
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-2 text-slate-600">
                  {lastWeatherUpdate && (
                    <span>
                      Observed: <strong>{lastWeatherUpdate}</strong>
                    </span>
                  )}
                  <span>•</span>
                  <span>
                    Solar Rad: <strong>{formData.solar_radiation || 18.0} MJ/m²/d</strong>
                  </span>
                </div>
              </div>

              {weatherError && mode === "LIVE_OPEN_METEO" && (
                <div className="bg-red-50 border border-red-200 text-red-700 text-xs p-2 rounded-lg flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                  <span>{weatherError}</span>
                </div>
              )}
            </div>

            {/* Weather Numeric Parameters */}
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
                  min="5"
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
                  step="0.1"
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
                  { id: "xgboost", name: "XGBoost", desc: "R²=0.93" },
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
                  <div className="flex items-center gap-2">
                    <span className="text-xs uppercase tracking-wider font-semibold text-emerald-300">
                      Estimated Requirement
                    </span>
                    <span className="text-[10px] bg-emerald-950/80 text-emerald-300 px-2 py-0.5 rounded-md border border-emerald-700/60 font-medium">
                      {mode === "OFFLINE_DATASET" ? "Offline FAO-56 Engine" : "Hybrid ML + FAO-56"}
                    </span>
                  </div>
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

                {/* Soil Profile & Texture Calibration Tag */}
                <div className="mt-4 pt-3 border-t border-emerald-700/60 flex flex-wrap items-center justify-between text-xs text-emerald-200/90 gap-2">
                  <div className="flex items-center gap-1.5">
                    <Layers className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Soil: <strong>{result.usda_soil_texture ? `USDA ${result.usda_soil_texture}` : result.soil_type}</strong></span>
                    {result.soil_depth_interval && (
                      <span className="text-[10px] bg-emerald-950/80 px-2 py-0.5 rounded text-emerald-300 font-mono">
                        {result.soil_depth_interval}
                      </span>
                    )}
                  </div>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                    result.soil_source === "isric_soilgrids_250m"
                      ? "bg-emerald-500/30 text-emerald-200 border border-emerald-400/50"
                      : "bg-emerald-950/70 text-emerald-300 border border-emerald-700/50"
                  }`}>
                    {result.soil_source === "isric_soilgrids_250m" ? "ISRIC SoilGrids 250m Calibrated" : "Manual Soil Baseline"}
                  </span>
                </div>

                {/* Model Predictions Mini-Comparison (Cloud ML Inference when connected) */}
                {result.model_predictions && Object.keys(result.model_predictions).length > 0 ? (
                  <div className="mt-4 pt-4 border-t border-emerald-700/60">
                    <span className="text-[11px] font-semibold text-emerald-300 block mb-2">
                      Cloud ML Multi-Model Estimates (mm depth):
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
                ) : (
                  <div className="mt-4 pt-3 border-t border-emerald-700/60 text-[11px] text-emerald-200/90 flex items-start gap-2 bg-emerald-950/40 p-2.5 rounded-xl border border-emerald-700/40">
                    <Info className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <span className="font-bold text-white block">Deterministic FAO-56 Agronomic Balance</span>
                      <span>
                        Trained ML neural models (XGBoost, ANN, LSTM) run on the cloud backend. When in offline dataset mode, irrigation requirements are calculated deterministically via standard FAO-56 Penman-Monteith physics equations.
                      </span>
                    </div>
                  </div>
                )}
              </div>

              {/* Comprehensive Agronomic Balance Breakdown */}
              <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4">
                <div className="flex items-center gap-2 text-slate-900 font-bold border-b border-slate-100 pb-3">
                  <Compass className="w-5 h-5 text-emerald-600" />
                  <h4>FAO-56 Agronomic Water Balance</h4>
                </div>

                <div className="grid grid-cols-2 gap-2.5 text-xs">
                  <div className="p-2.5 bg-slate-50 rounded-xl border border-slate-100">
                    <span className="text-[10px] uppercase font-bold text-slate-500 block">1. Reference ET₀</span>
                    <span className="font-extrabold text-slate-800 text-sm">{result.reference_et0_mm.toFixed(2)} mm/d</span>
                    <span className="text-[10px] text-slate-500 block">Penman-Monteith</span>
                  </div>

                  <div className="p-2.5 bg-slate-50 rounded-xl border border-slate-100">
                    <span className="text-[10px] uppercase font-bold text-slate-500 block">2. Crop ETc (ET₀ × Kc)</span>
                    <span className="font-extrabold text-emerald-700 text-sm">{result.crop_evapotranspiration_etc_mm.toFixed(2)} mm/d</span>
                    <span className="text-[10px] text-slate-500 block">Kc = {result.crop_kc.toFixed(2)}</span>
                  </div>

                  <div className="p-2.5 bg-slate-50 rounded-xl border border-slate-100">
                    <span className="text-[10px] uppercase font-bold text-slate-500 block">3. Effective Rainfall</span>
                    <span className="font-extrabold text-slate-800 text-sm">{result.effective_rainfall_mm.toFixed(1)} mm</span>
                    <span className="text-[10px] text-slate-500 block">USDA-SCS Formula</span>
                  </div>

                  <div className="p-2.5 bg-slate-50 rounded-xl border border-slate-100">
                    <span className="text-[10px] uppercase font-bold text-slate-500 block">4. Net Req. (NIR)</span>
                    <span className="font-extrabold text-slate-800 text-sm">{result.net_irrigation_requirement_mm.toFixed(1)} mm</span>
                    <span className="text-[10px] text-slate-500 block">Depletion Deficit</span>
                  </div>

                  <div className="p-2.5 bg-emerald-50/70 rounded-xl border border-emerald-200 col-span-2 flex items-center justify-between">
                    <div>
                      <span className="text-[10px] uppercase font-bold text-emerald-900 block">
                        5. Gross Req. (GIR) = NIR ÷ Efficiency
                      </span>
                      <span className="text-xs text-emerald-800">
                        Method Efficiency: <strong>{result.irrigation_efficiency_pct}%</strong> ({formData.irrigation_method})
                      </span>
                    </div>
                    <span className="font-black text-emerald-800 text-base">
                      {result.gross_irrigation_requirement_mm.toFixed(1)} mm
                    </span>
                  </div>
                </div>
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
                Fill out the farm details on the left or select an offline benchmark record to view the
                volumetric recommendation in Litres.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
