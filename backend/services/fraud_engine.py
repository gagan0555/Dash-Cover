"""
Dash-Cover Fraud Engine — Trust Composite Score (TCS) (ML Edition)
==================================================================
Multi-signal behavioral anomaly scoring system powered by Isolation Forest.

Scoring Components:
  - GPS Drift Distance (m) — derived from Haversine vs Alert Zone
  - Claims Frequency — number of recent claims this week
  - Speed/Activity Profile (0=Stationary, 1=Low-Speed, 2=Moving, 3=High-Speed)

Resolution Tiers (from README Section 8.3 & ML Architecture 7.3):
  - TCS >= 0.75      ->  AUTO-APPROVED
  - TCS 0.40 - 0.74   ->  SOFT REVIEW (FLAG FOR REVIEW)
  - TCS < 0.40       ->  HOLD & INVESTIGATE (REJECT)
"""

import os
import math
import pickle
import numpy as np
from typing import Tuple

# ─── Constants ───────────────────────────────────────────────────────────────

EARTH_RADIUS_KM = 6371.0

# Pre-load Models globally to optimize API response times
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
MODEL_PATH = os.path.join(MODEL_DIR, "isolation_forest.pkl")
SCALER_PATH = os.path.join(MODEL_DIR, "scaler.pkl")

clf = None
scaler = None

if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
    with open(MODEL_PATH, "rb") as f:
        clf = pickle.load(f)
    with open(SCALER_PATH, "rb") as f:
        scaler = pickle.load(f)


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


def encode_activity(activity_status: str) -> int:
    """
    Transforms string status into numeric for ML.
      - 'Stationary'  -> 0
      - 'Low-Speed'   -> 1
      - 'Moving'      -> 2
      - 'High-Speed'  -> 3
    """
    status = activity_status.lower().strip()
    score_map = {
        "stationary": 0,
        "low-speed": 1,
        "moving": 2,
        "high-speed": 3,
    }
    return score_map.get(status, 2)  # Default moving


# ─── Mock Claims Tracker ────────────────────────────────────────────────────

_mock_claims_tracker: dict[str, int] = {}

def get_claims_this_week(worker_id: str) -> int:
    """Retrieve the number of claims filed by a worker this week."""
    # In full production this queries Supabase:
    # select count(*) from claims where worker_id=X and timestamp > week_start
    return _mock_claims_tracker.get(worker_id, 0)

def record_claim(worker_id: str) -> None:
    _mock_claims_tracker[worker_id] = _mock_claims_tracker.get(worker_id, 0) + 1

def reset_weekly_claims() -> None:
    _mock_claims_tracker.clear()


# ─── ML TCS Calculator ──────────────────────────────────────────────────────

def calculate_trust_score(
    worker_id: str,
    current_lat: float,
    current_lon: float,
    activity_status: str,
    alert_lat: float,
    alert_lon: float,
) -> dict:
    """
    Calculate the Trust Composite Score (TCS) using the pretrained Isolation Forest.
    """
    distance_km = round(haversine_distance(current_lat, current_lon, alert_lat, alert_lon), 2)
    distance_m = distance_km * 1000.0
    
    claims_this_week = get_claims_this_week(worker_id)
    speed_encoded = encode_activity(activity_status)

    # If models are missing (e.g. not trained yet), fallback to extremely basic logic
    if clf is None or scaler is None:
        trust_score = 0.5
        recommendation = "Flag for Review"
        raw_anomaly = 0.0
    else:
        # Build feature vector
        X = np.array([[distance_m, claims_this_week, speed_encoded]])
        X_scaled = scaler.transform(X)

        # Output range is usually roughly -0.5 (strong anomaly) to 0.5 (very normal) for IsolationForest
        # We need to map it neatly into a 0.0 - 1.0 Trust Composite Score
        raw_anomaly = clf.decision_function(X_scaled)[0]
        
        # Sigmoid-like scale mapping to push scores to bounds 0-1
        # Shifting and scaling heuristic to fit standard ML outcomes nicely:
        tcs_val = 1.0 / (1.0 + np.exp(-10 * raw_anomaly))
        trust_score = round(float(tcs_val), 4)

    # Resolution tier (README Section 8.3)
    if trust_score >= 0.75:
        recommendation = "Approve"
    elif trust_score >= 0.40:
        recommendation = "Flag for Review"
    else:
        recommendation = "Reject"

    return {
        "trust_score": trust_score,
        "recommendation": recommendation,
        "breakdown": {
            "ml_raw_anomaly_score": round(float(raw_anomaly), 4),
            "features": {
                "distance_m": distance_m,
                "claims": claims_this_week,
                "speed_encoded": speed_encoded
            }
        },
        "distance_km": distance_km,
        "claims_this_week": claims_this_week,
    }
