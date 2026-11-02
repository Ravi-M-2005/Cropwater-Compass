import React, { useState, useEffect } from "react";
import { Navbar } from "./components/Navbar";
import { DashboardView } from "./components/DashboardView";
import { PredictionView } from "./components/PredictionView";
import { WeatherView } from "./components/WeatherView";
import { ModelComparisonView } from "./components/ModelComparisonView";
import { ExplainabilityView } from "./components/ExplainabilityView";
import { DatasetView } from "./components/DatasetView";
import { HistoryView } from "./components/HistoryView";
import { ReportsView } from "./components/ReportsView";
import { api } from "./services/api";
import { PredictionRequest } from "./types";
import { Sprout, Github, CheckCircle, ExternalLink } from "lucide-react";

export const App: React.FC = () => {
  const getInitialTab = () => {
    try {
      const params = new URLSearchParams(window.location.search);
      const tabParam = params.get("tab");
      if (tabParam) return tabParam;
      const hash = window.location.hash.replace("#", "");
      if (hash) return hash;
    } catch {
      // fallback
    }
    return "dashboard";
  };

  const [activeTab, setActiveTab] = useState(getInitialTab);
  const [systemHealthy, setSystemHealthy] = useState(true);
  const [shapRequest, setShapRequest] = useState<PredictionRequest | undefined>(undefined);

  useEffect(() => {
    window.location.hash = activeTab;
  }, [activeTab]);

  useEffect(() => {
    const ping = () => {
      api
        .checkHealth()
        .then(() => setSystemHealthy(true))
        .catch(() => setSystemHealthy(false));
    };
    ping();
    const interval = setInterval(ping, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleNavigateToShap = (req: PredictionRequest) => {
    setShapRequest(req);
    setActiveTab("explainability");
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans text-slate-800">
      {/* Dark Green Navigation Header */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        systemHealthy={systemHealthy}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === "dashboard" && <DashboardView onNavigate={setActiveTab} />}
        {activeTab === "predict" && <PredictionView onNavigateToShap={handleNavigateToShap} />}
        {activeTab === "weather" && <WeatherView />}
        {activeTab === "models" && <ModelComparisonView />}
        {activeTab === "explainability" && <ExplainabilityView initialRequest={shapRequest} />}
        {activeTab === "dataset" && <DatasetView />}
        {activeTab === "history" && <HistoryView />}
        {activeTab === "reports" && <ReportsView />}
      </main>

      {/* Professional Footer */}
      <footer className="bg-slate-900 text-slate-400 border-t border-slate-800 text-xs py-8 mt-12 no-print">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="bg-emerald-600 p-1.5 rounded-lg text-white">
              <Sprout className="w-4 h-4" />
            </div>
            <div>
              <span className="font-bold text-white text-sm">Cropwater Compass</span>
              <p className="text-[11px] text-slate-400">
                Smart Irrigation Management System Using Machine Learning
              </p>
            </div>
          </div>

          <div className="flex items-center gap-6 text-slate-400">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              FAO-56 CROPWAT Standards
            </span>
            <span>XGBoost | ANN | PyTorch LSTM</span>
            <a
              href="https://github.com/Ravi-M-2005/Cropwater-Compass"
              target="_blank"
              rel="noreferrer"
              className="text-slate-300 hover:text-white flex items-center gap-1 font-semibold"
            >
              <Github className="w-4 h-4" />
              GitHub
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
