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

# Preset agricultural regions with coordinates
POPULAR_LOCATIONS: Dict[str, Dict[str, float]] = {
    "Punjab, India": {"lat": 30.7333, "lon": 76.7794, "climate": "semi_arid"},
    "Haryana, India": {"lat": 29.0588, "lon": 76.0856, "climate": "semi_arid"},
    "Maharashtra, India": {"lat": 19.7515, "lon": 75.7139, "climate": "tropical_wet_dry"},
    "Uttar Pradesh, India": {"lat": 26.8467, "lon": 80.9462, "climate": "subtropical"},
    "California Central Valley, USA": {"lat": 36.7783, "lon": -119.4179, "climate": "mediterranean"},
    "Iowa Corn Belt, USA": {"lat": 41.8780, "lon": -93.0977, "climate": "humid_continental"},
    "Nile Delta, Egypt": {"lat": 30.8760, "lon": 31.0004, "climate": "arid"},
    "New Delhi, India": {"lat": 28.6139, "lon": 77.2090, "climate": "semi_arid"}
}


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

    return {
        "temperature_c": temp_c,
        "humidity_pct": humidity_pct,
        "wind_speed_kmh": wind_speed_kmh,
        "rainfall_mm": rainfall_mm,
        "solar_radiation": solar_radiation,
        "et0_mm": et0,
        "weather_condition": weather_desc,
        "city": city or f"Farm Region ({lat:.2f}, {lon:.2f})",
        "latitude": lat,
        "longitude": lon,
        "forecast_daily": forecast_daily,
        "source": "physics_simulation"
    }


def fetch_live_or_simulated_weather(lat: float, lon: float, city: Optional[str] = None) -> Dict[str, Any]:
    """
    Attempts to fetch live weather from Open-Meteo free API.
    Gracefully falls back to physical simulation if offline, network restricted, or timed out.
    """
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&"
        f"current=temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation,weather_code&"
        f"daily=temperature_2m_max,temperature_2m_min,et0_fao_evapotranspiration,precipitation_sum&"
        f"timezone=auto"
    )

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "CropwaterCompass/1.0 (Agriculture Water Management)"}
        )
        with urllib.request.urlopen(req, timeout=3.5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                current = data.get("current", {})
                daily = data.get("daily", {})

                temp_c = current.get("temperature_2m", 25.0)
                humidity_pct = current.get("relative_humidity_2m", 50.0)
                wind_speed_kmh = current.get("wind_speed_10m", 10.0)
                rainfall_mm = current.get("precipitation", 0.0)
                w_code = current.get("weather_code", 0)

                # FAO-56 ET0 from Open-Meteo daily or computed
                daily_et0 = daily.get("et0_fao_evapotranspiration", [])
                et0_mm = daily_et0[0] if (daily_et0 and len(daily_et0) > 0 and daily_et0[0] is not None) else calculate_fao56_et0(temp_c, humidity_pct, wind_speed_kmh, None, lat)

                # Condition code mapping (WMO)
                condition = "Clear Sky"
                if w_code in [1, 2, 3]:
                    condition = "Partly Cloudy"
                elif w_code in [45, 48]:
                    condition = "Foggy"
                elif w_code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
                    condition = "Rain / Showers"
                elif w_code in [95, 96, 99]:
                    condition = "Thunderstorm"

                # 7-day forecast format
                forecast_daily = []
                dates = daily.get("time", [])
                max_temps = daily.get("temperature_2m_max", [])
                min_temps = daily.get("temperature_2m_min", [])
                precips = daily.get("precipitation_sum", [])
                for i in range(min(7, len(dates))):
                    t_max = max_temps[i] if i < len(max_temps) else temp_c + 3
                    t_min = min_temps[i] if i < len(min_temps) else temp_c - 4
                    r_sum = precips[i] if i < len(precips) else 0.0
                    e_fao = daily_et0[i] if i < len(daily_et0) else et0_mm
                    forecast_daily.append({
                        "date": dates[i],
                        "temp_max_c": t_max,
                        "temp_min_c": t_min,
                        "temp_avg_c": round((t_max + t_min) / 2.0, 1),
                        "rainfall_mm": r_sum,
                        "et0_mm": round(e_fao, 2) if e_fao is not None else 4.0,
                        "condition": "Showers" if r_sum > 2 else "Clear"
                    })

                return {
                    "temperature_c": round(temp_c, 1),
                    "humidity_pct": round(humidity_pct, 1),
                    "wind_speed_kmh": round(wind_speed_kmh, 1),
                    "rainfall_mm": round(rainfall_mm, 1),
                    "solar_radiation": 19.5,
                    "et0_mm": round(et0_mm, 2),
                    "weather_condition": condition,
                    "city": city or f"Lat: {lat:.2f}, Lon: {lon:.2f}",
                    "latitude": lat,
                    "longitude": lon,
                    "forecast_daily": forecast_daily,
                    "source": "open_meteo_live"
                }
    except Exception as e:
        logger.info(f"Using physical simulation fallback: {e}")

    # Fallback simulation
    return get_simulated_weather(lat, lon, city)
