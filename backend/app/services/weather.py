"""
Weather Service and FAO-56 Reference Evapotranspiration (ET0) Engine
Fetches live weather or generates climate-consistent agricultural weather data,
and provides FAO-56 Penman-Monteith & Hargreaves calculations.
"""
import math
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import urllib.request
import json

logger = logging.getLogger("weather_service")

# Preset agricultural regions with coordinates (Karnataka and major Indian agro-zones)
POPULAR_LOCATIONS: Dict[str, Dict[str, Any]] = {
    # --- Karnataka Locations ---
    "Bengaluru": {"lat": 12.9716, "lon": 77.5946, "state": "Karnataka", "climate": "tropical_savannah"},
    "Devanahalli": {"lat": 13.2483, "lon": 77.7126, "state": "Karnataka", "climate": "semi_arid"},
    "Mysuru": {"lat": 12.2958, "lon": 76.6394, "state": "Karnataka", "climate": "tropical_savannah"},
    "Mandya": {"lat": 12.5218, "lon": 76.8951, "state": "Karnataka", "climate": "semi_arid"},
    "Hassan": {"lat": 13.0033, "lon": 76.1004, "state": "Karnataka", "climate": "tropical_wet_dry"},
    "Tumakuru": {"lat": 13.3409, "lon": 77.1006, "state": "Karnataka", "climate": "semi_arid"},
    "Belagavi": {"lat": 15.8497, "lon": 74.4977, "state": "Karnataka", "climate": "tropical_wet_dry"},
    "Hubballi": {"lat": 15.3647, "lon": 75.1240, "state": "Karnataka", "climate": "semi_arid"},
    "Vijayapura": {"lat": 16.8302, "lon": 75.7100, "state": "Karnataka", "climate": "arid_semi_arid"},
    "Kalaburagi": {"lat": 17.3297, "lon": 76.8343, "state": "Karnataka", "climate": "semi_arid"},

    # --- Other Indian States ---
    "Chennai, Tamil Nadu": {"lat": 13.0827, "lon": 80.2707, "state": "Tamil Nadu", "climate": "tropical_wet_dry"},
    "Coimbatore, Tamil Nadu": {"lat": 11.0168, "lon": 76.9558, "state": "Tamil Nadu", "climate": "semi_arid"},
    "Hyderabad, Telangana": {"lat": 17.3850, "lon": 78.4867, "state": "Telangana", "climate": "semi_arid"},
    "Vijayawada, Andhra Pradesh": {"lat": 16.5062, "lon": 80.6480, "state": "Andhra Pradesh", "climate": "tropical_savannah"},
    "Pune, Maharashtra": {"lat": 18.5204, "lon": 73.8567, "state": "Maharashtra", "climate": "semi_arid"},
    "Nagpur, Maharashtra": {"lat": 21.1458, "lon": 79.0882, "state": "Maharashtra", "climate": "tropical_wet_dry"},
    "Mumbai, Maharashtra": {"lat": 19.0760, "lon": 72.8777, "state": "Maharashtra", "climate": "tropical_coastal"},
    "Punjab": {"lat": 31.1471, "lon": 75.3412, "state": "Punjab", "climate": "semi_arid"},
    "Ludhiana, Punjab": {"lat": 30.9010, "lon": 75.8573, "state": "Punjab", "climate": "semi_arid"},
    "Jaipur, Rajasthan": {"lat": 26.9124, "lon": 75.7873, "state": "Rajasthan", "climate": "semi_arid"},
    "Ahmedabad, Gujarat": {"lat": 23.0225, "lon": 72.5714, "state": "Gujarat", "climate": "semi_arid"},
    "Bhopal, Madhya Pradesh": {"lat": 23.2599, "lon": 77.4126, "state": "Madhya Pradesh", "climate": "humid_subtropical"},
    "Lucknow, Uttar Pradesh": {"lat": 26.8467, "lon": 80.9462, "state": "Uttar Pradesh", "climate": "subtropical"},
    "Kolkata, West Bengal": {"lat": 22.5726, "lon": 88.3639, "state": "West Bengal", "climate": "tropical_wet_dry"},
    "Patna, Bihar": {"lat": 25.5941, "lon": 85.1376, "state": "Bihar", "climate": "humid_subtropical"},
    "Kochi, Kerala": {"lat": 9.9312, "lon": 76.2673, "state": "Kerala", "climate": "tropical_monsoon"},

    # Legacy/Global presets for test compatibility
    "Punjab, India": {"lat": 30.7333, "lon": 76.7794, "state": "Punjab", "climate": "semi_arid"},
    "Maharashtra, India": {"lat": 19.7515, "lon": 75.7139, "state": "Maharashtra", "climate": "tropical_wet_dry"},
    "Uttar Pradesh, India": {"lat": 26.8467, "lon": 80.9462, "state": "Uttar Pradesh", "climate": "subtropical"},
    "New Delhi, India": {"lat": 28.6139, "lon": 77.2090, "state": "Delhi", "climate": "semi_arid"}
}


def find_nearest_preset_location(lat: float, lon: float) -> Optional[Dict[str, Any]]:
    """Calculates Haversine distance to popular locations to find nearest regional hub."""
    min_dist_km = float("inf")
    nearest = None
    nearest_name = None

    for name, loc in POPULAR_LOCATIONS.items():
        dlat = math.radians(loc["lat"] - lat)
        dlon = math.radians(loc["lon"] - lon)
        a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat)) * math.cos(math.radians(loc["lat"])) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        dist_km = 6371.0 * c
        if dist_km < min_dist_km:
            min_dist_km = dist_km
            nearest = loc
            nearest_name = name

    if nearest and min_dist_km <= 65.0:
        return {"name": nearest_name, "distance_km": round(min_dist_km, 1), **nearest}
    return None


def calculate_fao56_et0(
    temp_c: float,
    humidity_pct: float,
    wind_speed_kmh: float,
    solar_radiation_mj: Optional[float] = None,
    lat_deg: float = 28.0,
    day_of_year: Optional[int] = None
) -> float:
    """
    Computes Reference Evapotranspiration (ET0) using FAO-56 Penman-Monteith equation.
    T: air temperature in C
    humidity: %
    wind_speed: km/h (converted to m/s at 2m height)
    solar_radiation_mj: net/solar radiation in MJ/m^2/day (estimated if missing)
    """
    if day_of_year is None:
        day_of_year = datetime.now().timetuple().tm_yday

    # Wind speed at 2m (u2 in m/s)
    # 1 km/h = 1000 / 3600 = 0.2778 m/s
    u2 = max(0.5, wind_speed_kmh * 0.2778)

    # Saturation vapor pressure es (kPa)
    # Tetens equation
    es = 0.6108 * math.exp((17.27 * temp_c) / (temp_c + 237.3))

    # Actual vapor pressure ea (kPa)
    ea = es * (humidity_pct / 100.0)

    # Vapor pressure deficit
    vpd = max(0.05, es - ea)

    # Slope of saturation vapor pressure curve Delta (kPa/C)
    delta = (4098 * es) / ((temp_c + 237.3) ** 2)

    # Psychrometric constant gamma (kPa/C) at sea level ~ 0.067
    gamma = 0.0665

    # Solar radiation estimation if not provided:
    # Extraterrestrial radiation Ra
    phi = math.radians(lat_deg)
    dr = 1.0 + 0.033 * math.cos(2.0 * math.pi * day_of_year / 365.0)
    delta_rad = 0.409 * math.sin((2.0 * math.pi * day_of_year / 365.0) - 1.39)
    ws = math.acos(max(-1.0, min(1.0, -math.tan(phi) * math.tan(delta_rad))))
    ra = (24.0 * 60.0 / math.pi) * 0.0820 * dr * (
        ws * math.sin(phi) * math.sin(delta_rad) + math.cos(phi) * math.cos(delta_rad) * math.sin(ws)
    )

    if solar_radiation_mj is None or solar_radiation_mj <= 0:
        # Hargreaves radiation approximation (clear to partly cloudy ~ 0.65 Ra)
        rs = 0.65 * max(10.0, ra)
    else:
        rs = solar_radiation_mj

    # Net radiation Rn ~ 0.77 * Rs (albedo 0.23 for reference grass) - net longwave loss
    rn = max(1.0, 0.77 * rs - 3.5)

    # Soil heat flux G is negligible on daily scale (G ~ 0)
    g = 0.0

    # Penman-Monteith equation:
    numerator = 0.408 * delta * (rn - g) + gamma * (900.0 / (temp_c + 273.0)) * u2 * vpd
    denominator = delta + gamma * (1.0 + 0.34 * u2)

    et0 = numerator / denominator
    return round(max(0.5, min(14.0, et0)), 2)


def get_simulated_weather(lat: float, lon: float, city: Optional[str] = None) -> Dict[str, Any]:
    """
    Generates realistic, physically-consistent agricultural weather data
    based on coordinates, seasonal sun angle, and day of year.
    """
    now = datetime.now()
    doy = now.timetuple().tm_yday

    # Base temperature calculation from latitude and season
    lat_factor = math.cos(math.radians(lat))
    season_factor = math.sin((doy - 80) / 365.0 * 2.0 * math.pi)

    base_temp = 16.0 + (16.0 * lat_factor) + (7.0 * season_factor)
    temp_c = round(max(5.0, min(44.0, base_temp)), 1)

    # Relative humidity is inversely correlated to high daytime temps
    base_humidity = 58.0 - (temp_c - 20.0) * 0.8
    humidity_pct = round(max(25.0, min(92.0, base_humidity)), 1)

    wind_speed_kmh = round(8.0 + abs(math.sin(doy * 0.1) * 12.0), 1)

    # Rainfall probability
    rainfall_mm = 0.0
    if humidity_pct > 75.0:
        rainfall_mm = round(max(0.0, (humidity_pct - 75.0) * 0.6), 1)

    solar_radiation = round(16.0 + 8.0 * max(0.0, math.sin(doy / 365.0 * math.pi)), 1)
    et0 = calculate_fao56_et0(temp_c, humidity_pct, wind_speed_kmh, solar_radiation, lat, doy)

    weather_desc = "Sunny / Clear"
    if rainfall_mm > 5.0:
        weather_desc = "Moderate Rain"
    elif rainfall_mm > 0.0:
        weather_desc = "Light Showers"
    elif humidity_pct > 70.0:
        weather_desc = "Overcast / Humid"
    elif temp_c > 32.0:
        weather_desc = "Hot & Dry"

    # Generate 7-day forecast
    forecast_daily = []
    for day in range(7):
        f_date = now + timedelta(days=day)
        f_temp = round(temp_c + math.sin((doy + day) * 0.5) * 2.5, 1)
        f_hum = round(max(30.0, min(90.0, humidity_pct - math.sin((doy + day) * 0.5) * 4.0)), 1)
        f_wind = round(max(5.0, wind_speed_kmh + math.cos(day) * 3.0), 1)
        f_rain = round(max(0.0, (f_hum - 78.0) * 0.8), 1) if f_hum > 78 else 0.0
        f_et0 = calculate_fao56_et0(f_temp, f_hum, f_wind, solar_radiation, lat, f_date.timetuple().tm_yday)

        forecast_daily.append({
            "date": f_date.strftime("%Y-%m-%d"),
            "temp_max_c": round(f_temp + 3.5, 1),
            "temp_min_c": round(f_temp - 4.0, 1),
            "temp_avg_c": f_temp,
            "humidity_pct": f_hum,
            "wind_speed_kmh": f_wind,
            "rainfall_mm": f_rain,
            "et0_mm": f_et0,
            "condition": "Showers" if f_rain > 0 else ("Sunny" if f_temp > 28 else "Partly Cloudy")
        })

    # Generate 24-hour hourly forecast
    forecast_hourly = []
    for h in range(24):
        h_time = (now + timedelta(hours=h)).strftime("%Y-%m-%d %H:00")
        hour_of_day = (now.hour + h) % 24
        diurnal_factor = math.cos((hour_of_day - 14) * math.pi / 12)
        h_temp = round(temp_c + diurnal_factor * 3.5, 1)
        h_hum = round(max(20.0, min(95.0, humidity_pct - diurnal_factor * 15.0)), 1)
        h_prob = round(max(0.0, min(100.0, (h_hum - 65.0) * 2.0)), 0) if h_hum > 65 else 0.0
        solar_weight = max(0.0, math.sin((hour_of_day - 6) * math.pi / 12)) if 6 <= hour_of_day <= 18 else 0.05
        h_et0 = round((et0 / 8.0) * solar_weight, 2)
        forecast_hourly.append({
            "time": h_time,
            "temp_c": h_temp,
            "humidity_pct": h_hum,
            "precipitation_probability": h_prob,
            "et0_mm": h_et0
        })

    # Determine resolved location name and GPS indicator
    nearest = find_nearest_preset_location(lat, lon)
    is_preset_match = any(abs(l["lat"] - lat) < 0.005 and abs(l["lon"] - lon) < 0.005 for l in POPULAR_LOCATIONS.values())
    is_gps = not is_preset_match

    if not city:
        if nearest:
            city_name = f"Near {nearest['name']} ({lat:.4f}°N, {lon:.4f}°E)"
        else:
            city_name = f"GPS Farm Location ({lat:.4f}°N, {lon:.4f}°E)"
    else:
        city_name = city

    return {
        "temperature_c": temp_c,
        "humidity_pct": humidity_pct,
        "wind_speed_kmh": wind_speed_kmh,
        "rainfall_mm": rainfall_mm,
        "solar_radiation": solar_radiation,
        "et0_mm": et0,
        "weather_condition": weather_desc,
        "city": city_name,
        "latitude": round(lat, 4),
        "longitude": round(lon, 4),
        "forecast_daily": forecast_daily,
        "forecast_hourly": forecast_hourly,
        "source": "physics_simulation",
        "last_updated": now.strftime("%Y-%m-%d %H:%M:%S"),
        "is_gps": is_gps
    }


def fetch_live_or_simulated_weather(lat: float, lon: float, city: Optional[str] = None) -> Dict[str, Any]:
    """
    Attempts to fetch live weather from Open-Meteo free API for arbitrary GPS coordinates.
    Gracefully falls back to physical simulation if offline, network restricted, or timed out.
    """
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&"
        f"current=temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation,weather_code&"
        f"hourly=temperature_2m,relative_humidity_2m,precipitation_probability,et0_fao_evapotranspiration&"
        f"daily=temperature_2m_max,temperature_2m_min,et0_fao_evapotranspiration,precipitation_sum,shortwave_radiation_sum&"
        f"timezone=auto"
    )

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "CropwaterCompass/1.0 (Agriculture Water Management)"}
        )
        with urllib.request.urlopen(req, timeout=5.0) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                current = data.get("current", {})
                daily = data.get("daily", {})
                hourly = data.get("hourly", {})

                temp_c = current.get("temperature_2m", 25.0)
                humidity_pct = current.get("relative_humidity_2m", 50.0)
                wind_speed_kmh = current.get("wind_speed_10m", 10.0)
                rainfall_mm = current.get("precipitation", 0.0)
                w_code = current.get("weather_code", 0)

                # Solar radiation from Open-Meteo daily shortwave radiation sum (MJ/m2/day)
                rad_list = daily.get("shortwave_radiation_sum", [])
                solar_radiation = round(float(rad_list[0]), 1) if (rad_list and len(rad_list) > 0 and rad_list[0] is not None) else 19.5

                # FAO-56 ET0 from Open-Meteo daily or computed with FAO-56 Penman-Monteith method
                daily_et0 = daily.get("et0_fao_evapotranspiration", [])
                if daily_et0 and len(daily_et0) > 0 and daily_et0[0] is not None:
                    et0_mm = float(daily_et0[0])
                else:
                    et0_mm = calculate_fao56_et0(temp_c, humidity_pct, wind_speed_kmh, solar_radiation, lat)

                # Condition code mapping (WMO standard)
                condition = "Clear Sky"
                if w_code in [1, 2, 3]:
                    condition = "Partly Cloudy"
                elif w_code in [45, 48]:
                    condition = "Foggy"
                elif w_code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
                    condition = "Rain / Showers"
                elif w_code in [95, 96, 99]:
                    condition = "Thunderstorm"

                # 7-day daily forecast format
                forecast_daily = []
                dates = daily.get("time", [])
                max_temps = daily.get("temperature_2m_max", [])
                min_temps = daily.get("temperature_2m_min", [])
                precips = daily.get("precipitation_sum", [])
                for i in range(min(7, len(dates))):
                    t_max = round(float(max_temps[i]), 1) if (i < len(max_temps) and max_temps[i] is not None) else round(float(temp_c) + 3.0, 1)
                    t_min = round(float(min_temps[i]), 1) if (i < len(min_temps) and min_temps[i] is not None) else round(float(temp_c) - 4.0, 1)
                    r_sum = round(float(precips[i]), 1) if (i < len(precips) and precips[i] is not None) else 0.0
                    e_fao = round(float(daily_et0[i]), 2) if (i < len(daily_et0) and daily_et0[i] is not None) else round(float(et0_mm), 2)
                    forecast_daily.append({
                        "date": dates[i],
                        "temp_max_c": t_max,
                        "temp_min_c": t_min,
                        "temp_avg_c": round((t_max + t_min) / 2.0, 1),
                        "rainfall_mm": r_sum,
                        "et0_mm": e_fao,
                        "condition": "Showers" if r_sum > 2.0 else "Clear"
                    })

                # 24-hour hourly forecast format
                forecast_hourly = []
                h_times = hourly.get("time", [])
                h_temps = hourly.get("temperature_2m", [])
                h_hums = hourly.get("relative_humidity_2m", [])
                h_probs = hourly.get("precipitation_probability", [])
                h_et0s = hourly.get("et0_fao_evapotranspiration", [])

                now_iso_prefix = datetime.now().strftime("%Y-%m-%dT%H:00")
                start_h = 0
                for idx, t_str in enumerate(h_times):
                    if t_str >= now_iso_prefix:
                        start_h = idx
                        break

                for i in range(start_h, min(start_h + 24, len(h_times))):
                    forecast_hourly.append({
                        "time": h_times[i],
                        "temp_c": round(float(h_temps[i]), 1) if (i < len(h_temps) and h_temps[i] is not None) else round(float(temp_c), 1),
                        "humidity_pct": round(float(h_hums[i]), 1) if (i < len(h_hums) and h_hums[i] is not None) else round(float(humidity_pct), 1),
                        "precipitation_probability": float(h_probs[i]) if (i < len(h_probs) and h_probs[i] is not None) else 0.0,
                        "et0_mm": round(float(h_et0s[i]), 2) if (i < len(h_et0s) and h_et0s[i] is not None) else 0.2
                    })

                # Resolve display name
                nearest = find_nearest_preset_location(lat, lon)
                is_preset_match = any(abs(l["lat"] - lat) < 0.005 and abs(l["lon"] - lon) < 0.005 for l in POPULAR_LOCATIONS.values())
                is_gps = not is_preset_match

                if not city:
                    if nearest:
                        city_name = f"Near {nearest['name']} ({lat:.4f}°N, {lon:.4f}°E)"
                    else:
                        city_name = f"GPS Farm Location ({lat:.4f}°N, {lon:.4f}°E)"
                else:
                    city_name = city

                obs_time = current.get("time", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

                return {
                    "temperature_c": round(float(temp_c), 1),
                    "humidity_pct": round(float(humidity_pct), 1),
                    "wind_speed_kmh": round(float(wind_speed_kmh), 1),
                    "rainfall_mm": round(float(rainfall_mm), 1),
                    "solar_radiation": solar_radiation,
                    "et0_mm": round(float(et0_mm), 2),
                    "weather_condition": condition,
                    "city": city_name,
                    "latitude": round(lat, 4),
                    "longitude": round(lon, 4),
                    "forecast_daily": forecast_daily,
                    "forecast_hourly": forecast_hourly,
                    "source": "open_meteo_live",
                    "last_updated": obs_time,
                    "is_gps": is_gps
                }
    except Exception as e:
        logger.info(f"Using physical simulation fallback: {e}")

    # Fallback simulation
    return get_simulated_weather(lat, lon, city)
