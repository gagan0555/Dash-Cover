import os
import pickle
import pandas as pd
from datetime import datetime

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
MODEL_PATH = os.path.join(MODEL_DIR, "xgboost_pricing.pkl")

pricing_model = None
if os.path.exists(MODEL_PATH):
    with open(MODEL_PATH, "rb") as f:
        pricing_model = pickle.load(f)

def calculate_weekly_premium(base_premium: float = 25.0, zone_risk_multiplier: float = 1.0, coverage_tier_multiplier: float = 1.4) -> float:
    """
    Calculate the weekly premium based on actuarial simulation logic.
    Formula: Premium = Base Premium * Zone Risk Multiplier * Coverage Tier Multiplier
    
    As validated in the actuarial simulation, targeting a Loss Ratio < 0.70.
    """
    return round(base_premium * zone_risk_multiplier * coverage_tier_multiplier, 2)

def determine_zone_risk_multiplier(zone_id: str) -> float:
    """
    Determine zone risk multiplier using the XGBoost pricing model based on zone_id.
    """
    zone_str = zone_id.lower()
    
    # Feature extraction defaults based on zone_id
    zone_type = 1 # Medium risk
    hist_disruptions = 5
    avg_duration = 3.0
    
    if "high" in zone_str or "monsoon" in zone_str or "red" in zone_str:
        zone_type = 2
        hist_disruptions = 12
        avg_duration = 6.0
    elif "low" in zone_str or "safe" in zone_str:
        zone_type = 0
        hist_disruptions = 2
        avg_duration = 1.5

    if pricing_model is not None:
        try:
            current_month = datetime.now().month
            X = pd.DataFrame({
                "zone_type": [zone_type],
                "historical_disruptions": [hist_disruptions],
                "avg_duration": [avg_duration],
                "month": [current_month]
            })
            pred = pricing_model.predict(X)[0]
            # Ensure multiplier is bounded
            return round(max(0.8, min(1.5, float(pred))), 2)
        except Exception as e:
            print(f"Error predicting pricing: {e}")

    # Fallback baseline multipliers
    if zone_type == 2:
        return 1.5
    elif zone_type == 1:
        return 1.2
    return 0.8

