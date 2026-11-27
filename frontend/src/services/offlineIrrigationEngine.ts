/**
 * Offline FAO-56 Irrigation Engine
 * Provides 100% offline agronomic calculations, volumetric water demand,
 * schedule generation, and crop parameter resolution without network calls.
 */
import { PredictionRequest, PredictionResponse, CropInfo } from "../types";
import {
  OFFLINE_CROP_PROFILES,
  OFFLINE_CROP_ALIASES,
  OfflineCropProfile,
} from "../data/cropProfiles";

export type CropProfile = OfflineCropProfile;
export const CROP_PROFILES: Record<string, OfflineCropProfile> = OFFLINE_CROP_PROFILES;

export const SOIL_PROFILES: Record<string, { fc: number; pwp: number; awc: number }> = {
  Sandy: { fc: 12.0, pwp: 5.0, awc: 70.0 },
  "Sandy Loam": { fc: 18.0, pwp: 8.0, awc: 100.0 },
  Loamy: { fc: 26.0, pwp: 12.0, awc: 140.0 },
  "Clay Loam": { fc: 32.0, pwp: 18.0, awc: 140.0 },
  Silty: { fc: 30.0, pwp: 14.0, awc: 160.0 },
  Clay: { fc: 38.0, pwp: 24.0, awc: 140.0 },
};

export const METHOD_EFFICIENCIES: Record<string, number> = {
  Drip: 90.0,
  Sprinkler: 75.0,
  "Surface/Flood": 60.0,
  Surface: 60.0,
};

export function resolveOfflineCropProfile(
  cropType: string,
  cropOverride?: CropInfo
): { canonicalName: string; profile: OfflineCropProfile } {
  if (cropOverride) {
    return {
      canonicalName: cropOverride.name,
      profile: {
        category: cropOverride.category,
        scientific_name: cropOverride.scientific_name,
        kc_initial: cropOverride.kc_initial,
        kc_vegetative: (cropOverride.kc_initial + cropOverride.kc_mid) / 2.0,
        kc_mid: cropOverride.kc_mid,
        kc_late: cropOverride.kc_late,
        root_depth_meters: cropOverride.root_depth_meters,
        critical_depletion_fraction: cropOverride.critical_depletion_fraction,
        typical_yield_season_days: cropOverride.typical_yield_season_days,
        notes: cropOverride.notes,
        data_source: cropOverride.data_source || "FAO-56",
        ml_validated: cropOverride.ml_validated ?? true,
      },
    };
  }

  const clean = (cropType || "").trim();
  if (!clean) {
    throw new Error("Crop type is required for offline FAO-56 calculation.");
  }

  if (OFFLINE_CROP_PROFILES[clean]) {
    return { canonicalName: clean, profile: OFFLINE_CROP_PROFILES[clean] };
  }

  if (OFFLINE_CROP_ALIASES[clean] && OFFLINE_CROP_PROFILES[OFFLINE_CROP_ALIASES[clean]]) {
    const target = OFFLINE_CROP_ALIASES[clean];
    return { canonicalName: target, profile: OFFLINE_CROP_PROFILES[target] };
  }

  const lower = clean.toLowerCase();
  for (const [k, prof] of Object.entries(OFFLINE_CROP_PROFILES)) {
    if (k.toLowerCase() === lower) {
      return { canonicalName: k, profile: prof };
    }
  }

  for (const [alias, target] of Object.entries(OFFLINE_CROP_ALIASES)) {
    if (alias.toLowerCase() === lower && OFFLINE_CROP_PROFILES[target]) {
      return { canonicalName: target, profile: OFFLINE_CROP_PROFILES[target] };
    }
  }

  throw new Error(
    `Unsupported crop "${cropType}" in offline engine — no FAO-56 parameters found.`
  );
}

export function convertAreaToSqMeters(area: number, unit: string): number {
  const u = (unit || "hectares").toLowerCase();
  if (u.includes("hect")) return area * 10000.0;
  if (u.includes("acre")) return area * 4046.86;
  return area;
}

export function getCropKcOffline(
  cropType: string,
  growthStage: string,
  cropOverride?: CropInfo
): number {
  const { profile } = resolveOfflineCropProfile(cropType, cropOverride);
  const stage = (growthStage || "Mid-season").toLowerCase();
  if (stage.includes("init")) return profile.kc_initial;
  if (stage.includes("veg") || stage.includes("develop")) return profile.kc_vegetative;
  if (stage.includes("mid")) return profile.kc_mid;
  if (stage.includes("late")) return profile.kc_late;
  return profile.kc_mid;
}

export function calculateEffectiveRainfallOffline(rainfallMm: number): number {
  if (rainfallMm <= 5.0) return 0.0;
  if (rainfallMm <= 50.0) return (rainfallMm - 5.0) * 0.75;
  return 45.0 * 0.75 + (rainfallMm - 50.0) * 0.5;
}

export function calculateOfflineIrrigation(
  req: PredictionRequest,
  cropOverride?: CropInfo
): PredictionResponse {
  const { canonicalName, profile: crop } = resolveOfflineCropProfile(
    req.crop_type,
    cropOverride
  );
  const soil = SOIL_PROFILES[req.soil_type] || SOIL_PROFILES["Loamy"];
  const efficiencyPct = METHOD_EFFICIENCIES[req.irrigation_method] || 90.0;
  const efficiency = efficiencyPct / 100.0;

  const areaSqMeters = convertAreaToSqMeters(req.area, req.area_unit);
  const et0 = req.et0_mm && req.et0_mm > 0 ? req.et0_mm : 4.5;
  const kc = getCropKcOffline(req.crop_type, req.growth_stage, cropOverride);
  const etc = et0 * kc;

  const peff = calculateEffectiveRainfallOffline(req.rainfall_mm || 0);

  // Soil water balance
  const rootDepth = crop.root_depth_meters;
  const fc = soil.fc;
  const pwp = soil.pwp;
  const taw = Math.max(10.0, 10.0 * (fc - pwp) * rootDepth);
  const raw = taw * crop.critical_depletion_fraction;

  const moisture = req.soil_moisture_pct;
  const depletion =
    moisture >= fc
      ? 0.0
      : Math.min(taw, Math.max(0.0, 10.0 * (fc - moisture) * rootDepth));
  const depletionFraction =
    taw > 0 ? Math.min(1.0, Math.max(0.0, depletion / taw)) : 0.0;

  // Net irrigation requirement
  let baseNir = Math.max(0.0, etc - peff);
  if (depletion > raw) {
    baseNir += (depletion - raw) * 0.4;
  }

  // Gross irrigation requirement
  const girMm = Number((baseNir / efficiency).toFixed(2));
  const waterLitres = Math.round(girMm * areaSqMeters);
  const waterM3 = Number((waterLitres / 1000.0).toFixed(3));

  // Urgency logic
  let urgency: "Critical" | "High" | "Moderate" | "Low" | "None" = "Moderate";
  if (moisture <= pwp + 2.0 || depletionFraction >= 0.85) {
    urgency = "Critical";
  } else if (moisture <= pwp + 5.0 || depletion > raw) {
    urgency = "High";
  } else if (depletionFraction >= 0.35) {
    urgency = "Moderate";
  } else if (girMm > 0.5) {
    urgency = "Low";
  } else {
    urgency = "None";
  }

  // Schedule recommendation
  const frequencyDays = Math.max(1, Math.min(7, Math.round(raw / Math.max(1.0, etc))));
  const applicationRateMmPerHour =
    req.irrigation_method === "Drip"
      ? 4.0
      : req.irrigation_method === "Sprinkler"
      ? 8.0
      : 15.0;
  const durationHours = Number(
    Math.max(0.5, Math.min(12.0, girMm / applicationRateMmPerHour)).toFixed(1)
  );

  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);

  const recommendations: string[] = [
    `Computed using local deterministic FAO-56 Agronomic Engine (Offline Mode) for ${canonicalName}.`,
    `Gross crop requirement: ${girMm} mm depth distributed over ${areaSqMeters.toLocaleString()} m² (${req.area} ${req.area_unit}).`,
    `Irrigation delivery efficiency calibrated to ${efficiencyPct}% for ${req.irrigation_method} systems.`,
  ];

  if (crop.data_source === "NEEDS CALIBRATION") {
    recommendations.push(
      `Calibration Notice: ${canonicalName} Kc parameters are fallback estimates. Local field calibration is recommended.`
    );
  }
  if (!crop.ml_validated) {
    recommendations.push(
      `ML Generalization Notice: Pre-trained ML models were validated on the original 34-crop benchmark; offline FAO-56 physical balance is used directly.`
    );
  }

  return {
    id: `PRED-OFFLINE-${Date.now().toString(36).toUpperCase()}`,
    crop_type: req.crop_type,
    growth_stage: req.growth_stage,
    area: req.area,
    area_unit: req.area_unit,
    area_sq_meters: areaSqMeters,
    soil_type: req.soil_type,
    soil_moisture_pct: moisture,
    water_requirement_litres: waterLitres,
    water_requirement_m3: waterM3,
    water_requirement_mm: girMm,
    net_irrigation_requirement_mm: Number(baseNir.toFixed(2)),
    gross_irrigation_requirement_mm: girMm,
    reference_et0_mm: Number(et0.toFixed(2)),
    crop_kc: Number(kc.toFixed(2)),
    crop_evapotranspiration_etc_mm: Number(etc.toFixed(2)),
    effective_rainfall_mm: Number(peff.toFixed(1)),
    soil_depletion_fraction: Number(depletionFraction.toFixed(2)),
    irrigation_efficiency_pct: efficiencyPct,
    irrigation_recommended: girMm > 0.5,
    urgency_level: urgency,
    recommended_schedule: {
      frequency_days: frequencyDays,
      duration_hours: durationHours,
      best_time: "Early Morning (05:00 AM - 08:30 AM)",
      emitter_discharge_lph: req.irrigation_method === "Drip" ? 4.0 : undefined,
      next_irrigation_date: tomorrow.toISOString().split("T")[0],
    },
    recommendations,
    model_used: "FAO-56 Deterministic Agronomic Engine (Offline)",
    model_predictions: {},
    timestamp: new Date().toISOString(),
  };
}
