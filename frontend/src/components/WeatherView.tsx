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
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { api } from "../services/api";
import { WeatherData, DailyForecast } from "../types";
import { SearchableSelect, SelectOption } from "./SearchableSelect";

export const WeatherView: React.FC = () => {
  const [weather, setWeather] = useState<WeatherData | null>(null);
  const [locations, setLocations] = useState<Record<string, any>>({});
  const [selectedLocation, setSelectedLocation] = useState("Bengaluru");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Custom coordinate inputs
  const [lat, setLat] = useState(12.9716);
  const [lon, setLon] = useState(77.5946);

  const fetchWeather = async (latitude: number, longitude: number, city?: string) => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getCurrentWeather(latitude, longitude, city);
      setWeather(data);
    } catch (err: any) {
      console.error("Failed to load weather:", err);
      setError(err.message || "Failed to retrieve real-time weather from Open-Meteo API.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const init = async () => {
      try {
        const locRes = await api.getPresetLocations();
        const locMap = locRes.locations || {};
        setLocations(locMap);
        const defaultName = locMap["Bengaluru"] ? "Bengaluru" : Object.keys(locMap)[0] || "Punjab, India";
        const defaultLoc = locMap[defaultName] || { lat: 12.9716, lon: 77.5946 };
        setSelectedLocation(defaultName);
        setLat(defaultLoc.lat);
        setLon(defaultLoc.lon);
        fetchWeather(defaultLoc.lat, defaultLoc.lon, defaultName);
      } catch (err: any) {
        setError("Could not load preset locations.");
        fetchWeather(12.9716, 77.5946, "Bengaluru");
      }
    };
    init();
  }, []);

  const handleLocationChange = (name: string) => {
    setSelectedLocation(name);
    const loc = locations[name];
    if (loc) {
      setLat(loc.lat);
      setLon(loc.lon);
      fetchWeather(loc.lat, loc.lon, name);
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

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header with Location Select */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-teal-800 bg-teal-50 px-2.5 py-1 rounded-full border border-teal-200">
            FAO-56 Microclimate Intelligence
          </span>
          <h1 className="text-2xl font-black text-slate-900 mt-2">
            Weather & Reference Evapotranspiration (ET₀)
          </h1>
          <p className="text-sm text-slate-600 mt-1">
            Real-time atmospheric parameters and Penman-Monteith evaporative demand across Indian agricultural hubs.
          </p>
        </div>

        {/* Region selector */}
        <div className="flex items-center gap-3 self-start md:self-auto w-full md:w-80">
          <div className="flex-1">
            <SearchableSelect
              options={locationOptions}
              value={selectedLocation}
              onChange={handleLocationChange}
              placeholder="Select location..."
              searchPlaceholder="Search 26 Indian locations..."
              icon={<MapPin className="w-4 h-4" />}
            />
          </div>
          <button
            onClick={() => fetchWeather(lat, lon, selectedLocation)}
            className="p-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors shadow-sm flex-shrink-0"
            title="Refresh weather"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-emerald-600" : ""}`} />
          </button>
        </div>
      </div>

      {error && (
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

      {/* Selected Location Pill & Metadata */}
      <div className="bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2">
          <MapPin className="w-4 h-4 text-emerald-600" />
          <span className="font-bold text-slate-800 text-sm">{selectedLocation}</span>
          <span className="text-slate-600">
            ({lat.toFixed(4)}°N, {lon.toFixed(4)}°E)
          </span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-slate-700">
            Atmospheric Condition: <strong className="text-slate-900">{weather?.weather_condition || "Clear"}</strong>
          </span>
          <span
            className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold ${
              weather?.source === "open_meteo_live"
                ? "bg-emerald-100 text-emerald-800 border border-emerald-300"
                : "bg-amber-100 text-amber-800 border border-amber-300"
            }`}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                weather?.source === "open_meteo_live" ? "bg-emerald-500 animate-pulse" : "bg-amber-500"
              }`}
            />
            {weather?.source === "open_meteo_live" ? "Live Open-Meteo Feed" : "FAO-56 Simulation Engine"}
          </span>
        </div>
      </div>

      {/* Main Meteorological Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        {/* ET0 */}
        <div className="bg-emerald-900 text-white rounded-2xl p-4 shadow-sm border border-emerald-800">
          <div className="flex justify-between items-center text-emerald-300">
            <span className="text-xs font-bold uppercase">Reference ET₀</span>
            <Sun className="w-4 h-4" />
          </div>
          <div className="text-2xl font-black mt-2">
            {weather?.et0_mm ?? 4.5}{" "}
            <span className="text-xs font-normal text-emerald-300">mm/d</span>
          </div>
          <span className="text-[10px] text-emerald-200 block mt-1 font-medium">
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
          <span className="text-[10px] text-slate-500 block mt-1">2m Height</span>
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
          <span className="text-[10px] text-slate-500 block mt-1">Relative Vapor</span>
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
            {((weather?.wind_speed_kmh ?? 11) * 0.2778).toFixed(1)} m/s u₂
          </span>
        </div>

        {/* Rainfall */}
        <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm">
          <div className="flex justify-between items-center text-slate-500">
            <span className="text-xs font-bold uppercase">Precipitation</span>
            <CloudRain className="w-4 h-4 text-indigo-500" />
          </div>
          <div className="text-2xl font-black text-slate-900 mt-2">
            {weather?.rainfall_mm ?? 0}{" "}
            <span className="text-xs font-normal text-slate-500">mm</span>
          </div>
          <span className="text-[10px] text-slate-500 block mt-1">Daily Total</span>
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
          <span className="text-[10px] text-slate-500 block mt-1">Incident Flux</span>
        </div>
      </div>

      {/* 7-Day Forecast Trend */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="font-bold text-slate-900 text-base">
              7-Day Agricultural Weather & ET₀ Projection
            </h2>
            <p className="text-xs text-slate-600">
              Anticipated reference water demand trajectory for irrigation scheduling
            </p>
          </div>
          <span className="text-xs font-semibold bg-slate-100 text-slate-700 px-3 py-1 rounded-full">
            Source: {weather?.source === "open_meteo_live" ? "Open-Meteo API" : "Climate Simulator"}
          </span>
        </div>

        <div className="h-72 w-full">
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
              Forecast data unavailable
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
