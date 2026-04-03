"""
Dash-Cover Fraud Engine — Trust Composite Score (TCS)
=====================================================
Multi-signal behavioral fingerprint scoring system.

Scoring Breakdown (Total: 1.0):
  - Location Match:   0.50  (worker within 5km of affected weather station)
  - Behavioral Check: 0.30  (activity coherence with weather conditions)
  - Frequency Cap:    0.20  (claim frequency within acceptable bounds)

Resolution Tiers (from README Section 8.3):
  - TCS >= 0.75  ->  AUTO-APPROVED
  - TCS 0.40-0.74 -> SOFT REVIEW (FLAG FOR REVIEW)
  - TCS < 0.40   ->  HOLD & INVESTIGATE (REJECT)
"""

import math
from typing import Tuple

# ─── Constants ───────────────────────────────────────────────────────────────

LOCATION_WEIGHT = 0.50
BEHAVIOR_WEIGHT = 0.30
FREQUENCY_WEIGHT = 0.20

MAX_PROXIMITY_KM = 5.0          # must be within 5km of the alert zone
MAX_WEEKLY_CLAIMS = 2            # more than 2 claims/week is suspicious
EARTH_RADIUS_KM = 6371.0


# ─── Helpers ─────────────────────────────────────────────────────────────────

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance (km) between two GPS coordinates
    using the Haversine formula.
    """
    lat1_r, lon1_r = math.radians(lat1), math.radians(lon1)
    lat2_r, lon2_r = math.radians(lat2), math.radians(lon2)

    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return EARTH_RADIUS_KM * c


# ─── Scoring Components ─────────────────────────────────────────────────────

def score_location_match(
    worker_lat: float,
    worker_lon: float,
    alert_lat: float,
    alert_lon: float,
) -> float:
    """
    Location Match Score (0.0 - 1.0).

    Full score (1.0) if worker is within MAX_PROXIMITY_KM of the weather station
    reporting the Red Alert. Score decays linearly to 0.0 at 3x the threshold.
    """
    distance_km = haversine_distance(worker_lat, worker_lon, alert_lat, alert_lon)

    if distance_km <= MAX_PROXIMITY_KM:
        return 1.0
    elif distance_km <= MAX_PROXIMITY_KM * 3:
        # Linear decay from 1.0 to 0.0 between 5km and 15km
        return max(0.0, 1.0 - (distance_km - MAX_PROXIMITY_KM) / (MAX_PROXIMITY_KM * 2))
    else:
        return 0.0


def score_behavioral_check(activity_status: str) -> float:
    """
    Behavioral Coherence Score (0.0 - 1.0).

    During extreme weather, a genuine worker should be stationary (sheltering).
    Movement patterns that contradict the weather event are flagged.

    Activity statuses and their scores:
      - 'Stationary'  -> 1.0  (sheltering, consistent with disruption)
      - 'Low-Speed'   -> 0.7  (walking/parking bike, plausible)
      - 'Moving'      -> 0.4  (ambiguous — could be seeking shelter)
      - 'High-Speed'  -> 0.1  (in a car/bus, not a bike rider — suspicious)
    """
    status = activity_status.lower().strip()

    score_map = {
        "stationary": 1.0,
        "low-speed": 0.7,
        "moving": 0.4,
        "high-speed": 0.1,
    }

    return score_map.get(status, 0.5)  # unknown defaults to neutral


def score_frequency_cap(claims_this_week: int) -> float:
    """
    Frequency Cap Score (0.0 - 1.0).

    Workers who have claimed more than MAX_WEEKLY_CLAIMS this week
    receive a reduced score. Score decays with each additional claim.

    0 claims -> 1.0
    1 claim  -> 1.0
    2 claims -> 1.0  (at the cap)
    3 claims -> 0.5  (one over — yellow flag)
    4+ claims -> 0.0 (pattern abuse — red flag)
    """
    if claims_this_week <= MAX_WEEKLY_CLAIMS:
        return 1.0
    elif claims_this_week == MAX_WEEKLY_CLAIMS + 1:
        return 0.5
    else:
        return 0.0


# ─── Mock Claims Tracker ────────────────────────────────────────────────────

# In production, this queries Supabase for the worker's claim history this week.
_mock_claims_tracker: dict[str, int] = {}


def get_claims_this_week(worker_id: str) -> int:
    """Retrieve the number of claims filed by a worker this week (mock)."""
    return _mock_claims_tracker.get(worker_id, 0)


def record_claim(worker_id: str) -> None:
    """Record a new claim for the worker (mock)."""
    _mock_claims_tracker[worker_id] = _mock_claims_tracker.get(worker_id, 0) + 1


def reset_weekly_claims() -> None:
    """Clear all weekly claim counts (call at the start of each new week)."""
    _mock_claims_tracker.clear()


# ─── Main TCS Calculator ────────────────────────────────────────────────────

def calculate_trust_score(
    worker_id: str,
    current_lat: float,
    current_lon: float,
    activity_status: str,
    alert_lat: float,
    alert_lon: float,
) -> dict:
    """
    Calculate the Trust Composite Score (TCS) for a claim event.

    Args:
        worker_id:       Unique identifier for the delivery worker.
        current_lat:     Worker's current GPS latitude.
        current_lon:     Worker's current GPS longitude.
        activity_status: One of 'Stationary', 'Low-Speed', 'Moving', 'High-Speed'.
        alert_lat:       Latitude of the weather station reporting the Red Alert.
        alert_lon:       Longitude of the weather station reporting the Red Alert.

    Returns:
        dict with:
          - trust_score (float):       Weighted composite score 0.0 - 1.0
          - recommendation (str):      'Approve', 'Flag for Review', or 'Reject'
          - breakdown (dict):          Individual component scores and weights
          - distance_km (float):       Actual distance from alert zone
          - claims_this_week (int):    Current weekly claim count
    """
    # Score each component
    loc_score = score_location_match(current_lat, current_lon, alert_lat, alert_lon)
    beh_score = score_behavioral_check(activity_status)
    claims_this_week = get_claims_this_week(worker_id)
    freq_score = score_frequency_cap(claims_this_week)

    # Weighted composite
    trust_score = round(
        (loc_score * LOCATION_WEIGHT)
        + (beh_score * BEHAVIOR_WEIGHT)
        + (freq_score * FREQUENCY_WEIGHT),
        4,
    )

    # Resolution tier (README Section 8.3)
    if trust_score >= 0.75:
        recommendation = "Approve"
    elif trust_score >= 0.40:
        recommendation = "Flag for Review"
    else:
        recommendation = "Reject"

    distance_km = round(
        haversine_distance(current_lat, current_lon, alert_lat, alert_lon), 2
    )

    return {
        "trust_score": trust_score,
        "recommendation": recommendation,
        "breakdown": {
            "location_match": {"score": round(loc_score, 4), "weight": LOCATION_WEIGHT},
            "behavioral_check": {"score": round(beh_score, 4), "weight": BEHAVIOR_WEIGHT},
            "frequency_cap": {"score": round(freq_score, 4), "weight": FREQUENCY_WEIGHT},
        },
        "distance_km": distance_km,
        "claims_this_week": claims_this_week,
    }
