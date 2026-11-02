"""
Pydantic Schemas for Cropwater Compass
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    crop_type: str = Field(..., description="Crop type (e.g. Wheat, Rice, Maize, Cotton, Tomato, Potato, Sugarcane, Soybean)")
    growth_stage: str = Field(..., description="Crop growth stage: Initial, Vegetative, Mid-season, Late")
    area: float = Field(..., gt=0, description="Farm land area")
    area_unit: str = Field("hectares", description="Area unit: hectares, acres, or sq_meters")
    soil_type: str = Field(..., description="Soil type: Sandy, Loamy, Clay, Silty, Sandy Loam, Clay Loam")
    soil_moisture_pct: float = Field(..., ge=0, le=100, description="Current root-zone soil moisture percentage (0-100%)")
    soil_ph: Optional[float] = Field(6.5, ge=3.0, le=10.0, description="Soil pH level")
    temperature_c: float = Field(..., ge=-10.0, le=60.0, description="Air temperature in Celsius")
    humidity_pct: float = Field(..., ge=0, le=100, description="Relative humidity percentage")
    wind_speed_kmh: float = Field(..., ge=0, description="Wind speed in km/h")
    rainfall_mm: float = Field(0.0, ge=0, description="Rainfall in the last 24h / expected rainfall in mm")
    solar_radiation: Optional[float] = Field(None, ge=0, description="Solar radiation in MJ/m2/day")
    et0_mm: Optional[float] = Field(None, ge=0, description="Reference Evapotranspiration ET0 in mm/day (optional, calculated if omitted)")
    irrigation_method: str = Field("Drip", description="Irrigation method: Drip, Sprinkler, Surface/Flood")
    model_name: Optional[str] = Field("xgboost", description="ML Model to use: xgboost, ann, lstm, or ensemble")

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
    source: str  # live_api, simulation, or fallback


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


class ModelMetric(BaseModel):
    model_name: str
    r2_score: float
    rmse: float
    mae: float
    mse: float
    training_time_sec: float
    inference_latency_ms: float
    best_features: List[str]
    description: str


class ModelsComparisonResponse(BaseModel):
    models: List[ModelMetric]
    benchmark_dataset_size: int
    target_variable: str
    evaluation_date: str
    recommended_model: str


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
