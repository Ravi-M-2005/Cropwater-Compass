import React, { useState, useEffect } from "react";
import {
  FileSpreadsheet,
  Upload,
  Download,
  CheckCircle2,
  AlertTriangle,
  Layers,
  Droplets,
  ArrowRight,
  Database,
  FileCheck,
} from "lucide-react";
import { api } from "../services/api";

export const DatasetView: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [datasetStats, setDatasetStats] = useState<any | null>(null);

  useEffect(() => {
    api.getDatasetStats().then(setDatasetStats).catch(console.error);
  }, []);

  const handleDownloadSample = async () => {
    try {
      const sample = await api.getSampleCSV();
      const blob = new Blob([sample.csv_content], { type: "text/csv;charset=utf-8;" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", sample.filename || "cropwater_sample.csv");
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err: any) {
      alert("Error downloading sample: " + err.message);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError("Please select a .csv file first");
      return;
    }
    try {
      setUploading(true);
      setError(null);
      const res = await api.uploadCSV(file);
      setUploadResult(res);
    } catch (err: any) {
      setError(err.message || "Failed to parse and process CSV file.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-emerald-800 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
            Batch Farm Ingestion
          </span>
          <h1 className="text-2xl font-black text-slate-900 mt-2">
            Dataset Upload & Batch Prediction
          </h1>
          <p className="text-sm text-slate-600 mt-1">
            Upload agricultural CSV records to evaluate irrigation water demand across multiple farm parcels simultaneously.
          </p>
        </div>
        <button
          onClick={handleDownloadSample}
          className="inline-flex items-center gap-2 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-300 font-bold px-4 py-2.5 rounded-xl text-xs transition-colors self-start md:self-auto shadow-sm"
        >
          <Download className="w-4 h-4 text-emerald-600" />
          Download Sample CSV Template
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded-xl text-red-800 text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0 text-red-500" />
          <span>{error}</span>
        </div>
      )}

      {/* Grid: Upload Box + Benchmark Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upload Container (2 Cols) */}
        <div className="lg:col-span-2 bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
          <h3 className="font-bold text-slate-900 text-base mb-2">Upload Field CSV Dataset</h3>
          <p className="text-xs text-slate-500 mb-6">
            Supported columns: <code className="bg-slate-100 px-1 py-0.5 rounded text-slate-700">crop_type</code>,{" "}
            <code className="bg-slate-100 px-1 py-0.5 rounded text-slate-700">growth_stage</code>,{" "}
            <code className="bg-slate-100 px-1 py-0.5 rounded text-slate-700">soil_type</code>,{" "}
            <code className="bg-slate-100 px-1 py-0.5 rounded text-slate-700">soil_moisture_pct</code>,{" "}
            <code className="bg-slate-100 px-1 py-0.5 rounded text-slate-700">temperature_c</code>,{" "}
            <code className="bg-slate-100 px-1 py-0.5 rounded text-slate-700">humidity_pct</code>,{" "}
            <code className="bg-slate-100 px-1 py-0.5 rounded text-slate-700">area</code>.
          </p>

          {/* Drag & Drop Box */}
          <div className="border-2 border-dashed border-emerald-300 hover:border-emerald-500 rounded-2xl p-8 text-center bg-emerald-50/20 transition-all flex flex-col items-center justify-center">
            <Upload className="w-10 h-10 text-emerald-600 mb-3" />
            <p className="text-sm font-bold text-slate-800">
              {file ? file.name : "Select a CSV file to evaluate"}
            </p>
            <p className="text-xs text-slate-500 mt-1">
              {file ? `${(file.size / 1024).toFixed(1)} KB` : "Drag and drop or browse from your computer"}
            </p>
            <input
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              className="mt-4 text-xs text-slate-600 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-emerald-600 file:text-white hover:file:bg-emerald-500 cursor-pointer"
            />
          </div>

          <div className="mt-5 flex justify-end">
            <button
              onClick={handleUpload}
              disabled={!file || uploading}
              className="bg-emerald-600 hover:bg-emerald-500 text-white font-extrabold px-6 py-2.5 rounded-xl shadow-md transition-all text-xs flex items-center gap-2 disabled:opacity-50"
            >
              {uploading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Processing Rows...</span>
                </>
              ) : (
                <>
                  <FileCheck className="w-4 h-4" />
                  <span>Process Dataset & Run Predictions</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Benchmark Metadata Box */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center gap-2 text-slate-900 font-bold border-b border-slate-100 pb-3">
            <Database className="w-5 h-5 text-emerald-600" />
            <h4>Benchmark Metadata</h4>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <span className="text-slate-500 block">Dataset Title</span>
              <span className="font-bold text-slate-800">
                {datasetStats?.dataset_name || "Cropwater Global Irrigation Benchmark"}
              </span>
            </div>
            <div>
              <span className="text-slate-500 block">Total Training Records</span>
              <span className="font-black text-slate-900 text-base">
                {datasetStats?.total_samples ? datasetStats.total_samples.toLocaleString() : 5000} samples
              </span>
            </div>
            <div>
              <span className="text-slate-500 block">Target Metric</span>
              <span className="font-bold text-emerald-700">water_requirement_mm & Litres</span>
            </div>
            <div>
              <span className="text-slate-500 block">Supported Varieties</span>
              <span className="font-bold text-slate-800">
                {datasetStats?.supported_crops_count || 34} crops across 4 agricultural categories
              </span>
            </div>
            <div>
              <span className="text-slate-500 block">Agronomic Standard</span>
              <span className="font-semibold text-slate-700">
                {datasetStats?.standard_reference || "FAO Irrigation Paper No. 56"}
              </span>
            </div>
            <div className="pt-2 border-t border-slate-100">
              <span className="text-[11px] text-amber-700 bg-amber-50 p-2 rounded-lg block border border-amber-200">
                <strong>Synthetic Benchmark Notice:</strong> Dataset is generated using empirical FAO-56 Penman-Monteith physical models and standard agronomic crop coefficients.
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Upload Results Preview */}
      {uploadResult && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden animate-fadeIn">
          <div className="p-6 bg-emerald-50/50 border-b border-emerald-100 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <span className="text-xs uppercase font-extrabold text-emerald-800">
                Batch Evaluation Complete
              </span>
              <h3 className="text-lg font-black text-slate-900 mt-0.5">
                {uploadResult.total_rows} Rows Processed Successfully
              </h3>
            </div>
            <div className="text-right">
              <span className="text-xs text-slate-500 block">Total Water Required Across Plots</span>
              <span className="text-2xl font-black text-emerald-700">
                {uploadResult.total_water_required_litres.toLocaleString()} Litres
              </span>
            </div>
          </div>

          {/* Table Preview */}
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-slate-600 text-xs uppercase font-semibold border-b border-slate-100">
                <tr>
                  <th className="px-6 py-3.5">Crop</th>
                  <th className="px-6 py-3.5">Growth Stage</th>
                  <th className="px-6 py-3.5">Soil Type</th>
                  <th className="px-6 py-3.5">Area</th>
                  <th className="px-6 py-3.5">Water Required (Litres)</th>
                  <th className="px-6 py-3.5">Urgency</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700 text-xs">
                {uploadResult.preview?.map((row: any, i: number) => (
                  <tr key={i} className="hover:bg-slate-50/50">
                    <td className="px-6 py-3.5 font-bold text-slate-900">{row.crop_type}</td>
                    <td className="px-6 py-3.5">{row.growth_stage}</td>
                    <td className="px-6 py-3.5">{row.soil_type}</td>
                    <td className="px-6 py-3.5">
                      {row.area} {row.area_unit}
                    </td>
                    <td className="px-6 py-3.5 font-extrabold text-emerald-700">
                      {row.water_requirement_litres.toLocaleString()} L
                    </td>
                    <td className="px-6 py-3.5">
                      <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-100 text-emerald-800">
                        {row.urgency_level}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
