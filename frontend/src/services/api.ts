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

const DEFAULT_PROD_API_BASE = "https://cropwater-compass.onrender.com/api";
const DEFAULT_DEV_API_BASE = "/api";

function resolveApiBase(): string {
  const envBase = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim();
  if (envBase) {
    let cleaned = envBase.replace(/\/+$/, "");
    if (!cleaned.endsWith("/api")) {
      cleaned = `${cleaned}/api`;
    }
    return cleaned;
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
  predict: (data: PredictionRequest) =>
    request<PredictionResponse>("/predict", {
      method: "POST",
      body: JSON.stringify(data),
    }),

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

  // Catalogs
  getCrops: () => request<CropInfo[]>("/crops"),
  getSoils: () => request<SoilInfo[]>("/soils"),
  getIrrigationMethods: () => request<IrrigationMethodInfo[]>("/irrigation-methods"),

  // Weather
  getCurrentWeather: (lat = 28.6139, lon = 77.209, city?: string) => {
    let q = `/weather/current?lat=${lat}&lon=${lon}`;
    if (city) q += `&city=${encodeURIComponent(city)}`;
    return request<WeatherData>(q);
  },

  getPresetLocations: () =>
    request<{ locations: Record<string, { lat: number; lon: number; climate: string }> }>(
      "/weather/locations"
    ),

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
