"""
Dash-Cover Parametric Trigger Definitions
==========================================
Defines all supported parametric triggers and their evaluation logic.

Trigger Types (from README §5):
  1. Heavy Rain / Flood     — rain_1h > 10.0 mm/hr
  2. Extreme Heat           — temp_celsius > 45°C
  3. Severe Air Pollution   — AQI > 400
  4. Unplanned Curfew       — curfew_active flag from govt alert feed
  5. Local Strike           — strike_active flag from news feed
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class TriggerResult:
    """Result of evaluating a parametric trigger."""
    triggered: bool
    trigger_type: str
    reason: str
    severity: str       # "none" | "moderate" | "severe" | "critical"
    disrupted_hours: float = 0.0


# ─── Threshold Constants (aligned with README §5) ──────────────────────────

RAIN_THRESHOLD_MM_HR = 10.0       # IMD Red Alert equivalent intensity
HEAT_THRESHOLD_CELSIUS = 45.0     # Extreme heat advisory
AQI_THRESHOLD = 400               # CPCB Hazardous category
MIN_DISRUPTION_HOURS = 2.0        # Minimum event duration for eligibility


# ─── Individual Trigger Evaluators ──────────────────────────────────────────

def evaluate_rain_trigger(weather_data: dict) -> TriggerResult:
    """Check if rainfall exceeds the heavy rain threshold."""
    rain = weather_data.get("rain_1h", 0.0)
    if rain > RAIN_THRESHOLD_MM_HR:
        severity = "critical" if rain > 20.0 else "severe"
        hours = min(rain / 4.0, 10.0)
        return TriggerResult(
            triggered=True,
            trigger_type="Heavy Rainfall",
            reason=f"Heavy Rainfall detected ({rain}mm/hr)",
            severity=severity,
            disrupted_hours=max(hours, MIN_DISRUPTION_HOURS),
        )
    return TriggerResult(False, "Heavy Rainfall", "Rainfall within safe limits", "none")


def evaluate_heat_trigger(weather_data: dict) -> TriggerResult:
    """Check if temperature exceeds the extreme heat threshold."""
    temp = weather_data.get("temp_celsius", 0.0)
    if temp > HEAT_THRESHOLD_CELSIUS:
        severity = "critical" if temp > 48.0 else "severe"
        return TriggerResult(
            triggered=True,
            trigger_type="Extreme Heat",
            reason=f"Extreme Heat advisory ({temp}°C)",
            severity=severity,
            disrupted_hours=6.0,
        )
    return TriggerResult(False, "Extreme Heat", "Temperature within safe limits", "none")


def evaluate_aqi_trigger(weather_data: dict) -> TriggerResult:
    """Check if AQI exceeds the hazardous threshold."""
    aqi = weather_data.get("aqi", 0)
    if aqi > AQI_THRESHOLD:
        severity = "critical" if aqi > 500 else "severe"
        return TriggerResult(
            triggered=True,
            trigger_type="Hazardous AQI",
            reason=f"Hazardous AQI detected (AQI: {aqi})",
            severity=severity,
            disrupted_hours=8.0,
        )
    return TriggerResult(False, "Hazardous AQI", "AQI within safe limits", "none")


def evaluate_curfew_trigger(alert_data: dict) -> TriggerResult:
    """Check if an unplanned curfew is active in the zone."""
    if alert_data.get("curfew_active", False):
        return TriggerResult(
            triggered=True,
            trigger_type="Unplanned Curfew",
            reason=f"Section 144 / emergency order: {alert_data.get('curfew_reason', 'Government order')}",
            severity="critical",
            disrupted_hours=alert_data.get("curfew_duration_hours", 8.0),
        )
    return TriggerResult(False, "Unplanned Curfew", "No curfew active", "none")


def evaluate_strike_trigger(alert_data: dict) -> TriggerResult:
    """Check if a local strike or market closure is active."""
    if alert_data.get("strike_active", False):
        return TriggerResult(
            triggered=True,
            trigger_type="Local Strike",
            reason=f"Market closure / strike: {alert_data.get('strike_reason', 'Local disruption')}",
            severity="severe",
            disrupted_hours=alert_data.get("strike_duration_hours", 6.0),
        )
    return TriggerResult(False, "Local Strike", "No strike active", "none")


# ─── Composite Trigger Evaluation ──────────────────────────────────────────

def evaluate_all_triggers(
    weather_data: dict,
    alert_data: Optional[dict] = None,
) -> TriggerResult:
    """
    Evaluate all parametric triggers and return the most severe one that fired.
    Priority order: Curfew > AQI > Rain > Heat > Strike
    """
    if alert_data is None:
        alert_data = {}

    triggers = [
        evaluate_curfew_trigger(alert_data),
        evaluate_aqi_trigger(weather_data),
        evaluate_rain_trigger(weather_data),
        evaluate_heat_trigger(weather_data),
        evaluate_strike_trigger(alert_data),
    ]

    for result in triggers:
        if result.triggered:
            return result

    return TriggerResult(False, "None", "All conditions within safe limits", "none")
