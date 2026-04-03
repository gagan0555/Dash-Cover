def calculate_weekly_premium(base_premium: float = 25.0, zone_risk_multiplier: float = 1.0, coverage_tier_multiplier: float = 1.4) -> float:
    """
    Calculate the weekly premium based on actuarial simulation logic.
    Formula: Premium = Base Premium * Zone Risk Multiplier * Coverage Tier Multiplier
    
    As validated in the actuarial simulation, targeting a Loss Ratio < 0.70.
    """
    return round(base_premium * zone_risk_multiplier * coverage_tier_multiplier, 2)

def determine_zone_risk_multiplier(zone_id: str) -> float:
    """
    Mock logic to determine zone risk multiplier based on zone_id.
    In a production system, this calls our ML pricing model (XGBoost).
    """
    zone_str = zone_id.lower()
    if "high" in zone_str or "monsoon" in zone_str or "red" in zone_str:
        return 1.5
    elif "med" in zone_str or "yellow" in zone_str:
        return 1.2
    elif "low" in zone_str or "safe" in zone_str:
        return 0.8
    # Default baseline multiplier
    return 1.0
