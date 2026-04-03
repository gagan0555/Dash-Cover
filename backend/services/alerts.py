import os

# Global state for mock curfew and strike
CURFEW_MODE_ACTIVE = False
STRIKE_MODE_ACTIVE = False

def set_curfew_mode(active: bool):
    global CURFEW_MODE_ACTIVE
    CURFEW_MODE_ACTIVE = active

def set_strike_mode(active: bool):
    global STRIKE_MODE_ACTIVE
    STRIKE_MODE_ACTIVE = active

def get_alert_data() -> dict:
    return {
        "curfew_active": CURFEW_MODE_ACTIVE,
        "curfew_reason": "Section 144 / Emergency Order (Demo)" if CURFEW_MODE_ACTIVE else "",
        "curfew_duration_hours": 8.0 if CURFEW_MODE_ACTIVE else 0.0,
        "strike_active": STRIKE_MODE_ACTIVE,
        "strike_reason": "Local Market Strike (Demo)" if STRIKE_MODE_ACTIVE else "",
        "strike_duration_hours": 6.0 if STRIKE_MODE_ACTIVE else 0.0
    }
