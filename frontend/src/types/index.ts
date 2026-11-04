export interface PredictionRequest {
  crop_type: string;
  growth_stage: string;
  area: number;
  area_unit: string;
  soil_type: string;
  soil_moisture_pct: number;
  soil_ph?: number;
  temperature_c: number;
  humidity_pct: number;
  wind_speed_kmh: number;
  rainfall_mm: number;
  solar_radiation?: number;
  et0_mm?: number;
  irrigation_method: string;
  model_name?: string;
}

export interface ScheduleRecommendation {
  frequency_days: number;
  duration_hours: number;
  best_time: string;
  emitter_discharge_lph?: number;
  next_irrigation_date: string;
}

export interface PredictionResponse {
  id?: string;
  crop_type: string;
  growth_stage: string;
  area: number;
  area_unit: string;
  area_sq_meters: number;
  soil_type: string;
  soil_moisture_pct: number;
  water_requirement_litres: number;
  water_requirement_m3: number;
  water_requirement_mm: number;
  net_irrigation_requirement_mm: number;
  gross_irrigation_requirement_mm: number;
  reference_et0_mm: number;
  crop_kc: number;
  crop_evapotranspiration_etc_mm: number;
  effective_rainfall_mm: number;
  soil_depletion_fraction: number;
  irrigation_efficiency_pct: number;
  irrigation_recommended: boolean;
  urgency_level: "Critical" | "High" | "Moderate" | "Low" | "None";
  recommended_schedule: ScheduleRecommendation;
  recommendations: string[];
  model_used: string;
  model_predictions: Record<string, number>;
  timestamp: string;
}

export interface ModelMetric {
  model_name: string;
  r2_score: number;
  rmse: number;
  mae: number;
  mse: number;
  training_time_sec: number;
  inference_latency_ms: number;
  best_features: string[];
  description: string;
}

export interface ModelsComparisonResponse {
  models: ModelMetric[];
  benchmark_dataset_size: number;
  target_variable: string;
  evaluation_date: string;
  recommended_model: string;
}

export interface FeatureImportanceItem {
  feature: string;
  display_name: string;
  importance: number;
  shap_value: number;
  impact_direction: "increases_water" | "decreases_water";
}

export interface ShapExplanationResponse {
  base_value: number;
  predicted_value: number;
  model_name: string;
  feature_importances: FeatureImportanceItem[];
  top_positive_features: string[];
  top_negative_features: string[];
  explanation_summary: string;
}

export interface DailyForecast {
  date: string;
  temp_max_c: number;
  temp_min_c: number;
  temp_avg_c: number;
  rainfall_mm: number;
  et0_mm: number;
  condition: string;
}

export interface HourlyForecast {
  time: string;
  temp_c: number;
  humidity_pct: number;
  precipitation_probability?: number;
  et0_mm: number;
}

export interface WeatherData {
  temperature_c: number;
  humidity_pct: number;
  wind_speed_kmh: number;
  rainfall_mm: number;
  solar_radiation: number;
  et0_mm: number;
  weather_condition: string;
  city?: string;
  latitude: number;
  longitude: number;
  forecast_daily?: DailyForecast[];
  forecast_hourly?: HourlyForecast[];
  source: string;
  last_updated?: string;
  is_gps?: boolean;
}

export interface CropInfo {
  name: string;
  category: string;
  kc_initial: number;
  kc_mid: number;
  kc_late: number;
  root_depth_meters: number;
  critical_depletion_fraction: number;
  typical_yield_season_days: number;
}

export interface SoilInfo {
  name: string;
  field_capacity_pct: number;
  wilting_point_pct: number;
  available_water_capacity_mm_per_m: number;
  infiltration_rate_mm_per_hr: number;
  description: string;
}

export interface IrrigationMethodInfo {
  name: string;
  efficiency_pct: number;
  typical_pressure_bar: number;
  suitable_crops: string[];
  description: string;
}

export interface HistoryStatsResponse {
  total_predictions: number;
  total_water_litres: number;
  avg_water_litres_per_hectare: number;
  water_by_crop: Record<string, number>;
  water_by_soil: Record<string, number>;
  predictions_by_model: Record<string, number>;
  urgency_distribution: Record<string, number>;
}

export interface SummaryReportResponse {
  report_id: string;
  generated_at: string;
  title: string;
  key_metrics: {
    total_evaluations: number;
    total_water_recommended_litres: number;
    total_water_recommended_m3: number;
    estimated_water_saved_litres: number;
    primary_model: string;
    highest_accuracy_r2: number;
  };
  water_distribution_by_crop: Record<string, number>;
  soil_profile_breakdown: Record<string, number>;
  urgency_levels: Record<string, number>;
  recent_activity: PredictionResponse[];
  recommended_conservation_actions: string[];
}
