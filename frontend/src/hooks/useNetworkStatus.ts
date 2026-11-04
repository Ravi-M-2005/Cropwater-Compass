import { useState, useEffect, useCallback } from "react";
import { networkManager, NetworkStatus, DataSourceMode } from "../services/networkManager";

export function useNetworkStatus() {
  const [status, setStatus] = useState<NetworkStatus>(networkManager.getStatus());

  useEffect(() => {
    return networkManager.subscribe(setStatus);
  }, []);

  const setMode = useCallback((mode: DataSourceMode, reason?: string) => {
    networkManager.setMode(mode, reason);
  }, []);

  const switchToLive = useCallback(async (): Promise<boolean> => {
    const reachable = await networkManager.verifyOpenMeteoReachability();
    if (reachable) {
      networkManager.setMode("LIVE_OPEN_METEO");
      return true;
    } else {
      networkManager.reportApiFailure("Internet or Open-Meteo API is still unreachable. Remaining in Offline Dataset Mode.");
      return false;
    }
  }, []);

  const switchToOffline = useCallback((reason?: string) => {
    networkManager.setMode("OFFLINE_DATASET", reason || "Manually switched to Offline Dataset Mode.");
  }, []);

  const switchToManual = useCallback(() => {
    networkManager.setMode("MANUAL_INPUT");
  }, []);

  return {
    ...status,
    setMode,
    switchToLive,
    switchToOffline,
    switchToManual,
  };
}
