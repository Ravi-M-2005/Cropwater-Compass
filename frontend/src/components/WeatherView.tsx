import React, { useState, useEffect } from "react";
import {
  CloudSun,
  Thermometer,
  Droplets,
  Wind,
  CloudRain,
  Sun,
  MapPin,
  RefreshCw,
  Calendar,
  Layers,
  ArrowUpRight,
  AlertTriangle,
  LocateFixed,
  Navigation,
  Clock,
  Compass,
  CheckCircle2,
  Database,
  Sliders,
  Wifi,
  WifiOff,
} from "lucide-react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { api } from "../services/api";
import { WeatherData, DailyForecast, HourlyForecast } from "../types";
import { SearchableSelect, SelectOption } from "./SearchableSelect";
import { useGeolocation } from "../hooks/useGeolocation";
import { useNetworkStatus } from "../hooks/useNetworkStatus";
import { OfflineDatasetSelector } from "./OfflineDatasetSelector";
import { OfflineDatasetRecord, OFFLINE_DATASET } from "../data/offlineDataset";
import { DataSourceBadge } from "./DataSourceBadge";

export const WeatherView: React.FC = () => {
  const { isOnline, isOpenMeteoReachable, mode, offlineReason, switchToLive, switchToOffline, switchToManual } = useNetworkStatus();

  const [weather, setWeather] = useState<WeatherData | null>(null);
  const [locations, setLocations] = useState<Record<string, any>>({});
  const [selectedLocation, setSelectedLocation] = useState<string>("Bengaluru");
  const [isGpsActive, setIsGpsActive] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeForecastTab, setActiveForecastTab] = useState<"daily" | "hourly">("daily");
  const [selectedOfflineRecord, setSelectedOfflineRecord] = useState<OfflineDatasetRecord | null>(null);

  // Coordinates
  const [lat, setLat] = useState<number>(12.9716);
  const [lon, setLon] = useState<number>(77.5946);

  // GPS hook
  const {
    coords: gpsCoords,
    loading: gpsLoading,
    error: gpsError,
    detectLocation,
  } = useGeolocation(false);

  const fetchWeather = async (latitude: number, longitude: number, city?: string) => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getCurrentWeather(latitude, longitude, city);
      setWeather(data);
      setLat(latitude);
      setLon(longitude);
    } catch (err: any) {
      console.warn("Open-Meteo live API failed or unreachable:", err);
      // Auto-fallback to offline dataset mode
      switchToOffline("Open-Meteo meteorological API unreachable. Switched to verified offline benchmark dataset.");
      loadDefaultOfflineRecord();
    } finally {
      setLoading(false);
    }
  };

  const loadDefaultOfflineRecord = () => {
    const defaultRec = OFFLINE_DATASET.find((r) => r.location === "Bengaluru") || OFFLINE_DATASET[0];
    applyOfflineRecord(defaultRec);
  };

  const applyOfflineRecord = (rec: OfflineDatasetRecord) => {
    setSelectedOfflineRecord(rec);
    setWeather({
      temperature_c: rec.temperature_c,
      humidity_pct: rec.humidity_pct,
      wind_speed_kmh: rec.wind_speed_kmh,
      rainfall_mm: rec.rainfall_mm,
      solar_radiation: rec.solar_radiation,
      et0_mm: rec.et0_mm,
      weather_condition: rec.rainfall_mm > 5 ? "Moderate Rain" : rec.rainfall_mm > 0 ? "Light Showers" : "Sunny / Clear",
      city: `${rec.location}, ${rec.state} (Offline Record ${rec.id})`,
      latitude: lat,
      longitude: lon,
      forecast_daily: [],
      forecast_hourly: [],
      source: "offline_dataset",
      last_updated: `${rec.date} (Historical Observation)`,
      is_gps: false,
    });
    setSelectedLocation(rec.location);
    setIsGpsActive(false);
  };

  // Initial load
  useEffect(() => {
    const init = async () => {
      let locMap: Record<string, any> = {};
      try {
        const locRes = await api.getPresetLocations();
        locMap = locRes.locations || {};
        setLocations(locMap);
      } catch (err) {
        console.warn("Could not load preset locations:", err);
      }

      // If user is already offline or Open-Meteo is known unreachable, load offline record directly
      if (!navigator.onLine || mode === "OFFLINE_DATASET") {
        loadDefaultOfflineRecord();
        setLoading(false);
        return;
      }

      // Try automatic GPS detection
      const detected = await detectLocation();
      if (detected) {
        setIsGpsActive(true);
        setSelectedLocation("Current Farm Location (GPS)");
        await fetchWeather(detected.latitude, detected.longitude, "Current Farm Location (GPS)");
      } else {
        setIsGpsActive(false);
        const defaultName = locMap["Bengaluru"] ? "Bengaluru" : Object.keys(locMap)[0] || "Punjab, India";
        const defaultLoc = locMap[defaultName] || { lat: 12.9716, lon: 77.5946 };
        setSelectedLocation(defaultName);
        await fetchWeather(defaultLoc.lat, defaultLoc.lon, defaultName);
      }
    };
    init();
  }, [detectLocation]);

  // When switching into OFFLINE_DATASET mode dynamically, ensure an offline record is loaded
  useEffect(() => {
    if (mode === "OFFLINE_DATASET" && !selectedOfflineRecord) {
      const match =
        OFFLINE_DATASET.find((r) => r.location === selectedLocation) ||
        OFFLINE_DATASET[0];
      applyOfflineRecord(match);
    }
  }, [mode]);

  // Handle manual "Detect My Location" button click
  const handleDetectLocationClick = async () => {
    if (!navigator.onLine) {
      alert("Device is offline. GPS live weather requires an internet connection to reach Open-Meteo. Please select an offline dataset record.");
      return;
    }
    const detected = await detectLocation();
    if (detected) {
      setIsGpsActive(true);
      setSelectedLocation("Current Farm Location (GPS)");
      await fetchWeather(detected.latitude, detected.longitude, "Current Farm Location (GPS)");
    }
  };

  // Handle selection from 26 preset Indian locations
  const handleLocationChange = (name: string) => {
    setSelectedLocation(name);
    setIsGpsActive(false);
    const loc = locations[name];
    if (loc) {
      if (mode === "OFFLINE_DATASET") {
        const match = OFFLINE_DATASET.find((r) => r.location === name) || OFFLINE_DATASET[0];
        applyOfflineRecord(match);
      } else {
        fetchWeather(loc.lat, loc.lon, name);
      }
    }
  };

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

  // Format hourly chart data
  const hourlyChartData = (weather?.forecast_hourly || []).map((h) => {
    const timeLabel = h.time.includes("T") ? h.time.split("T")[1].substring(0, 5) : h.time.slice(-5);
    return {
      time: timeLabel,
      temp: h.temp_c,
      humidity: h.humidity_pct,
      et0: h.et0_mm,
      precip_prob: h.precipitation_probability || 0,
    };
  });

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header with Mode Switcher & Location Select */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-teal-800 bg-teal-50 px-2.5 py-1 rounded-full border border-teal-200">
              FAO-56 Microclimate Intelligence
            </span>
            <DataSourceBadge />
          </div>

          <h1 className="text-2xl font-black text-slate-900 mt-2">
            Weather & Reference Evapotranspiration (ET₀)
          </h1>
          <p className="text-sm text-slate-600 mt-1">
            Atmospheric parameters and Penman-Monteith evaporative demand with automatic offline fallback.
          </p>
        </div>

        {/* Action Controls: GPS Detect & Manual Dropdown */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2.5 self-start md:self-auto w-full md:w-auto">
          {mode === "LIVE_OPEN_METEO" && (
            <button
              type="button"
              onClick={handleDetectLocationClick}
              disabled={gpsLoading}
              className={`inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all shadow-sm flex-shrink-0 ${
                isGpsActive
                  ? "bg-emerald-600 text-white hover:bg-emerald-500 shadow-emerald-200"
                  : "bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-300"
              }`}
              title="Automatically detect current farm location using device GPS"
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
              className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1 ${
                mode === "LIVE_OPEN_METEO"
                  ? "bg-white text-emerald-800 shadow-sm"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <Wifi className="w-3.5 h-3.5" />
              Live
            </button>
            <button
              type="button"
              onClick={() => switchToOffline()}
              className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1 ${
                mode === "OFFLINE_DATASET"
                  ? "bg-white text-amber-900 shadow-sm"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <Database className="w-3.5 h-3.5" />
              Offline Dataset
            </button>
          </div>

          {/* Fallback Searchable Select for 26 Indian Locations */}
          <div className="w-full sm:w-60">
            <SearchableSelect
              options={locationOptions}
              value={isGpsActive ? "" : selectedLocation}
              onChange={handleLocationChange}
              placeholder={isGpsActive ? "Using Device GPS" : "Select location..."}
              searchPlaceholder="Search 26 Indian locations..."
              icon={<MapPin className="w-4 h-4" />}
            />
          </div>

          {/* Refresh Button */}
          {mode === "LIVE_OPEN_METEO" && (
            <button
              onClick={() => fetchWeather(lat, lon, selectedLocation)}
              className="p-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors shadow-sm flex-shrink-0 self-end sm:self-auto"
              title="Refresh weather data"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-emerald-600" : ""}`} />
            </button>
          )}
        </div>
      </div>

      {/* Offline Mode Active Banner & Selector */}
      {mode === "OFFLINE_DATASET" && (
        <OfflineDatasetSelector
          onSelectRecord={applyOfflineRecord}
          selectedRecordId={selectedOfflineRecord?.id}
          initialLocation={selectedLocation}
          onSwitchToLive={switchToLive}
          onSwitchToManual={switchToManual}
          offlineReason={offlineReason}
        />
      )}

      {/* GPS Fallback / Permission Notice Banner if GPS was denied or failed */}
      {gpsError && !isGpsActive && mode === "LIVE_OPEN_METEO" && (
        <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded-xl text-blue-900 text-xs sm:text-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <Navigation className="w-4 h-4 flex-shrink-0 text-blue-600" />
            <span>
              <strong>GPS Notice:</strong> {gpsError} You can choose from the 26 Indian farming regions above or click <strong>Detect My Location</strong> to retry.
            </span>
          </div>
          <button
            type="button"
            onClick={handleDetectLocationClick}
            className="text-xs font-bold bg-blue-200 hover:bg-blue-300 text-blue-900 px-3 py-1.5 rounded-lg transition-colors self-start sm:self-auto flex-shrink-0"
          >
            Retry GPS Detection
          </button>
        </div>
      )}

      {/* Error Banner */}
      {error && mode === "LIVE_OPEN_METEO" && (
        <div className="bg-amber-50 border-l-4 border-amber-500 p-4 rounded-xl text-amber-900 text-sm flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 flex-shrink-0 text-amber-600" />
            <span>{error}</span>
          </div>
          <button
            onClick={() => fetchWeather(lat, lon, selectedLocation)}
            className="text-xs font-semibold bg-amber-200 hover:bg-amber-300 px-3 py-1 rounded-lg text-amber-900"
          >
            Retry
          </button>
        </div>
      )}

      {/* Location Metadata Bar: Coordinates, Live Source, and Last Updated */}
      <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm flex flex-wrap items-center justify-between gap-4 text-xs">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2 font-bold text-slate-800 text-sm">
            <MapPin className={`w-4 h-4 ${isGpsActive ? "text-emerald-600 animate-pulse" : mode === "OFFLINE_DATASET" ? "text-amber-600" : "text-slate-500"}`} />
            <span>{weather?.city || selectedLocation}</span>
          </div>

          <span className="text-slate-500 bg-slate-100 px-2.5 py-1 rounded-lg font-mono font-medium">
            {lat.toFixed(4)}°N, {lon.toFixed(4)}°E
          </span>

          {mode === "LIVE_OPEN_METEO" && isGpsActive && (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-extrabold bg-emerald-100 text-emerald-800 border border-emerald-300">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-ping" />
              Live Device GPS
            </span>
          )}

          {mode === "OFFLINE_DATASET" && (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-extrabold bg-amber-100 text-amber-900 border border-amber-300">
              <Database className="w-3 h-3 text-amber-700" />
              Offline Dataset Record {selectedOfflineRecord ? `(${selectedOfflineRecord.id})` : ""}
            </span>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Observation Date or Last Updated */}
          <div className="flex items-center gap-1.5 text-slate-500">
            <Clock className="w-3.5 h-3.5 text-slate-400" />
            <span>
              {mode === "OFFLINE_DATASET" ? "Observation Date: " : "Updated: "}
              <strong className="text-slate-800">{weather?.last_updated || "Just now"}</strong>
            </span>
          </div>

          {/* Data Source Badge */}
          <span
            className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-bold ${
              mode === "OFFLINE_DATASET"
                ? "bg-amber-100 text-amber-900 border border-amber-300"
                : weather?.source === "open_meteo_live"
                ? "bg-emerald-50 text-emerald-800 border border-emerald-300"
                : "bg-slate-100 text-slate-800 border border-slate-300"
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                mode === "OFFLINE_DATASET"
                  ? "bg-amber-500"
                  : weather?.source === "open_meteo_live"
                  ? "bg-emerald-500 animate-pulse"
                  : "bg-slate-400"
              }`}
            />
            {mode === "OFFLINE_DATASET"
              ? "OFFLINE DATASET (Historical)"
              : weather?.source === "open_meteo_live"
              ? "LIVE OPEN-METEO"
              : "FAO-56 Physical Simulator"}
          </span>
        </div>
      </div>

      {/* Main Meteorological Cards (6 Parameters) */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        {/* ET0 */}
        <div className={`rounded-2xl p-4 shadow-sm border ${
          mode === "OFFLINE_DATASET"
            ? "bg-gradient-to-br from-amber-900 via-amber-800 to-amber-950 text-white border-amber-700"
            : "bg-gradient-to-br from-emerald-900 via-emerald-800 to-teal-950 text-white border-emerald-700"
        }`}>
          <div className="flex justify-between items-center text-amber-200">
            <span className="text-xs font-bold uppercase tracking-wide">Reference ET₀</span>
            <Sun className="w-4 h-4" />
          </div>
          <div className="text-2xl font-black mt-2">
            {weather?.et0_mm ?? 4.5}{" "}
            <span className="text-xs font-normal text-emerald-200">mm/d</span>
          </div>
          <span className="text-[10px] text-amber-200 block mt-1 font-medium">
            Penman-Monteith
          </span>
        </div>

        {/* Temperature */}
        <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm">
          <div className="flex justify-between items-center text-slate-500">
            <span className="text-xs font-bold uppercase">Air Temp</span>
            <Thermometer className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-2xl font-black text-slate-900 mt-2">
            {weather?.temperature_c ?? 28}°C
          </div>
          <span className="text-[10px] text-slate-500 block mt-1">2m Standard Height</span>
        </div>

        {/* Humidity */}
        <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm">
          <div className="flex justify-between items-center text-slate-500">
            <span className="text-xs font-bold uppercase">Humidity</span>
            <Droplets className="w-4 h-4 text-blue-500" />
          </div>
          <div className="text-2xl font-black text-slate-900 mt-2">
            {weather?.humidity_pct ?? 50}%
          </div>
          <span className="text-[10px] text-slate-500 block mt-1">Relative Humidity</span>
        </div>

        {/* Wind Speed */}
        <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm">
          <div className="flex justify-between items-center text-slate-500">
            <span className="text-xs font-bold uppercase">Wind Velocity</span>
            <Wind className="w-4 h-4 text-teal-500" />
          </div>
          <div className="text-2xl font-black text-slate-900 mt-2">
            {weather?.wind_speed_kmh ?? 11}{" "}
            <span className="text-xs font-normal text-slate-500">km/h</span>
          </div>
          <span className="text-[10px] text-slate-500 block mt-1">
            {((weather?.wind_speed_kmh ?? 11) * 0.2778).toFixed(1)} m/s (10m Height)
          </span>
        </div>

        {/* Precipitation */}
        <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm">
          <div className="flex justify-between items-center text-slate-500">
            <span className="text-xs font-bold uppercase">Precipitation</span>
            <CloudRain className="w-4 h-4 text-indigo-500" />
          </div>
          <div className="text-2xl font-black text-slate-900 mt-2">
            {weather?.rainfall_mm ?? 0}{" "}
            <span className="text-xs font-normal text-slate-500">mm</span>
          </div>
          <span className="text-[10px] text-slate-500 block mt-1">
            {mode === "OFFLINE_DATASET" ? "Recorded in Dataset" : "Daily Recorded Rain"}
          </span>
        </div>

        {/* Solar Radiation */}
        <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm">
          <div className="flex justify-between items-center text-slate-500">
            <span className="text-xs font-bold uppercase">Solar Rad.</span>
            <Sun className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-2xl font-black text-slate-900 mt-2">
            {weather?.solar_radiation ?? 19}{" "}
            <span className="text-xs font-normal text-slate-500">MJ/m²</span>
          </div>
          <span className="text-[10px] text-slate-500 block mt-1">Shortwave Incident Sum</span>
        </div>
      </div>

      {/* Forecast Container with Tabs: 7-Day Daily vs 24-Hour Hourly */}
      {mode === "LIVE_OPEN_METEO" && (
        <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
            <div>
              <h2 className="font-bold text-slate-900 text-base">
                Agricultural Forecast & ET₀ Projections
              </h2>
              <p className="text-xs text-slate-600">
                High-resolution meteorological trajectories calculated for {weather?.city || selectedLocation}
              </p>
            </div>

            {/* Toggle Daily / Hourly */}
            <div className="flex items-center gap-1.5 bg-slate-100 p-1 rounded-xl self-start sm:self-auto">
              <button
                type="button"
                onClick={() => setActiveForecastTab("daily")}
                className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-all ${
                  activeForecastTab === "daily"
                    ? "bg-white text-emerald-800 shadow-sm"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                7-Day Daily Trend
              </button>
              <button
                type="button"
                onClick={() => setActiveForecastTab("hourly")}
                className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-all ${
                  activeForecastTab === "hourly"
                    ? "bg-white text-emerald-800 shadow-sm"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                24-Hour Diurnal Cycle
              </button>
            </div>
          </div>

          {/* Tab 1: 7-Day Trend Chart */}
          {activeForecastTab === "daily" && (
            <div className="h-72 w-full animate-fadeIn">
              {weather?.forecast_daily && weather.forecast_daily.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={weather.forecast_daily} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                    <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#64748b" }} />
                    <YAxis yAxisId="temp" orientation="left" tick={{ fontSize: 11, fill: "#64748b" }} unit="°C" />
                    <YAxis yAxisId="et0" orientation="right" tick={{ fontSize: 11, fill: "#059669" }} unit=" mm" />
                    <Tooltip contentStyle={{ borderRadius: "12px", border: "1px solid #e2e8f0" }} />
                    <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: "12px" }} />
                    <Line
                      yAxisId="temp"
                      type="monotone"
                      dataKey="temp_max_c"
                      name="Max Temp (°C)"
                      stroke="#ef4444"
                      strokeWidth={2}
                      dot={{ r: 3 }}
                    />
                    <Line
                      yAxisId="temp"
                      type="monotone"
                      dataKey="temp_min_c"
                      name="Min Temp (°C)"
                      stroke="#3b82f6"
                      strokeWidth={2}
                      dot={{ r: 3 }}
                    />
                    <Line
                      yAxisId="et0"
                      type="monotone"
                      dataKey="et0_mm"
                      name="Ref. ET0 (mm/day)"
                      stroke="#059669"
                      strokeWidth={3}
                      dot={{ r: 4 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-slate-400 text-sm">
                  Daily forecast data unavailable
                </div>
              )}
            </div>
          )}

          {/* Tab 2: 24-Hour Hourly Forecast Chart */}
          {activeForecastTab === "hourly" && (
            <div className="h-72 w-full animate-fadeIn">
              {hourlyChartData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={hourlyChartData} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                    <XAxis dataKey="time" tick={{ fontSize: 10, fill: "#64748b" }} />
                    <YAxis yAxisId="temp" orientation="left" tick={{ fontSize: 11, fill: "#64748b" }} unit="°C" />
                    <YAxis yAxisId="et0" orientation="right" tick={{ fontSize: 11, fill: "#059669" }} unit=" mm" />
                    <Tooltip contentStyle={{ borderRadius: "12px", border: "1px solid #e2e8f0" }} />
                    <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: "12px" }} />
                    <Bar
                      yAxisId="temp"
                      dataKey="temp"
                      name="Hourly Temp (°C)"
                      fill="#f59e0b"
                      radius={[4, 4, 0, 0]}
                    />
                    <Line
                      yAxisId="et0"
                      type="monotone"
                      dataKey="et0"
                      name="Hourly ET0 (mm/h)"
                      stroke="#059669"
                      strokeWidth={2}
                      dot={false}
                    />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-slate-400 text-sm">
                  Hourly forecast data unavailable
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
