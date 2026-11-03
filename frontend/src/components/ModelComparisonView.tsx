import React, { useEffect, useState } from "react";
import {
  Cpu,
  CheckCircle2,
  Zap,
  TrendingUp,
  Clock,
  Layers,
  Award,
  BarChart3,
  RefreshCw,
} from "lucide-react";
import {
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
import { ModelsComparisonResponse, ModelMetric } from "../types";

export const ModelComparisonView: React.FC = () => {
  const [data, setData] = useState<ModelsComparisonResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const loadMetrics = async () => {
    try {
      setLoading(true);
      const res = await api.getModelsComparison();
      setData(res);
    } catch (err) {
      console.error("Failed to load model metrics:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMetrics();
  }, []);

  const chartData = data?.models.map((m) => ({
    name: m.model_name.replace(" Regressor", "").replace("Artificial Neural Network ", ""),
    r2_pct: Math.round(m.r2_score * 1000) / 10,
    rmse: m.rmse,
    mae: m.mae,
    latency_ms: m.inference_latency_ms,
  })) || [];

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-emerald-800 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
            Empirical Benchmark Validation
          </span>
          <h1 className="text-2xl font-black text-slate-900 mt-2">
            Machine Learning Model Comparison
          </h1>
          <p className="text-sm text-slate-600 mt-1">
            Evaluation across XGBoost, ANN, and LSTM models evaluated on a held-out synthetic test split of 1,000 samples calibrated to FAO-56 physical equations.
          </p>
        </div>
        <button
          onClick={loadMetrics}
          className="p-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-600 self-start md:self-auto"
          title="Reload metrics"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* Model Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {data?.models.map((model) => {
          const isBest = data.recommended_model === model.model_name;
          return (
            <div
              key={model.model_name}
              className={`rounded-2xl p-6 border transition-all relative flex flex-col justify-between ${
                isBest
                  ? "bg-gradient-to-b from-emerald-50/50 to-white border-emerald-500 shadow-md ring-2 ring-emerald-500/20"
                  : "bg-white border-slate-200 shadow-sm"
              }`}
            >
              {isBest && (
                <div className="absolute -top-3 right-6 bg-emerald-600 text-white text-[11px] font-black uppercase tracking-wider px-3 py-0.5 rounded-full shadow-sm flex items-center gap-1">
                  <Award className="w-3.5 h-3.5" />
                  Recommended
                </div>
              )}

              <div>
                <div className="flex items-center gap-2 mb-2">
                  <Cpu className={`w-5 h-5 ${isBest ? "text-emerald-600" : "text-slate-500"}`} />
                  <h3 className="font-extrabold text-slate-900 text-base">{model.model_name}</h3>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed mb-5 min-h-[40px]">
                  {model.description}
                </p>

                {/* Score Grid */}
                <div className="grid grid-cols-2 gap-3 mb-5">
                  <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
                    <span className="text-[10px] uppercase font-bold text-slate-600 block">
                      R² Score
                    </span>
                    <span className="text-xl font-black text-emerald-800">
                      {model.r2_score.toFixed(4)}
                    </span>
                  </div>
                  <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
                    <span className="text-[10px] uppercase font-bold text-slate-600 block">
                      RMSE (Error)
                    </span>
                    <span className="text-xl font-black text-slate-900">
                      {model.rmse.toFixed(3)}{" "}
                      <span className="text-xs font-normal text-slate-600">mm</span>
                    </span>
                  </div>
                  <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
                    <span className="text-[10px] uppercase font-bold text-slate-600 block">
                      MAE
                    </span>
                    <span className="text-base font-extrabold text-slate-900">
                      {model.mae.toFixed(3)} mm
                    </span>
                  </div>
                  <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
                    <span className="text-[10px] uppercase font-bold text-slate-600 block">
                      Inference Speed
                    </span>
                    <span className="text-base font-extrabold text-slate-900 flex items-center gap-1">
                      <Zap className="w-3.5 h-3.5 text-amber-500" />
                      {model.inference_latency_ms.toFixed(1)} ms
                    </span>
                  </div>
                </div>
              </div>

              {/* Best Features Tag List */}
              <div className="pt-4 border-t border-slate-100">
                <span className="text-[11px] font-bold text-slate-600 uppercase block mb-1.5">
                  Key Drivers:
                </span>
                <div className="flex flex-wrap gap-1">
                  {model.best_features.map((feat) => (
                    <span
                      key={feat}
                      className="text-[10px] bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-medium"
                    >
                      {feat.replace(/_/g, " ")}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Comparative Performance Chart */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="font-bold text-slate-900 text-base">R² Accuracy & Error Comparison</h2>
            <p className="text-xs text-slate-600">
              Higher R² denotes higher explained variance; Lower RMSE indicates sharper precision
            </p>
          </div>
          <span className="text-xs font-bold text-emerald-800 bg-emerald-50 px-3 py-1 rounded-full border border-emerald-200">
            Evaluation Size: {data?.benchmark_dataset_size || 5000} samples
          </span>
        </div>

        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
              <XAxis dataKey="name" tick={{ fontSize: 12, fill: "#334155" }} />
              <YAxis yAxisId="left" tick={{ fontSize: 11, fill: "#64748b" }} domain={[0, 100]} unit="%" />
              <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11, fill: "#64748b" }} unit=" mm" />
              <Tooltip contentStyle={{ borderRadius: "12px", border: "1px solid #e2e8f0" }} />
              <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: "12px" }} />
              <Bar yAxisId="left" dataKey="r2_pct" name="R² Explained Variance (%)" fill="#059669" radius={[6, 6, 0, 0]} />
              <Bar yAxisId="right" dataKey="rmse" name="RMSE Error (mm)" fill="#f59e0b" radius={[6, 6, 0, 0]} />
              <Bar yAxisId="right" dataKey="mae" name="MAE Error (mm)" fill="#3b82f6" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
