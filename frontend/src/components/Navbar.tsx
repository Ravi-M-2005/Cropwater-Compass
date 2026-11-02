import React, { useState } from "react";
import {
  Sprout,
  Droplet,
  CloudSun,
  Cpu,
  BarChart2,
  FileSpreadsheet,
  History,
  FileText,
  Menu,
  X,
  Activity,
} from "lucide-react";

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  systemHealthy: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  systemHealthy,
}) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems = [
    { id: "dashboard", label: "Dashboard", icon: Activity },
    { id: "predict", label: "Irrigation Prediction", icon: Droplet },
    { id: "weather", label: "Weather & ET₀", icon: CloudSun },
    { id: "models", label: "Model Comparison", icon: Cpu },
    { id: "explainability", label: "SHAP Analysis", icon: BarChart2 },
    { id: "dataset", label: "Dataset & CSV", icon: FileSpreadsheet },
    { id: "history", label: "History", icon: History },
    { id: "reports", label: "Reports", icon: FileText },
  ];

  const handleSelectTab = (id: string) => {
    setActiveTab(id);
    setMobileMenuOpen(false);
  };

  return (
    <nav className="bg-emerald-950 text-white shadow-lg sticky top-0 z-50 border-b border-emerald-800/50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <div
            className="flex items-center space-x-3 cursor-pointer group"
            onClick={() => handleSelectTab("dashboard")}
          >
            <div className="bg-emerald-600/90 p-2 rounded-xl text-white shadow-md group-hover:bg-emerald-500 transition-colors">
              <Sprout className="w-6 h-6" />
            </div>
            <div>
              <div className="font-bold text-lg tracking-tight flex items-center gap-1.5 text-white">
                Cropwater <span className="text-emerald-400 font-extrabold">Compass</span>
              </div>
              <p className="text-[10px] text-emerald-300/80 -mt-0.5 tracking-wider font-medium">
                SMART IRRIGATION SYSTEM
              </p>
            </div>
          </div>

          {/* Desktop Navigation Links */}
          <div className="hidden lg:flex items-center space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => handleSelectTab(item.id)}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold transition-all duration-150 ${
                    isActive
                      ? "bg-emerald-600 text-white shadow-sm"
                      : "text-emerald-100/80 hover:bg-emerald-900/80 hover:text-white"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </div>

          {/* Backend Status Badge */}
          <div className="hidden sm:flex items-center space-x-3">
            <div
              className={`flex items-center gap-2 px-2.5 py-1 rounded-full text-xs font-medium border ${
                systemHealthy
                  ? "bg-emerald-900/60 text-emerald-300 border-emerald-700/60"
                  : "bg-red-950/60 text-red-300 border-red-800/60"
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  systemHealthy ? "bg-emerald-400 animate-pulse" : "bg-red-400"
                }`}
              />
              <span className="text-[11px] font-semibold">
                {systemHealthy ? "ML Engine Online" : "Connecting..."}
              </span>
            </div>
          </div>

          {/* Mobile menu button */}
          <div className="lg:hidden flex items-center">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="text-emerald-200 hover:text-white p-2 rounded-md hover:bg-emerald-900 focus:outline-none"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="lg:hidden bg-emerald-950 border-b border-emerald-800 px-4 pt-2 pb-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => handleSelectTab(item.id)}
                className={`flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm font-medium ${
                  isActive
                    ? "bg-emerald-600 text-white font-semibold"
                    : "text-emerald-100 hover:bg-emerald-900/80"
                }`}
              >
                <Icon className="w-5 h-5" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>
      )}
    </nav>
  );
};
