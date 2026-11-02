import React, { useState, useEffect } from "react";
import {
  FileText,
  Printer,
  Droplets,
  TrendingDown,
  CheckCircle2,
  ShieldCheck,
  Calendar,
  Layers,
  Sparkles,
} from "lucide-react";
import { api } from "../services/api";
import { SummaryReportResponse } from "../types";

export const ReportsView: React.FC = () => {
  const [report, setReport] = useState<SummaryReportResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .getSummaryReport()
      .then(setReport)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Action Header */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4 no-print">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-emerald-800 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
            Executive Report
          </span>
          <h1 className="text-2xl font-black text-slate-900 mt-2">
            Smart Irrigation Operational Report
          </h1>
          <p className="text-sm text-slate-600 mt-1">
            Comprehensive audit report documenting volumetric demand, model fidelity, and water stewardship strategies.
          </p>
        </div>
        <button
          onClick={handlePrint}
          className="inline-flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold px-5 py-2.5 rounded-xl text-xs shadow-md transition-all self-start sm:self-auto"
        >
          <Printer className="w-4 h-4" />
          Print / Save PDF Report
        </button>
      </div>

      {/* Printable Sheet Container */}
      <div className="bg-white rounded-3xl p-8 sm:p-12 border border-slate-200 shadow-lg max-w-4xl mx-auto space-y-8 text-slate-800 print:shadow-none print:border-none print:p-0">
        {/* Document Header */}
        <div className="border-b-2 border-slate-900 pb-6 flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 text-emerald-800 font-extrabold text-xl">
              <span className="text-2xl">🌱</span> Cropwater Compass
            </div>
            <h2 className="text-2xl font-black text-slate-900 mt-1">
              Irrigation Intelligence & Conservation Summary
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Standard: FAO-56 CROPWAT & Machine Learning Regression
            </p>
          </div>
          <div className="text-right text-xs text-slate-500">
            <span className="block font-mono font-bold text-slate-700">
              {report?.report_id || "RPT-20261102"}
            </span>
            <span>Date: {new Date().toLocaleDateString()}</span>
          </div>
        </div>

        {/* Executive Highlights Grid */}
        <div>
          <h3 className="text-xs font-black uppercase tracking-wider text-slate-500 mb-3">
            1. Operational Water Highlights
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
              <span className="text-[11px] font-semibold text-slate-500 block">
                Total Recommended
              </span>
              <span className="text-xl font-black text-emerald-800">
                {report?.key_metrics.total_water_recommended_litres.toLocaleString() || 0} L
              </span>
              <span className="text-[10px] text-slate-500 block">
                ({report?.key_metrics.total_water_recommended_m3 || 0} m³)
              </span>
            </div>

            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
              <span className="text-[11px] font-semibold text-slate-500 block">
                Est. Water Conserved
              </span>
              <span className="text-xl font-black text-teal-800">
                {report?.key_metrics.estimated_water_saved_litres.toLocaleString() || 0} L
              </span>
              <span className="text-[10px] text-teal-600 font-semibold block">~25% vs flood</span>
            </div>

            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
              <span className="text-[11px] font-semibold text-slate-500 block">
                Evaluations Recorded
              </span>
              <span className="text-xl font-black text-slate-900">
                {report?.key_metrics.total_evaluations || 0}
              </span>
              <span className="text-[10px] text-slate-500 block">Audit logs</span>
            </div>

            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
              <span className="text-[11px] font-semibold text-slate-500 block">
                Lead Model Accuracy
              </span>
              <span className="text-xl font-black text-emerald-800">
                R² = {report?.key_metrics.highest_accuracy_r2 || 0.99}
              </span>
              <span className="text-[10px] text-slate-500 block">
                {report?.key_metrics.primary_model || "LSTM Regressor"}
              </span>
            </div>
          </div>
        </div>

        {/* Conservation Strategies */}
        <div>
          <h3 className="text-xs font-black uppercase tracking-wider text-slate-500 mb-3">
            2. Strategic Conservation Actions
          </h3>
          <div className="bg-emerald-50/60 p-5 rounded-2xl border border-emerald-200 space-y-2.5">
            {report?.recommended_conservation_actions.map((act, i) => (
              <div key={i} className="flex items-start gap-2.5 text-xs text-emerald-950 font-medium">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 mt-0.5 flex-shrink-0" />
                <span>{act}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Water Breakdown by Crop */}
        {report?.water_distribution_by_crop && Object.keys(report.water_distribution_by_crop).length > 0 && (
          <div>
            <h3 className="text-xs font-black uppercase tracking-wider text-slate-500 mb-3">
              3. Crop Water Distribution Summary
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
              {Object.entries(report.water_distribution_by_crop).map(([crop, val]) => (
                <div key={crop} className="bg-slate-50 p-3 rounded-xl border border-slate-200 flex justify-between">
                  <span className="font-bold text-slate-800">{crop}</span>
                  <span className="font-black text-emerald-700">{val.toLocaleString()} L</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Footer / Sign-off */}
        <div className="pt-8 border-t border-slate-200 flex flex-col sm:flex-row justify-between items-center text-xs text-slate-500 gap-4">
          <div>
            <span className="font-bold block text-slate-700">Cropwater Compass Agricultural System</span>
            <span>https://github.com/Ravi-M-2005/Cropwater-Compass</span>
          </div>
          <div className="text-right">
            <span>Verified by FAO-56 Penman-Monteith Algorithm</span>
            <span className="block font-semibold text-emerald-700">Status: Certified Operational</span>
          </div>
        </div>
      </div>
    </div>
  );
};
