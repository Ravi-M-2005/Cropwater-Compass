import {
  PredictionRequest,
  PredictionResponse,
  ModelsComparisonResponse,
  ShapExplanationResponse,
  WeatherData,
  CropInfo,
  SoilInfo,
  IrrigationMethodInfo,
  HistoryStatsResponse,
  SummaryReportResponse,
} from "../types";
import {
  calculateOfflineIrrigation,
  CROP_PROFILES,
  SOIL_PROFILES,
} from "./offlineIrrigationEngine";
import { networkManager } from "./networkManager";

const DEFAULT_PROD_API_BASE = "https://cropwater-compass.onrender.com/api";
const DEFAULT_DEV_API_BASE = "/api";

function resolveApiBase(): string {
  const envBase = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim();
  if (envBase) {
    // If an explicit absolute HTTP/HTTPS URL is provided, sanitize and use it
    if (/^https?:\/\//i.test(envBase)) {
      let cleaned = envBase.replace(/\/+$/, "");
      if (!cleaned.endsWith("/api")) {
        cleaned = `${cleaned}/api`;
      }
      return cleaned;
    }
    // In local dev mode, allow relative /api proxied by Vite
    if (import.meta.env.DEV) {
      return envBase;
    }
    // In production, ignore relative paths (which fail on cloud hosts) and default to Render
    return DEFAULT_PROD_API_BASE;
  }
  // In development, default to "/api" (proxied to localhost via Vite)
  // In production builds, default to the live Render backend
  return import.meta.env.DEV ? DEFAULT_DEV_API_BASE : DEFAULT_PROD_API_BASE;
}

export const API_BASE = resolveApiBase();

export function buildApiUrl(endpoint: string): string {
  // Normalize leading slashes
  let cleanEndpoint = endpoint.replace(/^\/*/, "/");

  // Prevent duplicate "/api/api/..." if endpoint already contains the "/api" prefix
  while (cleanEndpoint.startsWith("/api/")) {
    cleanEndpoint = cleanEndpoint.substring(4);
  }
  if (cleanEndpoint === "/api") {
    cleanEndpoint = "";
  }

  return `${API_BASE}${cleanEndpoint}`;
}

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = buildApiUrl(endpoint);
  try {
    const res = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
      ...options,
    });

    if (!res.ok) {
      let errorMsg = `Server error: ${res.statusText} (${res.status})`;
      try {
        const errorData = await res.json();
        if (errorData.detail) errorMsg = errorData.detail;
      } catch {
        // Fallback to text
      }
      throw new Error(errorMsg);
    }

    return await res.json();
  } catch (err: any) {
    console.error(`API Error on [${options?.method || "GET"} ${url}]:`, err);
    throw err;
  }
}

export const api = {
  // Predictions
  predict: async (data: PredictionRequest): Promise<PredictionResponse> => {
    if (!navigator.onLine || networkManager.getStatus().mode === "OFFLINE_DATASET") {
      return calculateOfflineIrrigation(data);
    }
    try {
      return await request<PredictionResponse>("/predict", {
        method: "POST",
        body: JSON.stringify(data),
      });
    } catch (err) {
      console.warn("Backend /predict unavailable. Executing verified local FAO-56 irrigation engine:", err);
      return calculateOfflineIrrigation(data);
    }
  },

  predictBatch: (records: PredictionRequest[]) =>
    request<{ total_records: number; total_water_litres: number; predictions: PredictionResponse[] }>(
      "/predict/batch",
      {
        method: "POST",
        body: JSON.stringify({ records }),
      }
    ),

  // Models & Explainability
  getModelsComparison: () =>
    request<ModelsComparisonResponse>("/models/comparison"),

  getShapExplanation: (data: PredictionRequest) =>
    request<ShapExplanationResponse>("/explainability/shap", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Catalogs with offline fallbacks
  getCrops: async (): Promise<CropInfo[]> => {
    try {
      return await request<CropInfo[]>("/crops");
    } catch {
      return Object.entries(CROP_PROFILES).map(([name, prof]) => ({
        name,
        category: prof.category,
        kc_initial: prof.kc_initial,
        kc_mid: prof.kc_mid,
        kc_late: prof.kc_late,
        root_depth_meters: prof.root_depth_meters,
        critical_depletion_fraction: prof.critical_depletion_fraction,
        typical_yield_season_days: prof.typical_yield_season_days,
      }));
    }
  },

  getSoils: async (): Promise<SoilInfo[]> => {
    try {
      return await request<SoilInfo[]>("/soils");
    } catch {
      return Object.entries(SOIL_PROFILES).map(([name, s]) => ({
        name,
        field_capacity_pct: s.fc,
        wilting_point_pct: s.pwp,
        available_water_capacity_mm_per_m: s.awc,
        infiltration_rate_mm_per_hr: 15.0,
        description: `${name} soil type.`,
      }));
    }
  },

  getIrrigationMethods: async (): Promise<IrrigationMethodInfo[]> => {
    try {
      return await request<IrrigationMethodInfo[]>("/irrigation-methods");
    } catch {
      return [
        { name: "Drip", efficiency_pct: 90.0, typical_pressure_bar: 1.5, suitable_crops: ["Vegetables", "Orchards", "Row Crops"], description: "Localized micro-irrigation." },
        { name: "Sprinkler", efficiency_pct: 75.0, typical_pressure_bar: 2.5, suitable_crops: ["Cereals", "Pulses"], description: "Overhead pressurized distribution." },
        { name: "Surface/Flood", efficiency_pct: 60.0, typical_pressure_bar: 0.0, suitable_crops: ["Rice", "Sugarcane"], description: "Gravity-fed furrow flooding." },
      ];
    }
  },

  // Weather with fallback
  getCurrentWeather: async (lat = 28.6139, lon = 77.209, city?: string): Promise<WeatherData> => {
    let q = `/weather/current?lat=${lat}&lon=${lon}`;
    if (city) q += `&city=${encodeURIComponent(city)}`;
    return request<WeatherData>(q);
  },

  getPresetLocations: async () => {
    try {
      return await request<{ locations: Record<string, { lat: number; lon: number; climate: string; state?: string }> }>(
        "/weather/locations"
      );
    } catch {
      return {
        locations: {
          Bengaluru: { lat: 12.9716, lon: 77.5946, state: "Karnataka", climate: "tropical_savannah" },
          Devanahalli: { lat: 13.2483, lon: 77.7126, state: "Karnataka", climate: "semi_arid" },
          Mysuru: { lat: 12.2958, lon: 76.6394, state: "Karnataka", climate: "tropical_savannah" },
          Mandya: { lat: 12.5218, lon: 76.8951, state: "Karnataka", climate: "semi_arid" },
          Hassan: { lat: 13.0033, lon: 76.1004, state: "Karnataka", climate: "tropical_wet_dry" },
          Tumakuru: { lat: 13.3409, lon: 77.1006, state: "Karnataka", climate: "semi_arid" },
          Belagavi: { lat: 15.8497, lon: 74.4977, state: "Karnataka", climate: "tropical_wet_dry" },
          Hubballi: { lat: 15.3647, lon: 75.1240, state: "Karnataka", climate: "semi_arid" },
          Vijayapura: { lat: 16.8302, lon: 75.7100, state: "Karnataka", climate: "arid_semi_arid" },
          Kalaburagi: { lat: 17.3297, lon: 76.8343, state: "Karnataka", climate: "semi_arid" },
          "Chennai, Tamil Nadu": { lat: 13.0827, lon: 80.2707, state: "Tamil Nadu", climate: "tropical_wet_dry" },
          "Coimbatore, Tamil Nadu": { lat: 11.0168, lon: 76.9558, state: "Tamil Nadu", climate: "semi_arid" },
          "Hyderabad, Telangana": { lat: 17.3850, lon: 78.4867, state: "Telangana", climate: "semi_arid" },
          "Vijayawada, Andhra Pradesh": { lat: 16.5062, lon: 80.6480, state: "Andhra Pradesh", climate: "tropical_savannah" },
          "Pune, Maharashtra": { lat: 18.5204, lon: 73.8567, state: "Maharashtra", climate: "semi_arid" },
          "Nagpur, Maharashtra": { lat: 21.1458, lon: 79.0882, state: "Maharashtra", climate: "tropical_wet_dry" },
          "Mumbai, Maharashtra": { lat: 19.0760, lon: 72.8777, state: "Maharashtra", climate: "tropical_coastal" },
          Punjab: { lat: 31.1471, lon: 75.3412, state: "Punjab", climate: "semi_arid" },
          "Ludhiana, Punjab": { lat: 30.9010, lon: 75.8573, state: "Punjab", climate: "semi_arid" },
          "Jaipur, Rajasthan": { lat: 26.9124, lon: 75.7873, state: "Rajasthan", climate: "semi_arid" },
          "Ahmedabad, Gujarat": { lat: 23.0225, lon: 72.5714, state: "Gujarat", climate: "semi_arid" },
          "Bhopal, Madhya Pradesh": { lat: 23.2599, lon: 77.4126, state: "Madhya Pradesh", climate: "humid_subtropical" },
          "Lucknow, Uttar Pradesh": { lat: 26.8467, lon: 80.9462, state: "Uttar Pradesh", climate: "subtropical" },
          "Kolkata, West Bengal": { lat: 22.5726, lon: 88.3639, state: "West Bengal", climate: "tropical_wet_dry" },
          "Patna, Bihar": { lat: 25.5941, lon: 85.1376, state: "Bihar", climate: "humid_subtropical" },
          "Kochi, Kerala": { lat: 9.9312, lon: 76.2673, state: "Kerala", climate: "tropical_monsoon" },
        },
      };
    }
  },

  // Dataset Management
  uploadCSV: async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(buildApiUrl("/dataset/upload"), {
      method: "POST",
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "CSV upload failed");
    }
    return await res.json();
  },

  getSampleCSV: () =>
    request<{ filename: string; csv_content: string }>("/dataset/sample"),

  getDatasetStats: () => request<any>("/dataset/stats"),

  // History & Audit
  getHistory: (limit = 50, offset = 0, cropType?: string, soilType?: string) => {
    let q = `/history?limit=${limit}&offset=${offset}`;
    if (cropType) q += `&crop_type=${encodeURIComponent(cropType)}`;
    if (soilType) q += `&soil_type=${encodeURIComponent(soilType)}`;
    return request<PredictionResponse[]>(q);
  },

  getHistoryStats: () => request<HistoryStatsResponse>("/history/stats"),

  deleteHistoryItem: (id: string) =>
    request<{ message: string }>(`/history/${id}`, { method: "DELETE" }),

  clearHistory: () =>
    request<{ message: string }>("/history", { method: "DELETE" }),

  // Reports
  getSummaryReport: () => request<SummaryReportResponse>("/reports/summary"),

  // System Health
  checkHealth: () => request<{ status: string; database: string; ml_engine: string }>("/health"),
};
