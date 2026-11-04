/**
 * Network and Meteorological Data Source Manager
 * Coordinates automatic online/offline detection, Open-Meteo API probe,
 * and seamless fallback to the local FAO-56 agricultural dataset.
 */

export type DataSourceMode = "LIVE_OPEN_METEO" | "OFFLINE_DATASET" | "MANUAL_INPUT";

export interface NetworkStatus {
  isOnline: boolean;
  isOpenMeteoReachable: boolean;
  mode: DataSourceMode;
  offlineReason: string | null;
  lastChecked: number;
}

type Listener = (status: NetworkStatus) => void;

class NetworkManager {
  private isOnline: boolean = typeof navigator !== "undefined" ? navigator.onLine : true;
  private isOpenMeteoReachable: boolean = true;
  private mode: DataSourceMode = typeof navigator !== "undefined" && !navigator.onLine ? "OFFLINE_DATASET" : "LIVE_OPEN_METEO";
  private offlineReason: string | null = typeof navigator !== "undefined" && !navigator.onLine ? "No internet connection detected (device offline)." : null;
  private lastChecked: number = Date.now();
  private listeners: Set<Listener> = new Set();

  constructor() {
    if (typeof window !== "undefined") {
      window.addEventListener("online", () => {
        this.isOnline = true;
        this.verifyOpenMeteoReachability().then(() => {
          this.notify();
        });
      });

      window.addEventListener("offline", () => {
        this.isOnline = false;
        this.isOpenMeteoReachable = false;
        this.mode = "OFFLINE_DATASET";
        this.offlineReason = "Network connection lost. Automatically switched to local Offline Dataset Mode.";
        this.notify();
      });
    }
  }

  public getStatus(): NetworkStatus {
    return {
      isOnline: this.isOnline,
      isOpenMeteoReachable: this.isOpenMeteoReachable,
      mode: this.mode,
      offlineReason: this.offlineReason,
      lastChecked: this.lastChecked,
    };
  }

  public subscribe(listener: Listener): () => void {
    this.listeners.add(listener);
    listener(this.getStatus());
    return () => this.listeners.delete(listener);
  }

  private notify() {
    this.lastChecked = Date.now();
    const status = this.getStatus();
    this.listeners.forEach((fn) => fn(status));
  }

  public setMode(mode: DataSourceMode, reason?: string) {
    this.mode = mode;
    if (mode === "OFFLINE_DATASET") {
      this.offlineReason = reason || "Switched to local Offline Dataset Mode.";
    } else {
      this.offlineReason = null;
    }
    this.notify();
  }

  public reportApiFailure(errorMsg?: string) {
    this.isOpenMeteoReachable = false;
    this.mode = "OFFLINE_DATASET";
    this.offlineReason = errorMsg || "Open-Meteo meteorological API is unreachable or timed out.";
    this.notify();
  }

  public reportApiSuccess() {
    this.isOpenMeteoReachable = true;
    if (this.mode === "OFFLINE_DATASET" && this.isOnline && this.offlineReason?.includes("unreachable")) {
      // Don't forcefully switch if user explicitly chose offline, but mark API reachable
    }
    this.notify();
  }

  public async verifyOpenMeteoReachability(): Promise<boolean> {
    if (!navigator.onLine) {
      this.isOnline = false;
      this.isOpenMeteoReachable = false;
      return false;
    }
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 4000);
      const res = await fetch("https://api.open-meteo.com/v1/forecast?latitude=12.97&longitude=77.59&current=temperature_2m", {
        method: "HEAD",
        mode: "no-cors",
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      this.isOpenMeteoReachable = true;
      return true;
    } catch {
      this.isOpenMeteoReachable = false;
      return false;
    }
  }
}

export const networkManager = new NetworkManager();
