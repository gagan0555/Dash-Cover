from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from services.pricing import calculate_weekly_premium, determine_zone_risk_multiplier
from services.oracle import get_weather_data, set_storm_mode, STORM_MODE_ACTIVE
from services.fraud_engine import calculate_trust_score, reset_weekly_claims, record_claim
from services.triggers import evaluate_all_triggers
from datetime import datetime
import threading
import services.oracle as oracle_module

app = FastAPI(title="Dash-Cover Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── In-Memory Stores ───────────────────────────────────────────────────────

_lock = threading.Lock()
_worker_store: dict = {
    "W123": {
        "name": "Ravi Kumar", "phone": "+91 98765 43210", "vehicle": "DL 01 AB 1234",
        "upi": "ravi@okaxis", "zone_id": "Delhi-NC-HighRisk",
        "avg_daily_earnings": 800.0, "coverage_tier": "Standard",
        "lat": 28.6139, "lon": 77.2090, "behavior_profile": "genuine",
    },
    "W456": {
        "name": "Suspicious Tester", "phone": "+91 91234 56789", "vehicle": "HR 26 CD 5678",
        "upi": "tester@upi", "zone_id": "Gurugram-MedRisk",
        "avg_daily_earnings": 1000.0, "coverage_tier": "Standard",
        "lat": 28.4595, "lon": 77.0266, "behavior_profile": "suspicious",
    },
}
_claims_store: list = []
_next_id = 1000


def _gen_wid() -> str:
    global _next_id
    wid = f"W{_next_id}"
    _next_id += 1
    return wid


def _record_claim_event(worker_id, status, amount, reason, tcs_score, tcs_breakdown, trigger_type, disrupted_hours):
    _claims_store.append({
        "id": f"CLM-{len(_claims_store) + 1:04d}",
        "worker_id": worker_id,
        "timestamp": datetime.now().isoformat(),
        "status": status,
        "amount": round(amount, 2),
        "reason": reason,
        "tcs_score": tcs_score,
        "tcs_breakdown": tcs_breakdown,
        "trigger_type": trigger_type,
        "disrupted_hours": disrupted_hours,
    })


# ─── Models ──────────────────────────────────────────────────────────────────

class EnrollmentRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., min_length=10, max_length=15)
    vehicle: str = Field(..., min_length=4, max_length=20)
    upi: str = Field(..., min_length=3, max_length=50)
    zone_id: str = Field(default="Delhi-NC-HighRisk")
    avg_daily_earnings: float = Field(default=800.0, gt=0, le=5000)
    coverage_tier: str = Field(default="Standard")
    lat: float = Field(default=28.6139, ge=-90, le=90)
    lon: float = Field(default=77.2090, ge=-180, le=180)

    @field_validator("coverage_tier")
    @classmethod
    def validate_tier(cls, v):
        if v.lower() not in ("basic", "standard"):
            raise ValueError('Must be "Basic" or "Standard"')
        return v


class PremiumRequest(BaseModel):
    zone_id: str = Field(..., min_length=1)
    avg_earnings: float = Field(..., gt=0, le=10000)
    coverage_tier: str = Field(default="Standard")

    @field_validator("coverage_tier")
    @classmethod
    def validate_tier(cls, v):
        if v.lower() not in ("basic", "standard"):
            raise ValueError('Must be "Basic" or "Standard"')
        return v


class PremiumResponse(BaseModel):
    weekly_premium: float
    zone_risk_multiplier: float
    base_premium: float


# ─── Worker Routes ───────────────────────────────────────────────────────────

@app.get("/")
def read_root():
    return {"message": "Dash-Cover API is running."}


@app.post("/enroll")
def enroll_worker(request: EnrollmentRequest):
    with _lock:
        worker_id = _gen_wid()
        _worker_store[worker_id] = {
            "name": request.name, "phone": request.phone,
            "vehicle": request.vehicle, "upi": request.upi,
            "zone_id": request.zone_id,
            "avg_daily_earnings": request.avg_daily_earnings,
            "coverage_tier": request.coverage_tier,
            "lat": request.lat, "lon": request.lon,
            "behavior_profile": "genuine",
        }
    zmult = determine_zone_risk_multiplier(request.zone_id)
    tmult = 1.0 if request.coverage_tier.lower() == "basic" else 1.4
    premium = calculate_weekly_premium(25.0, zmult, tmult)
    tier_cap = 600.0 if request.coverage_tier.lower() == "standard" else 300.0
    return {
        "status": "SUCCESS", "worker_id": worker_id, "name": request.name,
        "weekly_premium": premium, "coverage_tier": request.coverage_tier,
        "zone_id": request.zone_id, "zone_risk_multiplier": zmult, "tier_cap": tier_cap,
    }


@app.post("/calculate-premium", response_model=PremiumResponse)
def calculate_premium(request: PremiumRequest):
    zmult = determine_zone_risk_multiplier(request.zone_id)
    tmult = 1.0 if request.coverage_tier.lower() == "basic" else 1.4
    premium = calculate_weekly_premium(25.0, zmult, tmult)
    return PremiumResponse(weekly_premium=premium, zone_risk_multiplier=zmult, base_premium=25.0)


@app.post("/demo/set-storm")
def toggle_storm(active: bool):
    set_storm_mode(active)
    if not active:
        reset_weekly_claims()
        _claims_store.clear()
    return {"status": "SUCCESS", "storm_active": active}


@app.get("/check-payout/{worker_id}")
def check_payout(worker_id: str):
    worker = _worker_store.get(worker_id)
    if not worker:
        raise HTTPException(status_code=404, detail=f"Worker '{worker_id}' not found.")

    weather_data = get_weather_data(worker["lat"], worker["lon"])
    trigger_result = evaluate_all_triggers(weather_data)

    if not trigger_result.triggered:
        return {"status": "ACTIVE", "message": "Weather within safe limits."}

    bp = worker.get("behavior_profile", "genuine")
    if bp == "genuine":
        drift_lat, drift_lon, activity = 0.005, 0.005, "Stationary"
    elif bp == "suspicious":
        drift_lat, drift_lon, activity = 0.08, 0.08, "High-Speed"
    else:
        drift_lat, drift_lon, activity = 0.01, 0.01, "Low-Speed"

    tcs = calculate_trust_score(
        worker_id=worker_id,
        current_lat=worker["lat"] + drift_lat, current_lon=worker["lon"] + drift_lon,
        activity_status=activity,
        alert_lat=worker["lat"], alert_lon=worker["lon"],
    )

    hours = trigger_result.disrupted_hours
    raw_payout = (worker["avg_daily_earnings"] / 8.0) * hours
    tier = worker.get("coverage_tier", "Standard").lower()
    tier_cap = 600.0 if tier == "standard" else 300.0

    # ── Daily payout cap enforcement ──
    # A worker cannot receive more than their tier cap in a single day.
    today = datetime.now().date().isoformat()
    paid_today = sum(
        c["amount"] for c in _claims_store
        if c["worker_id"] == worker_id
        and c["status"] == "SUCCESS"
        and c["timestamp"].startswith(today)
    )
    remaining_cap = tier_cap - paid_today
    if remaining_cap <= 0:
        return {
            "status": "CAPPED",
            "message": f"Daily payout cap reached (₹{tier_cap}). Already paid ₹{paid_today} today.",
            "tier_cap": tier_cap,
            "paid_today": paid_today,
        }

    payout = round(min(raw_payout, remaining_cap), 2)
    reason = trigger_result.reason

    if tcs["recommendation"] == "Approve":
        record_claim(worker_id)
        _record_claim_event(worker_id, "SUCCESS", payout, reason, tcs["trust_score"], tcs["breakdown"], trigger_result.trigger_type, hours)
        return {"status": "SUCCESS", "payout": payout, "reason": reason, "tier_cap": tier_cap,
                "coverage_tier": worker.get("coverage_tier"), "disrupted_hours": hours,
                "tcs_score": tcs["trust_score"], "tcs_breakdown": tcs["breakdown"]}
    elif tcs["recommendation"] == "Flag for Review":
        record_claim(worker_id)
        _record_claim_event(worker_id, "PENDING", payout, reason, tcs["trust_score"], tcs["breakdown"], trigger_result.trigger_type, hours)
        return {"status": "PENDING", "message": "Manual Review Required.", "pending_payout": payout,
                "tcs_score": tcs["trust_score"], "tcs_breakdown": tcs["breakdown"]}
    else:
        _record_claim_event(worker_id, "DENIED", 0, reason, tcs["trust_score"], tcs["breakdown"], trigger_result.trigger_type, hours)
        return {"status": "DENIED", "message": f"TCS too low ({tcs['trust_score']}).",
                "tcs_score": tcs["trust_score"], "tcs_breakdown": tcs["breakdown"]}


# ─── Claim History ───────────────────────────────────────────────────────────

@app.get("/claims/{worker_id}")
def get_claims(worker_id: str):
    if worker_id not in _worker_store:
        raise HTTPException(status_code=404, detail=f"Worker '{worker_id}' not found.")
    claims = [c for c in _claims_store if c["worker_id"] == worker_id]
    return {"worker_id": worker_id, "claims": claims, "total_claims": len(claims)}


# ─── Weather ─────────────────────────────────────────────────────────────────

@app.get("/weather/current")
def get_current_weather():
    weather = get_weather_data(28.6139, 77.2090)
    trigger = evaluate_all_triggers(weather)
    return {
        "storm_active": oracle_module.STORM_MODE_ACTIVE,
        "rain_1h": weather["rain_1h"], "aqi": weather["aqi"],
        "trigger_fired": trigger.triggered,
        "trigger_type": trigger.trigger_type if trigger.triggered else None,
        "trigger_reason": trigger.reason, "trigger_severity": trigger.severity,
    }


# ─── Admin Routes ────────────────────────────────────────────────────────────

@app.get("/admin/stats")
def get_admin_stats():
    total_paid = sum(c["amount"] for c in _claims_store if c["status"] == "SUCCESS")
    total_premiums = 0.0
    for w in _worker_store.values():
        zm = determine_zone_risk_multiplier(w["zone_id"])
        tm = 1.4 if w.get("coverage_tier", "Standard").lower() == "standard" else 1.0
        total_premiums += calculate_weekly_premium(25.0, zm, tm)
    return {
        "total_workers": len(_worker_store),
        "total_claims": len(_claims_store),
        "claims_approved": sum(1 for c in _claims_store if c["status"] == "SUCCESS"),
        "claims_pending": sum(1 for c in _claims_store if c["status"] == "PENDING"),
        "claims_denied": sum(1 for c in _claims_store if c["status"] == "DENIED"),
        "total_payouts": round(total_paid, 2),
        "weekly_premiums": round(total_premiums, 2),
        "loss_ratio": round(total_paid / total_premiums, 4) if total_premiums > 0 else 0,
        "storm_active": oracle_module.STORM_MODE_ACTIVE,
    }


@app.get("/admin/workers")
def get_admin_workers():
    workers = []
    for wid, w in _worker_store.items():
        wc = [c for c in _claims_store if c["worker_id"] == wid]
        zm = determine_zone_risk_multiplier(w["zone_id"])
        tm = 1.4 if w.get("coverage_tier", "Standard").lower() == "standard" else 1.0
        workers.append({
            "worker_id": wid, "name": w["name"], "zone_id": w["zone_id"],
            "coverage_tier": w.get("coverage_tier", "Standard"),
            "weekly_premium": calculate_weekly_premium(25.0, zm, tm),
            "behavior_profile": w.get("behavior_profile", "genuine"),
            "total_claims": len(wc),
            "approved_claims": sum(1 for c in wc if c["status"] == "SUCCESS"),
            "total_paid": round(sum(c["amount"] for c in wc if c["status"] == "SUCCESS"), 2),
            "last_tcs": wc[-1]["tcs_score"] if wc else None,
        })
    return {"workers": workers}


@app.get("/admin/claims")
def get_admin_claims():
    return {"claims": list(reversed(_claims_store)), "total": len(_claims_store)}


@app.get("/admin/zones")
def get_admin_zones():
    zones = [
        {"id": "Delhi-NC-HighRisk", "name": "North Delhi (High Risk)", "risk_multiplier": 1.5,
         "risk_level": "high", "center": [28.7041, 77.1025],
         "polygon": [[28.75, 77.05], [28.75, 77.15], [28.68, 77.15], [28.68, 77.05]]},
        {"id": "Delhi-Central-MedRisk", "name": "Central Delhi (Medium)", "risk_multiplier": 1.2,
         "risk_level": "medium", "center": [28.6139, 77.2090],
         "polygon": [[28.65, 77.17], [28.65, 77.27], [28.58, 77.27], [28.58, 77.17]]},
        {"id": "Gurugram-MedRisk", "name": "Gurugram (Medium)", "risk_multiplier": 1.2,
         "risk_level": "medium", "center": [28.4595, 77.0266],
         "polygon": [[28.50, 76.97], [28.50, 77.08], [28.42, 77.08], [28.42, 76.97]]},
        {"id": "Noida-LowRisk", "name": "Noida (Low Risk)", "risk_multiplier": 0.8,
         "risk_level": "low", "center": [28.5355, 77.3910],
         "polygon": [[28.58, 77.35], [28.58, 77.43], [28.50, 77.43], [28.50, 77.35]]},
        {"id": "Ghaziabad-HighRisk", "name": "Ghaziabad (High Risk)", "risk_multiplier": 1.5,
         "risk_level": "high", "center": [28.6692, 77.4538],
         "polygon": [[28.71, 77.40], [28.71, 77.50], [28.63, 77.50], [28.63, 77.40]]},
    ]
    storm = oracle_module.STORM_MODE_ACTIVE
    for z in zones:
        z["workers"] = sum(1 for w in _worker_store.values() if z["id"].split("-")[0].lower() in w["zone_id"].lower())
        z["storm_active"] = storm and z["risk_level"] in ("high", "medium")
    return {"zones": zones, "storm_active": storm}
