"""
Pydantic Schemas for Cropwater Compass
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


class PredictionRequest(BaseModel):
    crop_type: str = Field(..., description="Crop type (e.g. Wheat, Rice, Maize, Cotton, Tomato, Potato, Sugarcane, Soybean)")
    growth_stage: str = Field(..., description="Crop growth stage: Initial, Vegetative, Mid-season, Late")
    area: float = Field(..., gt=0, description="Farm land area (must be greater than 0)")
    area_unit: str = Field("hectares", description="Area unit: hectares, acres, or sq_meters")
    soil_type: str = Field(..., description="Soil type: Sandy, Loamy, Clay, Silty, Sandy Loam, Clay Loam")
    soil_moisture_pct: float = Field(..., ge=0.0, le=100.0, description="Current root-zone soil moisture percentage (0-100%)")
    soil_ph: Optional[float] = Field(6.5, ge=3.0, le=11.0, description="Soil pH level (3.0 to 11.0)")
    temperature_c: float = Field(..., ge=-20.0, le=60.0, description="Air temperature in Celsius (-20 to 60°C)")
    humidity_pct: float = Field(..., ge=0.0, le=100.0, description="Relative humidity percentage (0-100%)")
    wind_speed_kmh: float = Field(..., ge=0.0, description="Wind speed in km/h (>= 0)")
    rainfall_mm: float = Field(0.0, ge=0.0, description="Rainfall in the last 24h / expected rainfall in mm (>= 0)")
    solar_radiation: Optional[float] = Field(None, ge=0.0, description="Solar radiation in MJ/m2/day")
    et0_mm: Optional[float] = Field(None, ge=0.0, description="Reference Evapotranspiration ET0 in mm/day (optional, calculated if omitted)")
    irrigation_method: str = Field("Drip", description="Irrigation method: Drip, Sprinkler, Surface/Flood")
    model_name: Optional[str] = Field("xgboost", description="ML Model to use: xgboost, ann, lstm, or ensemble")

    # Optional geographical coordinates
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Latitude in decimal degrees (-90 to 90)")
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="Longitude in decimal degrees (-180 to 180)")

    # Optional ISRIC SoilGrids 250m properties
    soil_source: Optional[str] = Field("manual", description="Source of soil properties: manual or isric_soilgrids_250m")
    soil_depth_interval: Optional[str] = Field("0-5cm", description="Soil depth interval: 0-5cm, 5-15cm, 15-30cm, 30-60cm, 60-100cm, 100-200cm")
    sand_pct: Optional[float] = Field(None, ge=0.0, le=100.0, description="Soil sand fraction percentage")
    silt_pct: Optional[float] = Field(None, ge=0.0, le=100.0, description="Soil silt fraction percentage")
    clay_pct: Optional[float] = Field(None, ge=0.0, le=100.0, description="Soil clay fraction percentage")
    soil_organic_carbon_g_per_kg: Optional[float] = Field(None, ge=0.0, description="Soil organic carbon in g/kg")
    soil_bulk_density_cg_per_cm3: Optional[float] = Field(None, ge=0.0, description="Bulk density in cg/cm3 or kg/dm3")
    soil_cec_cmolc_per_kg: Optional[float] = Field(None, ge=0.0, description="Cation exchange capacity at pH 7")
    volumetric_water_content_fc_pct: Optional[float] = Field(None, ge=0.0, le=100.0, description="Field capacity at 33 kPa (%)")
    volumetric_water_content_wp_pct: Optional[float] = Field(None, ge=0.0, le=100.0, description="Wilting point at 1500 kPa (%)")
    awc_volumetric_pct: Optional[float] = Field(None, ge=0.0, le=100.0, description="Available water capacity (%)")

    @field_validator("area")
    @classmethod
    def validate_area_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Farm area must be strictly positive (> 0)")
        return v

    @field_validator("rainfall_mm")
    @classmethod
    def validate_rainfall_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Rainfall cannot be negative")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "crop_type": "Wheat",
                "growth_stage": "Mid-season",
                "area": 2.5,
                "area_unit": "hectares",
                "soil_type": "Loamy",
                "soil_moisture_pct": 32.0,
                "soil_ph": 6.8,
                "temperature_c": 28.5,
                "humidity_pct": 52.0,
                "wind_speed_kmh": 11.4,
                "rainfall_mm": 0.0,
                "solar_radiation": 21.0,
                "et0_mm": 4.6,
                "irrigation_method": "Drip",
                "model_name": "xgboost"
            }
        }
    }


class ScheduleRecommendation(BaseModel):
    frequency_days: int
    duration_hours: float
    best_time: str
    emitter_discharge_lph: Optional[float] = None
    next_irrigation_date: str


class PredictionResponse(BaseModel):
    id: Optional[str] = None
    crop_type: str
    growth_stage: str
    area: float
    area_unit: str
    area_sq_meters: float
    soil_type: str
    soil_moisture_pct: float

    # Core water volume outputs
    water_requirement_litres: float = Field(..., description="Total water volume requirement in litres")
    water_requirement_m3: float = Field(..., description="Total water volume requirement in cubic meters")
    water_requirement_mm: float = Field(..., description="Gross water depth required in millimeters")
    net_irrigation_requirement_mm: float = Field(..., description="Net irrigation requirement after accounting for rainfall and soil depletion")
    gross_irrigation_requirement_mm: float = Field(..., description="Gross irrigation requirement after application efficiency")

    # Agronomic parameters
    reference_et0_mm: float
    crop_kc: float
    crop_evapotranspiration_etc_mm: float
    effective_rainfall_mm: float
    soil_depletion_fraction: float
    irrigation_efficiency_pct: float

    # Recommendation status
    irrigation_recommended: bool
    urgency_level: str  # Critical, High, Moderate, Low, None
    recommended_schedule: ScheduleRecommendation
    recommendations: List[str]

    # ML Model comparison details
    model_used: str
    model_predictions: Dict[str, float] = Field(default_factory=dict, description="Predictions in mm by individual models (xgboost, ann, lstm)")

    # SoilGrids details (if used)
    soil_source: Optional[str] = "manual"
    usda_soil_texture: Optional[str] = None
    soil_depth_interval: Optional[str] = None

    timestamp: str


class BatchPredictionRequest(BaseModel):
    records: List[PredictionRequest]


class BatchPredictionResponse(BaseModel):
    total_records: int
    total_water_litres: float
    predictions: List[PredictionResponse]


class WeatherQuery(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    city: Optional[str] = None


class WeatherData(BaseModel):
    temperature_c: float
    humidity_pct: float
    wind_speed_kmh: float
    rainfall_mm: float
    solar_radiation: float
    et0_mm: float
    weather_condition: str
    city: Optional[str] = None
    latitude: float
    longitude: float
    forecast_daily: Optional[List[Dict[str, Any]]] = None
    forecast_hourly: Optional[List[Dict[str, Any]]] = None
    source: str  # live_api, simulation, or fallback
    last_updated: Optional[str] = None
    is_gps: Optional[bool] = False


class ET0CalculationRequest(BaseModel):
    temperature_c: float
    humidity_pct: float
    wind_speed_kmh: float
    solar_radiation: Optional[float] = None
    latitude: Optional[float] = 20.0
    day_of_year: Optional[int] = 180


class ET0CalculationResponse(BaseModel):
    et0_mm: float
    method_used: str
    details: Dict[str, Any]


# ---------------------------------------------------------------------------
# ISRIC SoilGrids 250m Schemas
# ---------------------------------------------------------------------------

class SoilPropertyItem(BaseModel):
    property: str
    name: str
    raw_mean: Optional[float] = None
    raw_unit: str
    converted_value: Optional[float] = None
    converted_unit: str
    depth_interval: str
    description: str


class SoilPropertiesResponse(BaseModel):
    latitude: float
    longitude: float
    depth_interval: str
    source: str = "isric_soilgrids_250m"
    cached: bool = False
    status: str = "success"  # success, partial, unavailable
    status_message: Optional[str] = None
    usda_texture_class: Optional[str] = None
    mapped_soil_type: Optional[str] = None
    fao_awc_estimate_mm_per_m: Optional[float] = None
    properties: Dict[str, SoilPropertyItem] = Field(default_factory=dict)
    citation: str = "ISRIC - World Soil Information (SoilGrids250m v2.0)"


class TextureClassifyRequest(BaseModel):
    sand_pct: float = Field(..., ge=0.0, le=100.0)
    silt_pct: float = Field(..., ge=0.0, le=100.0)
    clay_pct: float = Field(..., ge=0.0, le=100.0)


class TextureClassifyResponse(BaseModel):
    sand_pct: float
    silt_pct: float
    clay_pct: float
    usda_texture_class: str
    mapped_cropwater_soil: str
    field_capacity_pct: float
    wilting_point_pct: float
    awc_mm_per_m: float


# ---------------------------------------------------------------------------
# Cross-Validation & Regression Evaluation Schemas
# ---------------------------------------------------------------------------

class CrossValidationResult(BaseModel):
    k_folds: int = 5
    r2_mean: float
    r2_std: float
    rmse_mean: float
    rmse_std: float
    mae_mean: float
    mae_std: float
    mape_mean: float
    mape_std: float
    fold_scores: Optional[List[Dict[str, float]]] = None


class ResidualAnalysis(BaseModel):
    residual_mean: float
    residual_std: float
    residual_min: float
    residual_max: float
    quantiles: Dict[str, float]
    distribution_bins: List[Dict[str, Any]]
    actual_vs_predicted_sample: Optional[List[Dict[str, float]]] = None


class ModelMetric(BaseModel):
    model_name: str
    r2_score: float
    rmse: float
    mae: float
    mse: float
    mape: float
    training_time_sec: float
    inference_latency_ms: float
    best_features: List[str]
    description: str
    strengths: Optional[List[str]] = None
    limitations: Optional[List[str]] = None
    suitability_reason: Optional[str] = None
    cross_validation: Optional[CrossValidationResult] = None
    residual_analysis: Optional[ResidualAnalysis] = None


class ExternalDatasetValidation(BaseModel):
    dataset_name: str
    source_url: str
    license: str
    total_records: int
    features: List[str]
    target_variable: str
    target_description: str
    limitations: str
    metrics_by_model: Dict[str, Dict[str, float]]


class ModelsComparisonResponse(BaseModel):
    models: List[ModelMetric]
    benchmark_dataset_size: int
    target_variable: str
    evaluation_date: str
    recommended_model: str
    model_justifications: Optional[Dict[str, Dict[str, Any]]] = None
    external_dataset_validation: Optional[ExternalDatasetValidation] = None


class FeatureImportanceItem(BaseModel):
    feature: str
    display_name: str
    importance: float
    shap_value: float
    impact_direction: str  # "increases_water" or "decreases_water"


class ShapExplanationResponse(BaseModel):
    base_value: float
    predicted_value: float
    model_name: str
    feature_importances: List[FeatureImportanceItem]
    top_positive_features: List[str]
    top_negative_features: List[str]
    explanation_summary: str


class HistoryFilter(BaseModel):
    limit: Optional[int] = 50
    offset: Optional[int] = 0
    crop_type: Optional[str] = None
    soil_type: Optional[str] = None


class HistoryStatsResponse(BaseModel):
    total_predictions: int
    total_water_litres: float
    avg_water_litres_per_hectare: float
    water_by_crop: Dict[str, float]
    water_by_soil: Dict[str, float]
    predictions_by_model: Dict[str, int]
    urgency_distribution: Dict[str, int]


class CropInfo(BaseModel):
    name: str
    category: str
    kc_initial: float
    kc_mid: float
    kc_late: float
    root_depth_meters: float
    critical_depletion_fraction: float
    typical_yield_season_days: int


class SoilInfo(BaseModel):
    name: str
    field_capacity_pct: float
    wilting_point_pct: float
    available_water_capacity_mm_per_m: float
    infiltration_rate_mm_per_hr: float
    description: str


class IrrigationMethodInfo(BaseModel):
    name: str
    efficiency_pct: float
    typical_pressure_bar: float
    suitable_crops: List[str]
    description: str
