import { useState, useEffect, useCallback } from "react";

export interface Coordinates {
  latitude: number;
  longitude: number;
  accuracy?: number;
}

export interface GeolocationState {
  coords: Coordinates | null;
  loading: boolean;
  error: string | null;
  permissionDenied: boolean;
  isSupported: boolean;
  timestamp: number | null;
}

export function useGeolocation(autoDetectOnMount: boolean = false) {
  const isSupported = typeof window !== "undefined" && "geolocation" in navigator;

  const [coords, setCoords] = useState<Coordinates | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [permissionDenied, setPermissionDenied] = useState<boolean>(false);
  const [timestamp, setTimestamp] = useState<number | null>(null);

  const detectLocation = useCallback((): Promise<Coordinates | null> => {
    return new Promise((resolve) => {
      if (!isSupported) {
        const msg = "GPS Geolocation is not supported by your current browser.";
        setError(msg);
        setLoading(false);
        resolve(null);
        return;
      }

      setLoading(true);
      setError(null);

      navigator.geolocation.getCurrentPosition(
        (position) => {
          const loc: Coordinates = {
            latitude: Number(position.coords.latitude.toFixed(6)),
            longitude: Number(position.coords.longitude.toFixed(6)),
            accuracy: position.coords.accuracy ? Math.round(position.coords.accuracy) : undefined,
          };
          setCoords(loc);
          setLoading(false);
          setError(null);
          setPermissionDenied(false);
          setTimestamp(position.timestamp || Date.now());
          resolve(loc);
        },
        (geoErr) => {
          let errorMsg = "Unable to determine device GPS coordinates.";
          let isDenied = false;

          if (geoErr.code === geoErr.PERMISSION_DENIED) {
            errorMsg = "Location permission was denied. You can select your farming region manually or retry GPS detection.";
            isDenied = true;
          } else if (geoErr.code === geoErr.POSITION_UNAVAILABLE) {
            errorMsg = "GPS satellite or network signal is currently unavailable. Using manual region selection as fallback.";
          } else if (geoErr.code === geoErr.TIMEOUT) {
            errorMsg = "GPS detection request timed out. Please retry or pick a manual region.";
          }

          setLoading(false);
          setError(errorMsg);
          setPermissionDenied(isDenied);
          resolve(null);
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 30000,
        }
      );
    });
  }, [isSupported]);

  const clearLocation = useCallback(() => {
    setCoords(null);
    setError(null);
    setLoading(false);
    setPermissionDenied(false);
  }, []);

  useEffect(() => {
    if (autoDetectOnMount) {
      detectLocation();
    }
  }, [autoDetectOnMount, detectLocation]);

  return {
    coords,
    loading,
    error,
    permissionDenied,
    isSupported,
    timestamp,
    detectLocation,
    clearLocation,
  };
}
