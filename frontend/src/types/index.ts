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
  latitude?: number;
  longitude?: number;
  soil_source?: string;
  soil_depth_interval?: string;
  sand_pct?: number;
  silt_pct?: number;
  clay_pct?: number;
  volumetric_water_content_fc_pct?: number;
  volumetric_water_content_wp_pct?: number;
  awc_volumetric_pct?: number;
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
  soil_source?: string;
  usda_soil_texture?: string;
  soil_depth_interval?: string;
  timestamp: string;
}

export interface FoldScore {
  fold: number;
  r2: number;
  rmse: number;
  mae: number;
  mape: number;
}

export interface CrossValidationResult {
  k_folds: number;
  r2_mean: number;
  r2_std: number;
  rmse_mean: number;
  rmse_std: number;
  mae_mean: number;
  mae_std: number;
  mape_mean: number;
  mape_std: number;
  fold_scores: FoldScore[];
}

export interface DistributionBin {
  bin_start: number;
  bin_end: number;
  label: string;
  count: number;
}

export interface ActualVsPredictedPair {
  actual: number;
  predicted: number;
  residual: number;
}

export interface ResidualAnalysis {
  residual_mean: number;
  residual_std: number;
  residual_min?: number;
  residual_max?: number;
  quantiles: Record<string, number>;
  distribution_bins: DistributionBin[];
  actual_vs_predicted_sample?: ActualVsPredictedPair[];
}

export interface ModelMetric {
  model_name: string;
  r2_score: number;
  rmse: number;
  mae: number;
  mse: number;
  mape?: number;
  training_time_sec: number;
  inference_latency_ms: number;
  best_features: string[];
  description: string;
  strengths?: string[];
  limitations?: string[];
  suitability_reason?: string;
  cross_validation?: CrossValidationResult;
  residual_analysis?: ResidualAnalysis;
}

export interface ExternalDatasetValidation {
  dataset_name: string;
  source_url: string;
  license: string;
  total_records: number;
  features: string[];
  target_variable: string;
  target_description: string;
  limitations: string;
  metrics_by_model: Record<string, {
    r2_score: number;
    rmse: number;
    mae: number;
    mape_pct: number;
  }>;
}

export interface ModelsComparisonResponse {
  models: ModelMetric[];
  benchmark_dataset_size: number;
  target_variable: string;
  evaluation_date: string;
  recommended_model: string;
  model_justifications?: Record<string, {
    strengths: string[];
    limitations: string[];
    suitability_reason: string;
  }>;
  external_dataset_validation?: ExternalDatasetValidation;
}

export interface SoilPropertyItem {
  display_name: string;
  description: string;
  raw_value: number;
  raw_units: string;
  converted_value: number;
  target_units: string;
  conversion_factor: number;
  citation: string;
}

export interface SoilPropertiesResponse {
  latitude: number;
  longitude: number;
  depth_interval: string;
  spatial_resolution: string;
  is_available: boolean;
  source: string;
  citation: string;
  retrieval_date: string;
  properties: Record<string, SoilPropertyItem>;
  derived_usda_texture: string;
  cropwater_soil_type: string;
  field_capacity_pct: number;
  wilting_point_pct: number;
  available_water_capacity_mm_per_m: number;
  error_message?: string | null;
}

export interface TextureClassifyResponse {
  sand_pct: number;
  silt_pct: number;
  clay_pct: number;
  usda_texture_class: string;
  mapped_cropwater_soil: string;
  field_capacity_pct: number;
  wilting_point_pct: number;
  awc_mm_per_m: number;
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

export interface ReportModelBenchmark {
  model_name: string;
  test_r2: number;
  test_rmse: number;
  test_mae: number;
  cv_r2_mean?: number | null;
  cv_r2_std?: number | null;
  cv_rmse_mean?: number | null;
  cv_rmse_std?: number | null;
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
  model_benchmarks?: ReportModelBenchmark[];
  water_distribution_by_crop: Record<string, number>;
  soil_profile_breakdown: Record<string, number>;
  urgency_levels: Record<string, number>;
  recent_activity: PredictionResponse[];
  recommended_conservation_actions: string[];
}
