import React, { useEffect, useState } from "react";
import {
  Droplets,
  TrendingDown,
  Layers,
  Sparkles,
  ArrowRight,
  AlertTriangle,
  Calendar,
  CheckCircle2,
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
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";
import { api } from "../services/api";
import { HistoryStatsResponse, PredictionResponse } from "../types";

interface DashboardViewProps {
  onNavigate: (tab: string) => void;
}

const COLORS = ["#059669", "#10b981", "#34d399", "#065f46", "#6ee7b7", "#a7f3d0", "#047857"];

export const DashboardView: React.FC<DashboardViewProps> = ({ onNavigate }) => {
  const [stats, setStats] = useState<HistoryStatsResponse | null>(null);
  const [recentPredictions, setRecentPredictions] = useState<PredictionResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [statsData, historyData] = await Promise.all([
        api.getHistoryStats(),
        api.getHistory(6),
      ]);
      setStats(statsData);
      setRecentPredictions(historyData);
    } catch (err: any) {
      setError(err.message || "Failed to load dashboard metrics");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  // Format data for charts
  const cropChartData = stats?.water_by_crop
    ? Object.entries(stats.water_by_crop).map(([crop, litres]) => ({
        crop,
        litres,
        m3: Math.round(litres / 1000),
      }))
    : [];

  const soilChartData = stats?.water_by_soil
    ? Object.entries(stats.water_by_soil).map(([soil, litres]) => ({
        name: soil,
        value: litres,
      }))
    : [];

  const totalLitres = stats?.total_water_litres || 0;
  const estimatedSavedLitres = Math.round(totalLitres * 0.25);

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Top Welcome & Overview Banner */}
      <div className="bg-gradient-to-r from-emerald-900 via-emerald-800 to-teal-900 rounded-2xl p-6 sm:p-8 text-white shadow-xl relative overflow-hidden">
        <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-emerald-500/20 via-transparent to-transparent pointer-events-none" />
        <div className="max-w-3xl relative z-10">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-700/60 text-emerald-200 border border-emerald-500/30 mb-3">
            <Sparkles className="w-3.5 h-3.5 text-emerald-300" />
            AI-Driven Precision Irrigation
          </span>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            Smart Cropwater Management Dashboard
          </h1>
          <p className="mt-2 text-emerald-100 text-sm sm:text-base leading-relaxed">
            Real-time agro-meteorological monitoring and FAO-56 CROPWAT volumetric water
            estimation powered by XGBoost, Artificial Neural Networks, and LSTM deep learning.
          </p>

          <div className="mt-6 flex flex-wrap gap-3">
            <button
              onClick={() => onNavigate("predict")}
              className="inline-flex items-center gap-2 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold px-4 py-2.5 rounded-xl shadow-md transition-all text-sm"
            >
              <Droplets className="w-4 h-4" />
              New Prediction
              <ArrowRight className="w-4 h-4 ml-1" />
            </button>
            <button
              onClick={() => onNavigate("dataset")}
              className="inline-flex items-center gap-2 bg-emerald-950/60 hover:bg-emerald-950/90 text-white font-medium px-4 py-2.5 rounded-xl border border-emerald-600/50 transition-all text-sm"
            >
              <Layers className="w-4 h-4" />
              Upload Field CSV
            </button>
            <button
              onClick={loadDashboardData}
              title="Refresh Stats"
              className="p-2.5 rounded-xl bg-emerald-800/60 hover:bg-emerald-700/60 text-emerald-200 transition-colors"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            </button>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Card 1: Total Water */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
              Total Recommended
            </span>
            <div className="w-10 h-10 rounded-xl bg-emerald-50 flex items-center justify-center text-emerald-700">
              <Droplets className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-4">
            <div className="text-2xl font-black text-slate-900">
              {totalLitres.toLocaleString()}{" "}
              <span className="text-sm font-semibold text-emerald-600">Litres</span>
            </div>
            <div className="text-xs text-slate-600 mt-1 flex items-center gap-1 font-medium">
              <span>{(totalLitres / 1000).toLocaleString(undefined, { maximumFractionDigits: 1 })} m³ volume</span>
            </div>
          </div>
        </div>

        {/* Card 2: Estimated Water Saved */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
              Est. Water Conserved
            </span>
            <div className="w-10 h-10 rounded-xl bg-teal-50 flex items-center justify-center text-teal-700">
              <TrendingDown className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-4">
            <div className="text-2xl font-black text-slate-900">
              {estimatedSavedLitres.toLocaleString()}{" "}
              <span className="text-sm font-semibold text-teal-600">Litres</span>
            </div>
            <div className="text-xs text-teal-700 font-semibold mt-1">
              ~25% vs conventional unmetered flood
            </div>
          </div>
        </div>

        {/* Card 3: Average Irrigation Requirement */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
              Avg. Per Evaluation
            </span>
            <div className="w-10 h-10 rounded-xl bg-green-50 flex items-center justify-center text-green-700">
              <Layers className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-4">
            <div className="text-2xl font-black text-slate-900">
              {stats?.avg_water_litres_per_hectare
                ? stats.avg_water_litres_per_hectare.toLocaleString()
                : 0}{" "}
              <span className="text-sm font-semibold text-green-600">L/run</span>
            </div>
            <div className="text-xs text-slate-600 mt-1">
              Field capacity & ETc dynamic demand
            </div>
          </div>
        </div>

        {/* Card 4: Total Evaluations */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
              Evaluations Logged
            </span>
            <div className="w-10 h-10 rounded-xl bg-emerald-50 flex items-center justify-center text-emerald-700">
              <CheckCircle2 className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-4">
            <div className="text-2xl font-black text-slate-900">
              {stats?.total_predictions || 0}{" "}
              <span className="text-sm font-semibold text-slate-700">Records</span>
            </div>
            <div className="text-xs text-slate-600 mt-1">
              Audited in persistent SQLite DB
            </div>
          </div>
        </div>
      </div>

      {/* Visualizations Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Bar Chart: Crop-wise Water Requirement */}
        <div className="lg:col-span-2 bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="font-bold text-slate-900 text-base">
                Cumulative Water Requirement by Crop
              </h2>
              <p className="text-xs text-slate-600">
                Total evaluated irrigation volume across agricultural plots (Litres)
              </p>
            </div>
            <span className="text-xs font-semibold bg-emerald-50 text-emerald-700 px-2.5 py-1 rounded-full border border-emerald-200">
              FAO-56 Calibrated
            </span>
          </div>

          <div className="h-72 w-full">
            {cropChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={cropChartData} margin={{ top: 10, right: 10, left: 10, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="crop" tick={{ fontSize: 12, fill: "#64748b" }} interval={0} />
                  <YAxis
                    tick={{ fontSize: 11, fill: "#64748b" }}
                    tickFormatter={(val) => (val >= 1000 ? `${(val / 1000).toFixed(0)}k` : val)}
                  />
                  <Tooltip
                    formatter={(val: any) => [`${Number(val).toLocaleString()} Litres`, "Total Water"]}
                    contentStyle={{ borderRadius: "12px", border: "1px solid #e2e8f0" }}
                  />
                  <Bar dataKey="litres" fill="#059669" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-slate-400">
                <Droplets className="w-10 h-10 mb-2 opacity-40 text-emerald-500" />
                <p className="text-sm font-medium">No historical crop runs yet.</p>
                <button
                  onClick={() => onNavigate("predict")}
                  className="mt-2 text-xs font-bold text-emerald-600 hover:underline"
                >
                  Run your first prediction &rarr;
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Donut Chart: Water Demand by Soil Class */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
          <div className="mb-4">
            <h2 className="font-bold text-slate-900 text-base">Water Demand by Soil Class</h2>
            <p className="text-xs text-slate-600">Retention & infiltration distribution</p>
          </div>

          <div className="h-72 w-full flex items-center justify-center">
            {soilChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={soilChartData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={85}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {soilChartData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(val: any) => [`${Number(val).toLocaleString()} Litres`, "Water"]}
                    contentStyle={{ borderRadius: "12px", border: "1px solid #e2e8f0" }}
                  />
                  <Legend verticalAlign="bottom" height={36} wrapperStyle={{ fontSize: "11px" }} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-center text-slate-400">
                <Layers className="w-10 h-10 mx-auto mb-2 opacity-40 text-emerald-500" />
                <p className="text-sm font-medium">Awaiting soil evaluations</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Recent Activity Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="font-bold text-slate-900 text-base">Recent Field Recommendations</h2>
            <p className="text-xs text-slate-600">Latest evaluated farm plots and required irrigation volumes</p>
          </div>
          <button
            onClick={() => onNavigate("history")}
            className="text-xs font-bold text-emerald-700 hover:text-emerald-800 flex items-center gap-1 self-start sm:self-auto"
          >
            View Complete History
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50/70 text-slate-600 text-xs uppercase font-semibold border-b border-slate-100">
              <tr>
                <th className="px-6 py-3.5">Crop & Stage</th>
                <th className="px-6 py-3.5">Farm Area</th>
                <th className="px-6 py-3.5">Soil Profile</th>
                <th className="px-6 py-3.5">Water Needed (Litres)</th>
                <th className="px-6 py-3.5">Urgency</th>
                <th className="px-6 py-3.5">Model Used</th>
                <th className="px-6 py-3.5">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {recentPredictions.length > 0 ? (
                recentPredictions.map((rec, idx) => {
                  const urgencyColors: Record<string, string> = {
                    Critical: "bg-red-50 text-red-700 border-red-200",
                    High: "bg-amber-50 text-amber-700 border-amber-200",
                    Moderate: "bg-blue-50 text-blue-700 border-blue-200",
                    Low: "bg-emerald-50 text-emerald-700 border-emerald-200",
                    None: "bg-slate-100 text-slate-700 border-slate-200",
                  };
                  return (
                    <tr key={rec.id || idx} className="hover:bg-slate-50/60 transition-colors">
                      <td className="px-6 py-4 font-semibold text-slate-900 flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-emerald-500" />
                        <div>
                          <div>{rec.crop_type}</div>
                          <div className="text-xs font-normal text-slate-500">{rec.growth_stage} stage</div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        {rec.area} {rec.area_unit}
                      </td>
                      <td className="px-6 py-4">
                        <div>{rec.soil_type}</div>
                        <div className="text-xs text-slate-500">{rec.soil_moisture_pct}% moisture</div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="font-extrabold text-emerald-800 text-base">
                          {rec.water_requirement_litres.toLocaleString()} L
                        </span>
                        <span className="text-xs text-slate-600 block">
                          ({rec.water_requirement_mm.toFixed(1)} mm depth)
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold border ${
                            urgencyColors[rec.urgency_level] || urgencyColors.Moderate
                          }`}
                        >
                          {rec.urgency_level}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-xs font-medium uppercase text-slate-700 bg-slate-100 px-2 py-0.5 rounded">
                          {rec.model_used}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <button
                          onClick={() => onNavigate("history")}
                          className="text-xs font-semibold text-emerald-700 hover:underline"
                        >
                          Details
                        </button>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={7} className="px-6 py-10 text-center text-slate-500">
                    No predictions found. Click "New Prediction" above to analyze your first plot!
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
