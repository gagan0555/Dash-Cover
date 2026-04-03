import os

# Global toggle for demo presentations to always fire a payout
MOCK_MODE_FORCE_TRIGGER = os.getenv("MOCK_MODE_FORCE_TRIGGER", "False").lower() in ("true", "1", "yes")

# Active storm state for the demo
# NOTE: In production, weather state comes from external APIs, not in-memory globals.
# For multi-worker uvicorn deployments, use Redis or a shared store instead.
STORM_MODE_ACTIVE = False

def set_storm_mode(active: bool):
    global STORM_MODE_ACTIVE
    STORM_MODE_ACTIVE = active

def get_weather_data(lat: float, lon: float) -> dict:
    """
    Simulates a call to OpenWeatherMap's 'One Call 3.0' API.
    Returns deterministic data based on STORM_MODE_ACTIVE.
    """
    if STORM_MODE_ACTIVE:
        return {
            "rain_1h": 25.5,   # Intense heavy rain (mm/hr) — triggers rain threshold
            "aqi": 85,         # Normal AQI — storm ≠ pollution, these are separate events
        }
    else:
        return {
            "rain_1h": 1.2,    # Normal light rain
            "aqi": 85,         # Normal AQI
        }

def evaluate_trigger(weather_data: dict) -> bool:
    """
    Evaluates whether the weather conditions meet the parametric trigger thresholds.

    Parametric Trigger Thresholds (aligned with README §5):
      - Intense hourly rain: rain_1h > 10.0 mm/hr
        (IMD Red Alert intensity: 64.5mm/day sustained over ~6hr peak ≈ 10.75mm/hr)
      - Hazardous air quality: aqi > 400 (CPCB Hazardous category)

    Returns: True if either condition is met (trigger activated), else False.
    """
    if MOCK_MODE_FORCE_TRIGGER:
        return True

    rain_1h = weather_data.get("rain_1h", 0.0)
    aqi = weather_data.get("aqi", 0)

    if rain_1h > 10.0 or aqi > 400:
        return True

    return False
