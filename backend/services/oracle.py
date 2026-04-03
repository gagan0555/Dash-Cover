import os
import json
import urllib.request
import urllib.error
import urllib.parse

# ─── Configuration ────────────────────────────────────────────────────────────

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "51ca69ba24d715ceea09896f4da75a9c")

# Global toggle for demo presentations to always fire a payout
MOCK_MODE_FORCE_TRIGGER = os.getenv("MOCK_MODE_FORCE_TRIGGER", "False").lower() in ("true", "1", "yes")

# Active storm state for demo
STORM_MODE_ACTIVE = False


def set_storm_mode(active: bool):
    global STORM_MODE_ACTIVE
    STORM_MODE_ACTIVE = active


# ─── PM2.5 to AQI Calculation (US EPA Standard) ──────────────────────────────
def calculate_aqi_from_pm25(pm25: float) -> int:
    """Converts raw PM2.5 concentration (μg/m³) to standard continuous AQI."""
    breakpoints = [
        (0.0, 12.0, 0, 50),
        (12.1, 35.4, 51, 100),
        (35.5, 55.4, 101, 150),
        (55.5, 150.4, 151, 200),
        (150.5, 250.4, 201, 300),
        (250.5, 350.4, 301, 400),
        (350.5, 500.4, 401, 500),
    ]
    for c_low, c_high, i_low, i_high in breakpoints:
        if c_low <= pm25 <= c_high:
            # Linear interpolation formula
            return int(((i_high - i_low) / (c_high - c_low)) * (pm25 - c_low) + i_low)
    return 500 if pm25 > 500.4 else 0

def geocode_location(query: str) -> list:
    """Fetch matching locations for a city/area query from OpenWeatherMap Geocoding API."""
    url = f"http://api.openweathermap.org/geo/1.0/direct?q={urllib.parse.quote(query)}&limit=5&appid={OPENWEATHER_API_KEY}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "DashCover/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            results = []
            for item in data:
                results.append({
                    "name": item.get('name', ''),
                    "state": item.get('state', ''),
                    "country": item.get('country', ''),
                    "lat": item.get('lat', 0.0),
                    "lon": item.get('lon', 0.0)
                })
            return results
    except Exception as e:
        print(f"[Oracle] Geocode error: {e}")
        return []

def _fetch_owm_weather(lat: float, lon: float) -> dict:
    """"""
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "DashCover/1.0"})
    with urllib.request.urlopen(req, timeout=8) as resp:
        return json.loads(resp.read().decode())


def _fetch_owm_aqi(lat: float, lon: float) -> int:
    """Retrieves raw PM2.5/PM10 from OWM and calculates standard AQI."""
    url = (
        f"https://api.openweathermap.org/data/2.5/air_pollution"
        f"?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "DashCover/1.0"})
    with urllib.request.urlopen(req, timeout=8) as resp:
        data = json.loads(resp.read().decode())
        # Instead of using OWM's basic 1-5 qualitative scale, grab exact PM2.5
        pm25_concentration = data["list"][0]["components"]["pm2_5"]
        return calculate_aqi_from_pm25(float(pm25_concentration))


# ─── Primary Entry Point ─────────────────────────────────────────────────────

def get_weather_data(lat: float, lon: float) -> dict:
    if STORM_MODE_ACTIVE:
        return {
            "rain_1h": 25.5,
            "aqi": 85,
            "temp_c": 24.0,
            "humidity": 95,
            "description": "Heavy intensity rain",
            "city": "Storm Zone (Demo)",
            "source": "mock",
        }

    try:
        w = _fetch_owm_weather(lat, lon)

        rain_1h = 0.0
        if "rain" in w and "1h" in w["rain"]:
            rain_1h = float(w["rain"]["1h"])

        temp_c = w.get("main", {}).get("temp", 0.0)
        humidity = w.get("main", {}).get("humidity", 0)
        desc = w.get("weather", [{}])[0].get("description", "N/A").title()
        city = w.get("name", "Unknown")

        aqi = _fetch_owm_aqi(lat, lon)

        return {
            "rain_1h": round(rain_1h, 2),
            "aqi": aqi,
            "temp_c": round(temp_c, 1),
            "humidity": humidity,
            "description": desc,
            "city": city,
            "source": "live",
        }

    except Exception as e:
        print(f"[Oracle] OWM API error: {e}")
        return {
            "rain_1h": 0.0,
            "aqi": 100,
            "temp_c": 0.0,
            "humidity": 0,
            "description": "API unavailable",
            "city": "Offline",
            "source": "fallback",
        }


# ─── Legacy trigger (kept for backward compat) ───────────────────────────────

def evaluate_trigger(weather_data: dict) -> bool:
    if MOCK_MODE_FORCE_TRIGGER:
        return True
    rain_1h = weather_data.get("rain_1h", 0.0)
    aqi = weather_data.get("aqi", 0)
    if rain_1h > 10.0 or aqi > 400:
        return True
    return False
