from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
import uuid
import threading
import time
import os

from supabase_client import supabase

from services.pricing import calculate_weekly_premium, determine_zone_risk_multiplier
from services.oracle import get_weather_data, set_storm_mode, STORM_MODE_ACTIVE
from services.fraud_engine import calculate_trust_score, reset_weekly_claims, record_claim
from services.triggers import evaluate_all_triggers
import services.oracle as oracle_module
import services.alerts as alerts_module
from services.alerts import get_alert_data, set_curfew_mode, set_strike_mode

app = FastAPI(title="Dash-Cover Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_lock = threading.Lock()

def _gen_wid() -> str:
    return f"W{uuid.uuid4().hex[:6].upper()}"

def _record_claim_event(worker_id, status, amount, reason, tcs_score, tcs_breakdown, trigger_type, disrupted_hours):
    claim_id = f"CLM-{uuid.uuid4().hex[:8].upper()}"
    try:
        supabase.table("claims").insert({
            "id": claim_id,
            "worker_id": worker_id,
            "status": status,
            "amount": round(amount, 2),
            "reason": reason,
            "description": f"Trigger: {trigger_type}. Hours: {disrupted_hours}. Breakdowns: {tcs_breakdown}",
            "tcs_score": tcs_score,
        }).execute()
    except Exception as e:
        print(f"Error recording claim: {e}")


# ─── Background Auto-Polling (P2) ────────────────────────────────────────────
# Polls all workers every 60 seconds and auto-fires payouts when triggers are active.
# This delivers on the "automatic detection" promise without manual button presses.

def _background_poll():
    while True:
        time.sleep(60)
        try:
            r = supabase.table("workers").select("worker_id, lat, lon").execute()
            for w in r.data:
                try:
                    weather = get_weather_data(w["lat"], w["lon"])
                    alert = get_alert_data()
                    trigger = evaluate_all_triggers(weather, alert)
                    if trigger.triggered:
                        print(f"[AutoPoll] Trigger detected for {w['worker_id']}: {trigger.trigger_type}")
                        check_payout(w["worker_id"])
                except Exception as e:
                    print(f"[AutoPoll] {w['worker_id']}: {e}")
        except Exception as e:
            print(f"[AutoPoll] Poll error: {e}")

_poll_thread = threading.Thread(target=_background_poll, daemon=True)
_poll_thread.start()


# ─── Models ──────────────────────────────────────────────────────────────────

class EnrollmentRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., min_length=10, max_length=15)
    vehicle: str = Field(..., min_length=4, max_length=20)
    upi: str = Field(..., min_length=3, max_length=50)
    zone_id: str = Field(default="Delhi-NC-HighRisk")
    avg_daily_earnings: float = Field(default=800.0, gt=0, le=5000)  # P3: now sent from frontend
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
    return {"message": "Dash-Cover API is running (Supabase connected)."}


# P2/P3: Worker lookup endpoint — returns worker data + calculated premium for login flow
@app.get("/worker/{worker_id}")
def get_worker(worker_id: str):
    r = supabase.table("workers").select("*").eq("worker_id", worker_id).execute()
    if not r.data:
        raise HTTPException(status_code=404, detail="Worker not found")
    worker = r.data[0]
    zmult = determine_zone_risk_multiplier(worker["zone_id"])
    tmult = 1.4 if worker.get("coverage_tier", "Standard").lower() == "standard" else 1.0
    premium = calculate_weekly_premium(25.0, zmult, tmult)
    tier_cap = 600.0 if worker.get("coverage_tier", "Standard").lower() == "standard" else 300.0
    return {**worker, "weekly_premium": premium, "zone_risk_multiplier": zmult, "tier_cap": tier_cap}


@app.post("/enroll")
def enroll_worker(request: EnrollmentRequest):
    with _lock:
        worker_id = _gen_wid()
        zmult = determine_zone_risk_multiplier(request.zone_id)
        tmult = 1.0 if request.coverage_tier.lower() == "basic" else 1.4
        premium = calculate_weekly_premium(25.0, zmult, tmult)
        tier_cap = 600.0 if request.coverage_tier.lower() == "standard" else 300.0

        try:
            supabase.table("workers").insert({
                "worker_id": worker_id,
                "name": request.name,
                "phone": request.phone,
                "vehicle": request.vehicle,
                "upi": request.upi,
                "zone_id": request.zone_id,
                "avg_daily_earnings": request.avg_daily_earnings,
                "coverage_tier": request.coverage_tier,
                "lat": request.lat,
                "lon": request.lon,
                "behavior_profile": "genuine",
            }).execute()
        except Exception as e:
            print(e)
            raise HTTPException(status_code=500, detail=str(e))

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
    return {"status": "SUCCESS", "storm_active": active}

@app.post("/demo/set-curfew")
def toggle_curfew(active: bool):
    set_curfew_mode(active)
    if not active:
        reset_weekly_claims()
    return {"status": "SUCCESS", "curfew_active": active}

@app.post("/demo/set-strike")
def toggle_strike(active: bool):
    set_strike_mode(active)
    if not active:
        reset_weekly_claims()
    return {"status": "SUCCESS", "strike_active": active}


# P3: Seed W456 as a suspicious worker so the fraud demo button always works
@app.post("/demo/seed-fraud-worker")
def seed_fraud_worker():
    existing = supabase.table("workers").select("worker_id").eq("worker_id", "W456").execute()
    if existing.data:
        supabase.table("workers").update({"behavior_profile": "suspicious"}).eq("worker_id", "W456").execute()
        return {"status": "UPDATED", "worker_id": "W456"}

    supabase.table("workers").insert({
        "worker_id": "W456",
        "name": "Demo Fraud Worker",
        "phone": "9999999999",
        "vehicle": "DL01FR4UD",
        "upi": "fraud@demo",
        "zone_id": "Delhi-NC-HighRisk",
        "avg_daily_earnings": 800.0,
        "coverage_tier": "Standard",
        "lat": 28.6139,
        "lon": 77.2090,
        "behavior_profile": "suspicious",
    }).execute()
    return {"status": "CREATED", "worker_id": "W456"}


@app.get("/check-payout/{worker_id}")
def check_payout(worker_id: str):
    r = supabase.table("workers").select("*").eq("worker_id", worker_id).execute()
    if not r.data:
        raise HTTPException(status_code=404, detail=f"Worker '{worker_id}' not found.")
    worker = r.data[0]

    weather_data = get_weather_data(worker["lat"], worker["lon"])
    alert_data = get_alert_data()
    trigger_result = evaluate_all_triggers(weather_data, alert_data)

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

    today = datetime.now().date().isoformat()
    claims_req = supabase.table("claims")\
        .select("amount")\
        .eq("worker_id", worker_id)\
        .eq("status", "SUCCESS")\
        .gte("timestamp", today).execute()
    paid_today = sum(c["amount"] for c in claims_req.data)

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


@app.get("/demo/simulate-storm-trigger")
def backend_simulate_storm():
    r = supabase.table("workers").select("*").execute()
    workers = r.data
    triggers = 0
    payouts = 0.0
    for w in workers:
        res = check_payout(w["worker_id"])
        if res.get("status") in ("SUCCESS", "PENDING"):
            triggers += 1
            payouts += res.get("payout", res.get("pending_payout", 0))
    return {
        "status": "STORM_TRIGGERED",
        "affected_workers": len(workers),
        "claims_triggered": triggers,
        "total_payout_amount": payouts
    }


# ─── Claim History ───────────────────────────────────────────────────────────

@app.get("/claims/{worker_id}")
def get_claims(worker_id: str):
    r = supabase.table("claims").select("*").eq("worker_id", worker_id).order("timestamp", desc=True).execute()
    return {"worker_id": worker_id, "claims": r.data, "total_claims": len(r.data)}

@app.post("/demo/full-reset")
def full_reset(worker_id: str = None):
    set_storm_mode(False)
    set_curfew_mode(False)
    set_strike_mode(False)
    reset_weekly_claims()
    
    # Delete claims from Supabase too
    if worker_id:
        supabase.table("claims").delete().eq("worker_id", worker_id).execute()
    else:
        supabase.table("claims").delete().neq("id", "").execute()  # delete all
    
    return {"status": "FULL_RESET_OK"}

# ─── Weather ─────────────────────────────────────────────────────────────────

@app.get("/weather/current")
def get_current_weather(worker_id: str = None):
    lat, lon = 28.6139, 77.2090
    if worker_id:
        r = supabase.table("workers").select("lat, lon").eq("worker_id", worker_id).execute()
        if r.data:
            lat, lon = r.data[0]["lat"], r.data[0]["lon"]

    weather = get_weather_data(lat, lon)
    alert_data = get_alert_data()
    trigger = evaluate_all_triggers(weather, alert_data)
    return {
        "storm_active": oracle_module.STORM_MODE_ACTIVE,
        "curfew_active": alerts_module.CURFEW_MODE_ACTIVE,
        "strike_active": alerts_module.STRIKE_MODE_ACTIVE,
        "rain_1h": weather["rain_1h"],
        "aqi": weather["aqi"],
        "temp_c": weather.get("temp_c", 0),
        "humidity": weather.get("humidity", 0),
        "description": weather.get("description", ""),
        "city": weather.get("city", ""),
        "source": weather.get("source", "live"),
        "trigger_active": trigger.triggered,
        "trigger_reason": trigger.reason,
    }


# ─── Admin Endpoints ─────────────────────────────────────────────────────────

@app.get("/admin/stats")
def get_admin_stats():
    wr = supabase.table("workers").select("worker_id", count="exact").execute()
    w_count = wr.count if wr.count else 0

    cr = supabase.table("claims").select("*").execute()
    claims = cr.data
    total_paid = sum(c["amount"] for c in claims if c["status"] == "SUCCESS")

    total_premiums = 0.0
    w_full = supabase.table("workers").select("zone_id, coverage_tier").execute()
    for w in w_full.data:
        zm = determine_zone_risk_multiplier(w["zone_id"])
        tm = 1.4 if w.get("coverage_tier", "Standard").lower() == "standard" else 1.0
        total_premiums += calculate_weekly_premium(25.0, zm, tm)

    return {
        "total_workers": w_count,
        "total_claims": len(claims),
        "claims_approved": sum(1 for c in claims if c["status"] == "SUCCESS"),
        "claims_pending": sum(1 for c in claims if c["status"] == "PENDING"),
        "claims_denied": sum(1 for c in claims if c["status"] == "DENIED"),
        "total_payouts": round(total_paid, 2),
        "weekly_premiums": round(total_premiums, 2),
        "loss_ratio": round(total_paid / total_premiums, 4) if total_premiums > 0 else 0,
        "storm_active": oracle_module.STORM_MODE_ACTIVE,
        "curfew_active": alerts_module.CURFEW_MODE_ACTIVE,
        "strike_active": alerts_module.STRIKE_MODE_ACTIVE,
    }

@app.get("/admin/workers")
def get_admin_workers():
    w_res = supabase.table("workers").select("*").execute()
    c_res = supabase.table("claims").select("*").execute()

    claims_lookup = {}
    for c in c_res.data:
        claims_lookup.setdefault(c["worker_id"], []).append(c)

    workers_list = []
    for w in w_res.data:
        wid = w["worker_id"]
        wc = claims_lookup.get(wid, [])
        zm = determine_zone_risk_multiplier(w["zone_id"])
        tm = 1.4 if w.get("coverage_tier", "Standard").lower() == "standard" else 1.0
        wc.sort(key=lambda x: x["timestamp"])
        last_tcs = wc[-1]["tcs_score"] if wc and "tcs_score" in wc[-1] else None
        workers_list.append({
            "worker_id": wid, "name": w["name"], "zone_id": w["zone_id"],
            "coverage_tier": w.get("coverage_tier", "Standard"),
            "weekly_premium": calculate_weekly_premium(25.0, zm, tm),
            "behavior_profile": w.get("behavior_profile", "genuine"),
            "total_claims": len(wc),
            "approved_claims": sum(1 for c in wc if c["status"] == "SUCCESS"),
            "total_paid": round(sum(c["amount"] for c in wc if c["status"] == "SUCCESS"), 2),
            "last_tcs": last_tcs,
        })
    return {"workers": workers_list}

@app.get("/admin/claims")
def get_admin_claims():
    c_res = supabase.table("claims").select("*").order("timestamp", desc=True).execute()
    return {"claims": c_res.data, "total": len(c_res.data)}


# ─── Geocode & Zones ─────────────────────────────────────────────────────────

@app.get("/geocode")
def geocode(q: str):
    return {"results": oracle_module.geocode_location(q)}

@app.get("/admin/zones")
def get_admin_zones():
    storm = oracle_module.STORM_MODE_ACTIVE
    curfew = alerts_module.CURFEW_MODE_ACTIVE
    strike = alerts_module.STRIKE_MODE_ACTIVE

    w_res = supabase.table("workers").select("zone_id, lat, lon").execute()

    dynamic_zones = {}
    for w in w_res.data:
        zid = w["zone_id"]
        if zid not in dynamic_zones:
            lat, lon = w["lat"], w["lon"]
            poly = [[lat+0.05, lon-0.05],[lat+0.05, lon+0.05],[lat-0.05, lon+0.05],[lat-0.05, lon-0.05]]
            dynamic_zones[zid] = {
                "id": zid,
                "name": zid.replace("-", " ").replace("DynamicZone", "").strip(),
                "risk_multiplier": determine_zone_risk_multiplier(zid),
                "risk_level": "medium" if "MedRisk" in zid else ("high" if "HighRisk" in zid else "low"),
                "center": [lat, lon], "polygon": poly, "workers": 0
            }
        dynamic_zones[zid]["workers"] += 1

    if not dynamic_zones:
        dynamic_zones["Delhi-Demo"] = {
            "id": "Delhi-Demo", "name": "Delhi (Demo)",
            "risk_multiplier": 1.5, "risk_level": "high",
            "center": [28.6139, 77.2090],
            "polygon": [[28.66, 77.15],[28.66, 77.25],[28.56, 77.25],[28.56, 77.15]],
            "workers": 0
        }

    zones = []
    for zid, zdata in dynamic_zones.items():
        try:
            weather = get_weather_data(zdata["center"][0], zdata["center"][1])
            rain, aqi, temp, desc = weather.get("rain_1h",0), weather.get("aqi",0), weather.get("temp_c",0), weather.get("description","")
        except Exception:
            rain, aqi, temp, desc = 0, 0, 0, ""

        zdata["storm_active"] = storm and zdata["risk_level"] in ("high", "medium")
        zdata["curfew_active"] = curfew
        zdata["strike_active"] = strike
        zdata["weather"] = {"rain_1h": rain, "aqi": aqi, "temp_c": temp, "description": desc}
        zones.append(zdata)

    return {"zones": zones, "storm_active": storm}
