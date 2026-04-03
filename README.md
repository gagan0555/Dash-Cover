# 🛵 Dash-Cover — AI-Powered Parametric Income Insurance for Q-Commerce Delivery Partners

> **Guidewire DEVTrails 2026 | Team [ByteForge]**
> Persona: Grocery - Blinkit / Zepto

---

## 📌 Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [Our Solution](#2-our-solution)
3. [Persona & Scenario Walkthrough](#3-persona--scenario-walkthrough)
4. [How it's built](#4-how-it's-built)
5. [Parametric Triggers](#5-parametric-triggers)
6. [Weekly Premium Model](#6-weekly-premium-model)
7. [AI/ML Architecture](#7-aiml-architecture)
8. [Adversarial Defense & Anti-Spoofing Strategy](#8-adversarial-defense--anti-spoofing-strategy)
9. [Tech Stack](#9-tech-stack)
10. [Platform Choice: Why Web?](#10-platform-choice-why-web)
11. [Development Plan](#11-development-plan)

---

## 1. Problem Statement

India's Q-Commerce delivery partners (Blinkit, Zepto) operate in a high-pressure environment where they have to deliver groceries and essentials within just 10–20 minutes , Unlike food delivery where they have a leeway of 40 to 45 mins or e commerce/online shopping platforms where they have a leeway of more than an hour(not considering ther Flipkart minutes) . Also Q-Commerce workers often operate across fixed dark-store zones for a specific area, making them especially vulnerable to disruptions like bad weather like heavy rainfall, severe heatwave or Bad AQI,etc.

When extreme weather hits, or a curfew is imposed, or air pollution crosses safe limits, these workers are **forced off the road with zero income protection**. They lose 20–30% of monthly earnings to events that are entirely outside of their control, with no insurance available.

**Dash-Cover** is built to change that.

---

## 2. Our Solution

Dash-Cover is an **AI-enabled parametric income insurance platform** that is designed exclusively for Q-Commerce delivery partners. It provides:

- Payout hits your UPI before you even think to file a claim — we detect the disruption, you get paid
- Weekly premium adjusts based on your zone's actual risk, not a flat rate someone guessed
- Fraud detection that catches bad actors without punishing honest riders stuck in a storm
- Income loss only — we don't cover your bike, your health, or anything else. Just your lost wages.

> **Coverage Scope:** Lost working hours/wages only, caused by verified external disruptions.

---

## 3. Persona & Scenario Walkthrough

### 👤 Primary Persona: Ravi, Blinkit Delivery Partner, Delhi NCR

- He works 8–10 hours/day, 6 days/week out of a Blinkit dark store in Ghaziabad
- He earns approximately ₹600–₹900/day
- He operates on a week-to-week cash basis — a single disrupted day might mean skipped meals or missed rent
- No employer benefits, no sick leave, no safety net

### 🌧️ Scenario 1 — Heavy Rain Event

A sudden IMD red-alert rainfall hits Ghaziabad and Blinkit suspends deliveries for 6 hours. Ravi cannot work and doesn't get any incentive for lost hours from Blinkit. **Dash-Cover automatically detects the trigger**,and it verifies against Ravi's zone and active policy, and initiates a payout for lost hours — And there is no need for ravi to file any form or anything.

### 🌫️ Scenario 2 — Severe Pollution (AQI > 400)

Delhi's AQI breaches the hazardous threshold. Local authorities advise against outdoor activity. Ravi's app goes quiet. **Dash-Cover AQI monitor flags the event**, cross-validates it against delivery platform activity data in Ravi's zone, and processes an income compensation payout.

### 🚫 Scenario 3 — Unplanned Curfew / Local Strike

A sudden Section 144 order or a local market strike blocks Ravi's delivery zone. **Dash-Cover social disruption monitor** (fed by mock news/government alert APIs) detects the event and triggers a payout for affected hours.

---

## 4. How it's built

```
┌─────────────────────────────────────────────────────────┐
│                     GIGSHIELD PLATFORM                  │
│                                                         │
│  [1] ONBOARDING                                         │
│      └── Worker registers with phone, zone, platform    │
│          (Blinkit/Zepto), avg. weekly earnings          │
│          └── AI generates risk profile for their zone   │
│                                                         │
│  [2] POLICY CREATION                                    │
│      └── ML model calculates weekly premium             │
│          based on zone risk score + earnings baseline   │
│      └── Worker selects coverage tier (Basic/Standard)  │
│      └── Weekly auto-deduction from earnings (simulated)│
│                                                         │
│  [3] REAL-TIME MONITORING (Background)                  │
│      └── Weather API (IMD / OpenWeatherMap)             │
│      └── AQI API (CPCB / IQAir)                        │
│      └── Traffic / curfew alert feeds (mock)            │
│      └── Platform delivery volume signals (mock)        │
│                                                         │
│  [4] PARAMETRIC TRIGGER FIRED                           │
│      └── System checks: Is worker's zone affected ?      │
│      └── Is worker's policy active this week?           │
│      └── Fraud engine validates claim (see Section 8)   │
│                                                         │
│  [5] AUTOMATED PAYOUT                                   │
│      └── Payout = (hourly earnings × disrupted hours)   │
│      └── Credited via UPI / mock payment gateway        │
│                                                         │
│  [6] DASHBOARD                                          │
│      └── Worker: Weekly coverage, earnings protected    │
│      └── Admin: Loss ratios, fraud flags, zone risk map │
└─────────────────────────────────────────────────────────┘
```

---

## 5. Parametric Triggers

All triggers are **objective, third-party verifiable data points** — no subjective claim filing required.

| # | Trigger | Data Source | Threshold | Income Impact |
|---|---------|-------------|-----------|---------------|
| 1 | Heavy Rain / Flood | IMD API / OpenWeatherMap | Rainfall > 64.5 mm/day (Red Alert) OR standing water reports | Deliveries halted in zone |
| 2 | Extreme Heat | OpenWeatherMap | Temperature > 45°C + Heat Index advisory | Unsafe outdoor conditions |
| 3 | Severe Air Pollution | CPCB AQI API / IQAir | AQI > 400 (Hazardous) | Health advisory, outdoor work unsafe |
| 4 | Unplanned Curfew | Govt. alert feed (mock) | Section 144 / emergency order in worker's zone | Zone inaccessible |
| 5 | Local Strike / Market Closure | News API (mock) | Verified strike affecting pickup/drop zones | Pickup locations inaccessible |

> **Important:** A trigger payout is only initiated when the disruption is verified AND the worker's zone is confirmed as affected. Workers outside the disruption zone are **not** eligible for that event.

---

## 6. Weekly Premium Model

Q-Commerce workers operate week-to-week, so GigShield's entire financial model is structured on a **7-day  cycle**.

### Premium Calculation Logic

```
Weekly Premium = Base Rate × Zone Risk Multiplier × Coverage Tier Multiplier

Where:
  Base Rate         = ₹25/week (floor price, reviewed quarterly)
  Zone Risk Multiplier = ML-generated score (0.8x – 1.5x) based on:
                         - Historical disruption frequency in the pin code
                         - Seasonal weather risk (monsoon vs. winter)
                         - Flood/waterlogging susceptibility score
  Coverage Tier:
    Basic     → 1.0x  → Covers up to ₹300/disrupted day
    Standard  → 1.4x  → Covers up to ₹600/disrupted day
```

### Example Scenarios

| Worker Zone | Tier | Zone Risk | Weekly Premium | Max Daily Payout |
|-------------|------|-----------|----------------|-----------------|
| Ghaziabad (flood-prone) | Standard | 1.3x | ₹45/week | ₹600 |
| South Delhi (low risk) | Basic | 0.85x | ₹21/week | ₹300 |
| Gurugram (moderate) | Standard | 1.1x | ₹38/week | ₹600 |

### Payout Formula

```
Payout Amount = (Worker's Avg Hourly Earning) × (Disrupted Hours in Zone) × Coverage Tier Cap

Disrupted Hours = Time window confirmed by trigger API for the worker's specific zone
```

---

## 7. AI/ML Architecture

### 7.1 ML-Based Dynamic Premium Pricing

- **Model Type:** Gradient Boosted Regressor (XGBoost / scikit-learn)
- **Training Data:** Historical IMD weather data, CPCB AQI logs, pin-code level disruption history (public datasets), district flood maps
- **Features:** Pin code, month/season, historical claim rate for zone, average disruption hours/year
- **Output:** Zone Risk Score (0.8 – 1.5) used to adjust the base weekly premium
- **Update Cycle:** Re-scored weekly using fresh weather/AQI trend data

### 7.2 Rule-Based Trigger Validation

Before any payout is initiated, a lightweight rule engine runs the following checks:
- Worker's registered zone matches the disruption zone
- Policy was active and premium paid for the current week
- Disruption duration meets minimum threshold (e.g., ≥ 2 hours for weather events)
- No duplicate claim already processed for the same event window

### 7.3 Anomaly Detection for Fraud (see full strategy in Section 8)

- **Model Type:** Isolation Forest + statistical Z-score profiling
- **Purpose:** Detect abnormal claim patterns, coordinated fraud rings, and GPS signal anomalies
- **Triggers review** when behavioural signals deviate significantly from the worker's own historical baseline

---

## 8. Adversarial Defense & Anti-Spoofing Strategy

> ⚠️ **Critical Security Update — Phase 1 Addendum**
> In response to the DEVTrails threat advisory: a coordinated syndicate of 500 delivery workers exploited a beta parametric platform using GPS-spoofing apps to fake locations inside red-alert weather zones and drain the liquidity pool. GigShield's architecture is designed from the ground up to defeat this class of attack.

---

### 8.1 The Differentiation — Genuine Stranded Worker vs. Bad Actor

GigShield does **not** rely on GPS as a primary trust signal. Instead, we build a **multi-signal behavioral fingerprint** for every worker and every claim event. A genuine worker caught in a disruption will produce a consistent, corroborating pattern of signals. A GPS spoofer will not.

The core insight: **GPS can be faked. Behaviour cannot be faked at scale, consistently, across all signals simultaneously.**

Our system computes a **Trust Composite Score (TCS)** for every claim event, combining the following signals:

| Signal Layer | Genuine Worker (Expected) | Spoofer (Red Flag) |
|---|---|---|
| Platform Activity Drop | Blinkit/Zepto order volume drops sharply in the zone during the event | Worker claims disruption but platform shows normal order flow in their zone |
| Device Sensor Coherence | Accelerometer + gyroscope shows device stationary or minimal movement (sheltering) | Spoofer app may show GPS movement inconsistency vs. static device sensors |
| Historical Behavioral Baseline | Worker's activity pattern during past disruptions matches current claim | First-ever claim filed precisely during a red-alert event with no prior history |
| Network Cell Tower Triangulation | Cell tower data (approximate) corroborates GPS-reported location | GPS reports a flood zone but cell tower triangulation places device at home |
| Claim Timing vs. Trigger Onset | Claim auto-triggered by system; worker doesn't need to "file" manually | In manual-claim systems, spoofers file within seconds of an alert — GigShield has no manual filing |
| Peer Cluster Analysis | Workers in the same zone show similar inactivity patterns | A suspicious cluster of workers all registered to the same pin code all simultaneously claiming from the same event |

---

### 8.2 The Data — Beyond GPS Coordinates

All of the following signals are fed into an Isolation Forest anomaly detection model to calculate the final Trust Composite Score.

Our fraud detection layer ingests the following data points to detect coordinated rings:


**Individual-Level Signals**
- Device sensor data: accelerometer, gyroscope, battery drain rate (high GPS spoofing apps drain battery abnormally fast)
- App session metadata: screen-on time, interaction patterns during claimed disruption window
- Historical claim frequency and claim-to-active-days ratio
- Onboarding verification: Blinkit/Zepto worker ID cross-reference (simulated), KYC linkage

**Zone-Level & Aggregate Signals**
- Delivery platform order volume in the worker's dark-store zone (mock API) — a genuine disruption will suppress orders platform-wide; spoofed claims will appear during normal order volumes
- Number of simultaneous claims from the same pin code vs. historical baseline for that zone
- Network graph analysis: workers sharing the same device fingerprint, referral chain, or registration IP address flagged as a potential syndicate cluster
- IMD / AQI data granularity check: We validate the weather event against the **specific ward/pin code**, not just the city level. A city-level red alert does not automatically cover every pin code — hyperlocal validation prevents broad spoofing

**Temporal Signals**
- Claim onset time vs. API trigger time — our system auto-initiates claims, so any manually-submitted claim is itself a red flag
- Duration of claimed disruption vs. official event window from APIs

---

### 8.3 The UX Balance — Flagged Claims Without Penalizing Honest Workers

We recognize that bad weather also causes genuine network drops, GPS drift, and connectivity issues. Our flagging system is designed to **never auto-deny** a claim — it escalates for lightweight review instead.

**Three-Tier Claim Resolution:**

```
┌─────────────────────────────────────────────────────────┐
│               CLAIM RESOLUTION TIERS                    │
│                                                         │
│  🟢 AUTO-APPROVED (TCS ≥ 0.75)                         │
│     └── All signals corroborate. Payout in < 2 minutes  │
│         No worker action needed.                        │
│                                                         │
│  🟡 SOFT REVIEW (TCS 0.40 – 0.74)                      │
│     └── System sends worker a single WhatsApp/SMS       │
│         prompt: "Are you currently unable to deliver    │
│         due to [event]? Reply YES to confirm."          │
│     └── On confirmation → payout proceeds               │
│     └── No documents, no forms, no proof uploads        │
│     └── Resolved within 10 minutes                      │
│                                                         │
│  🔴 HOLD & INVESTIGATE (TCS < 0.40)                    │
│     └── Claim held for 24-hour review                   │
│     └── Worker notified: "Your claim is being           │
│         verified. You'll hear back within 24 hours."    │
│     └── Human reviewer + automated report generated     │
│     └── If cleared → payout + ₹10 inconvenience credit │
│     └── If fraud confirmed → policy suspended,          │
│         flagged in the system                           │
└─────────────────────────────────────────────────────────┘
```

**Key UX Principles for Honest Workers:**
- **No proof uploads ever.** A genuine worker will never be asked to photograph flooded roads or upload documents.
- **Innocent until proven otherwise.** A low TCS score means "needs a second look," not "fraud confirmed." Workers are never penalized based on a score alone.
- **Transparent communication.** Workers are told exactly what the system is checking and why, in plain Hindi/English via SMS.
- **Network drop protection:** If a genuine worker experiences a network drop during a disruption (common in heavy rain), their claim is still auto-triggered by the server-side event monitor — their device being offline does **not** void their claim.
- **Appeal mechanism:** Any held or denied claim can be appealed via a simple in-app button. Appeals are reviewed within 48 hours.

---

## 9. Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vanilla React (via Vite) + Tailwind CSS |
| Backend | Python / FastAPI |
| Database | Supabase  |
| ML / AI | scikit-learn (XGBoost for pricing, Isolation Forest for fraud) |
| Weather API | OpenWeatherMap (free tier) / IMD mock |
| AQI API | CPCB / IQAir (free tier) |
| Alert Feed | Mock REST APIs for curfew/strike events |
| Payment (Mock) | Razorpay Test Mode / UPI Simulator |
| Hosting | Render / Railway (free tier for hackathon) |
| Version Control | GitHub |

---

## 10. Platform Choice: Why Web?

We chose a **Web App** over a native mobile app for the following reasons:

- **Zero installation friction** — delivery workers can access via any smartphone browser without downloading an app; critical for adoption in a low-storage-device demographic
- **Admin dashboard** — the insurer-facing analytics panel is best suited to a web interface, allowing side-by-side use on desktop by operations teams
- **PWA-ready** — the web app can be made installable as a Progressive Web App with offline support, matching mobile UX where needed

---

## 11. Development Plan

### Phase 1 (Weeks 1–2) — Ideation & Foundation ✅
- [x] Define persona and use cases (Blinkit/Zepto, Delhi NCR focus)
- [x] Define parametric triggers and premium model logic
- [x] Design system architecture and fraud defense strategy
- [x] Set up GitHub repo, FastAPI boilerplate, PostgreSQL schema
- [x] Build basic worker onboarding flow (frontend)

### Phase 2 (Weeks 3–4) — Automation & Disruption Implementation ✅
- [x] Integrate Three-Tier Claim Resolution engine (Auto-Approve, Soft Review, Hold & Investigate based on TCS)
- [x] Build Live Parametric Trigger APIs (Weather/Storm & AQI Mock Services)
- [x] Develop Modular Frontend Component Architecture (Status Ring, Live Telemetry Widget, Claims History)
- [x] Construct interactive Admin Dashboard (Real-time Loss Ratios, Worker Risk Metrics)
- [x] Implement Live Zone Risk Map with dynamic Geo-spatial Polygons displaying active disruption areas

### Phase 3 (Weeks 5–6) — Scale & Optimisation ⏳
- [ ] Transition from mock in-memory stores to persistent Supabase schema
- [ ] Connect production Weather (OpenWeatherMap) and CPCB AQI Live APIs
- [ ] Train and integrate XGBoost pricing model and Isolation Forest anomaly detection engine
- [ ] Implement Razorpay/UPI payout settlement gateway
- [ ] Deploy WhatsApp/SMS integration for "Soft Review" Tier 2 prompts

---

> **Dash-Cover** — *Because the last mile deserves a safety net.*
