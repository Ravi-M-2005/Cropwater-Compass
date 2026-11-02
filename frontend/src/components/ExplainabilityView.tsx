import React, { useState, useEffect } from "react";
import {
  Sparkles,
  ArrowUpRight,
  ArrowDownRight,
  Info,
  HelpCircle,
  Cpu,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Layers,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { api } from "../services/api";
import { PredictionRequest, ShapExplanationResponse } from "../types";

interface ExplainabilityViewProps {
  initialRequest?: PredictionRequest;
}

export const ExplainabilityView: React.FC<ExplainabilityViewProps> = ({
  initialRequest,
}) => {
  const [params, setParams] = useState<PredictionRequest>(
    initialRequest || {
      crop_type: "Wheat",
      growth_stage: "Mid-season",
      area: 2.0,
      area_unit: "hectares",
      soil_type: "Loamy",
      soil_moisture_pct: 24.0,
      soil_ph: 6.8,
      temperature_c: 31.0,
      humidity_pct: 45.0,
      wind_speed_kmh: 12.0,
      rainfall_mm: 0.0,
      solar_radiation: 20.0,
      et0_mm: 4.8,
      irrigation_method: "Drip",
      model_name: "xgboost",
    }
  );

  const [explanation, setExplanation] = useState<ShapExplanationResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchExplanation = async (reqData: PredictionRequest) => {
    try {
      setLoading(true);
      const res = await api.getShapExplanation(reqData);
      setExplanation(res);
    } catch (err) {
      console.error("SHAP computation failed:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExplanation(params);
  }, []);

  const chartData = explanation?.feature_importances.map((item) => ({
    name: item.display_name,
    shap_value: item.shap_value,
    abs_importance: item.importance,
    direction: item.impact_direction,
  })) || [];

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-emerald-800 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
            Explainable AI (XAI)
          </span>
          <h1 className="text-2xl font-black text-slate-900 mt-2">
            SHAP Feature Importance & Model Transparency
          </h1>
          <p className="text-sm text-slate-600 mt-1">
            Revealing why the ML model outputs a specific water volume by attributing marginal contributions (SHAP values) to each parameter.
          </p>
        </div>
        <button
          onClick={() => fetchExplanation(params)}
          className="p-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-600 self-start md:self-auto"
          title="Recalculate SHAP"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* Baseline to Prediction Waterfall Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm">
          <span className="text-xs uppercase font-bold text-slate-600 block">
            Base Value (Mean Baseline)
          </span>
          <div className="text-2xl font-black text-slate-800 mt-2">
            {explanation?.base_value.toFixed(2)} mm
          </div>
          <p className="text-xs text-slate-600 mt-1">
            Expected gross irrigation requirement across all baseline conditions.
          </p>
        </div>

        <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm">
          <span className="text-xs uppercase font-bold text-slate-600 block">
            Estimated Requirement
          </span>
          <div className="text-2xl font-black text-emerald-800 mt-2">
            {explanation?.predicted_value.toFixed(2)} mm
          </div>
          <p className="text-xs text-slate-600 mt-1">
            Final output after aggregating positive and negative feature attributions.
          </p>
        </div>

        <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm">
          <span className="text-xs uppercase font-bold text-slate-600 block">
            Primary Influencers
          </span>
          <div className="flex items-center gap-1.5 mt-2 flex-wrap">
            {explanation?.top_positive_features.slice(0, 2).map((f) => (
              <span
                key={f}
                className="text-xs font-bold bg-amber-50 text-amber-700 border border-amber-200 px-2 py-0.5 rounded-md flex items-center gap-1"
              >
                <ArrowUpRight className="w-3 h-3" />
                {f}
              </span>
            ))}
            {explanation?.top_negative_features.slice(0, 1).map((f) => (
              <span
                key={f}
                className="text-xs font-bold bg-teal-50 text-teal-700 border border-teal-200 px-2 py-0.5 rounded-md flex items-center gap-1"
              >
                <ArrowDownRight className="w-3 h-3" />
                {f}
              </span>
            ))}
          </div>
          <p className="text-xs text-slate-600 mt-1">
            Red/Amber increases water; Green/Teal decreases water needed.
          </p>
        </div>
      </div>

      {/* SHAP Waterfall / Feature Contributions Chart */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="font-bold text-slate-900 text-base">Feature Attribution Breakdown (SHAP Values)</h2>
            <p className="text-xs text-slate-600">
              Positive values push the prediction higher than the mean; negative values lower the irrigation demand
            </p>
          </div>
          <div className="flex items-center gap-4 text-xs font-bold">
            <span className="flex items-center gap-1 text-amber-600">
              <span className="w-3 h-3 rounded-full bg-amber-500" /> Increases Water
            </span>
            <span className="flex items-center gap-1 text-emerald-600">
              <span className="w-3 h-3 rounded-full bg-emerald-600" /> Decreases Water
            </span>
          </div>
        </div>

        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData}
              layout="vertical"
              margin={{ top: 10, right: 30, left: 100, bottom: 10 }}
            >
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
              <XAxis type="number" tick={{ fontSize: 11, fill: "#64748b" }} unit=" mm" />
              <YAxis
                type="category"
                dataKey="name"
                tick={{ fontSize: 11, fill: "#334155" }}
                width={130}
              />
              <Tooltip
                formatter={(val: any) => [`${Number(val).toFixed(3)} mm`, "SHAP Contribution"]}
                contentStyle={{ borderRadius: "12px", border: "1px solid #e2e8f0" }}
              />
              <Bar dataKey="shap_value" radius={[4, 4, 4, 4]}>
                {chartData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={entry.shap_value >= 0 ? "#f59e0b" : "#059669"}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Narrative Explanation */}
        {explanation?.explanation_summary && (
          <div className="mt-6 p-4 bg-emerald-50/70 border border-emerald-200 rounded-xl text-xs text-emerald-950 flex items-start gap-3">
            <Info className="w-5 h-5 text-emerald-700 flex-shrink-0 mt-0.5" />
            <div>
              <span className="font-bold block text-emerald-900 mb-0.5">Agronomic Explanation:</span>
              <p className="leading-relaxed text-emerald-900/90">{explanation.explanation_summary}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
