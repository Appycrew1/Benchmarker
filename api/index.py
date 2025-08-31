\
from fastapi import FastAPI, Query
from typing import List, Dict
import math, random, statistics

app = FastAPI(title="Moving Benchmark + Choropleth — MVP Plus (No DB)")

# ---------- Seed areas & metrics ----------
AREAS = [
    {"code":"E1","name":"Whitechapel","lat":51.517,"lng":-0.059},
    {"code":"SE1","name":"Southwark","lat":51.503,"lng":-0.091},
    {"code":"SW11","name":"Battersea","lat":51.464,"lng":-0.163},
    {"code":"W2","name":"Paddington","lat":51.515,"lng":-0.187},
    {"code":"NW3","name":"Hampstead","lat":51.555,"lng":-0.175},
    {"code":"N1","name":"Islington","lat":51.536,"lng":-0.103},
    {"code":"EC1","name":"Clerkenwell","lat":51.524,"lng":-0.109},
    {"code":"WC2","name":"Covent Garden","lat":51.512,"lng":-0.124}
]
BASE = {
    "E1":  {"demand":78,"comp":55,"rate":98,"rev":4.5,"close":33,"ont":92,"job":520},
    "SE1": {"demand":73,"comp":47,"rate":102,"rev":4.4,"close":31,"ont":93,"job":560},
    "SW11":{"demand":80,"comp":52,"rate":108,"rev":4.3,"close":28,"ont":94,"job":590},
    "W2":  {"demand":68,"comp":60,"rate":95,"rev":4.6,"close":34,"ont":91,"job":500},
    "NW3": {"demand":62,"comp":42,"rate":110,"rev":4.2,"close":27,"ont":95,"job":640},
    "N1":  {"demand":70,"comp":58,"rate":97,"rev":4.5,"close":33,"ont":90,"job":510},
    "EC1": {"demand":65,"comp":53,"rate":100,"rev":4.4,"close":30,"ont":92,"job":540},
    "WC2": {"demand":77,"comp":45,"rate":112,"rev":4.3,"close":29,"ont":93,"job":610}
}

# Simulated competitor prices per area for "watch" & pricing logic
COMP_PRICES = { k: [max(60, min(150, BASE[k]["rate"] + random.randint(-15, 15))) for _ in range(6)]
    for k in BASE.keys()
}
# Simulated ad intensity signals (0-100) per area (marketing optimizer)
AD_INTENSITY = { k: random.randint(30, 85) for k in BASE.keys() }

def intensity(d, c):
    return max(0.0, min(1.0, (d - c + 50) / 100.0))

def area_avg_price(code):
    return statistics.mean(COMP_PRICES.get(code, [BASE[code]["rate"]]))

# Build very simple square-ish polygons around centroids (demo only)
def make_square(lat, lng, dlat=0.01, dlng=0.02):
    return [[lng-dlng, lat-dlat],[lng+dlng, lat-dlat],[lng+dlng, lat+dlat],[lng-dlng, lat+dlat],[lng-dlng, lat-dlat]]

def feature_for_area(a):
    code = a["code"]
    m = BASE[code]
    score = m["demand"] - m["comp"]  # used for choropleth color scale
    geom = {"type":"Polygon","coordinates":[make_square(a["lat"], a["lng"])]}
    props = {"area_code":code,"name":a["name"],"demand":m["demand"],"competition":m["comp"],
             "avg_hourly_rate":m["rate"],"avg_review_score":m["rev"],"close_rate":m["close"],
             "on_time":m["ont"],"avg_job_value":m["job"],"score":score}
    return {"type":"Feature","geometry":geom,"properties":props}

@app.get("/api/geojson")
def geojson():
    return {"type":"FeatureCollection","features":[feature_for_area(a) for a in AREAS]}

# ---------- Core endpoints ----------
@app.get("/api/areas")
def areas():
    return AREAS

@app.get("/api/heatmap")
def heatmap():  # kept for compatibility; no longer used by UI
    return [[a["lat"], a["lng"], intensity(BASE[a["code"]]["demand"], BASE[a["code"]]["comp"])] for a in AREAS]

@app.get("/api/metrics")
def metrics(area_code: str = Query(...)):
    if area_code not in BASE: return {"error": "not found"}
    m = BASE[area_code]
    return {
        "area_code": area_code,
        "demand_index": m["demand"],
        "competition_index": m["comp"],
        "avg_hourly_rate": m["rate"],
        "avg_review_score": m["rev"],
        "close_rate_pct": m["close"],
        "on_time_pct": m["ont"],
        "avg_job_value": m["job"],
        "competitor_avg_rate": round(area_avg_price(area_code), 1)
    }

@app.get("/api/benchmark")
def benchmark(area_code: str, your_hourly_rate: float = 0.0, your_review_score: float = 0.0):
    data = metrics(area_code)
    if "error" in data: return data
    return {
        "area_code": area_code,
        "area_avg": {
            "hourly_rate": data["avg_hourly_rate"],
            "review_score": data["avg_review_score"],
            "close_rate_pct": data["close_rate_pct"],
            "on_time_pct": data["on_time_pct"],
            "avg_job_value": data["avg_job_value"]
        },
        "your_vs_area": {
            "hourly_rate_diff": (your_hourly_rate - data["avg_hourly_rate"]) if your_hourly_rate else None,
            "review_score_diff": (your_review_score - data["avg_review_score"]) if your_review_score else None
        }
    }

@app.get("/api/insights")
def insights(area_code: str):
    data = metrics(area_code)
    if "error" in data: return data
    tips = []
    if data["avg_hourly_rate"]>100: tips.append("Premium pricing area; test discounts or bundle packing.")
    if data["demand_index"]>70 and data["competition_index"]<50: tips.append("High demand + low competition; boost ads here.")
    if data["avg_review_score"]<4.5: tips.append("Reviews under 4.5★; automate post-job review requests.")
    return {"area_code": area_code, "insights": tips}

# ---------- A) Predictive Demand Forecasting ----------
@app.get("/api/forecast")
def forecast(area_code: str, horizon_days: int = 30):
    if area_code not in BASE: return {"error":"not found"}
    base_d = BASE[area_code]["demand"]
    out = []
    for i in range(horizon_days):
        seasonal = 5 * math.sin((i/7)*2*math.pi)  # weekly
        trend = (i / 60.0) * 3
        noise = random.uniform(-2, 2)
        val = max(0, min(100, base_d + seasonal + trend + noise))
        out.append({"day": i+1, "forecast_demand": round(val,1)})
    return {"area_code": area_code, "points": out}

# ---------- B) Dynamic Pricing Recommendations ----------
@app.get("/api/pricing")
def pricing(area_code: str):
    if area_code not in BASE: return {"error":"not found"}
    m = BASE[area_code]
    comp_avg = area_avg_price(area_code)
    demand, comp, your = m["demand"], m["comp"], m["rate"]
    pressure = (demand - comp) / 100.0
    target = comp_avg * (1 + 0.15 * pressure)
    delta_pct = (target - your) / your
    rec = {
        "current_rate": your,
        "competitor_avg_rate": round(comp_avg,1),
        "recommended_rate": round(target, 1),
        "change_pct": round(delta_pct * 100, 1),
        "rationale": "High demand and/or lower competition allows a premium; aligned towards competitor average."
                      if pressure>0 else "Lower demand or higher competition suggests staying closer to competitor average."
    }
    return {"area_code": area_code, "pricing": rec}

# ---------- C) Competitor Watch Alerts ----------
@app.get("/api/competitor_watch")
def competitor_watch(area_code: str):
    if area_code not in BASE: return {"error":"not found"}
    prices = COMP_PRICES[area_code]
    new_price = max(60, min(150, BASE[area_code]["rate"] + random.randint(-15, 15)))
    prices2 = prices[1:] + [new_price]
    COMP_PRICES[area_code] = prices2

    prev_avg = round(statistics.mean(prices[:-1]), 1)
    latest = prices2[-1]
    delta = latest - prices[-1]
    alert = None
    if abs(delta) >= 10:
        alert = f"Competitor price {'decrease' if delta<0 else 'increase'} of £{abs(delta)} detected."
    return {
        "area_code": area_code,
        "history": prices2,
        "latest": latest,
        "prev_avg": prev_avg,
        "alert": alert
    }

# ---------- D) Lead Intelligence Scoring ----------
@app.get("/api/lead_score")
def lead_score(area_code: str, est_job_value: float = 500.0, your_review_score: float = 4.3):
    if area_code not in BASE: return {"error":"not found"}
    m = BASE[area_code]
    v = min(1000.0, max(100.0, est_job_value))
    v_norm = (v - 100.0) / (1000.0 - 100.0) * 100.0
    demand_signal = m["demand"] - m["comp"] + 50.0
    review_bonus = (your_review_score - 4.0) * 10.0
    score = max(0.0, min(100.0, 0.5*v_norm + 0.3*demand_signal + 0.2*review_bonus))
    reason = []
    if v > 600: reason.append("High potential job value.")
    if m["demand"] > m["comp"]: reason.append("Favorable demand vs competition.")
    if your_review_score >= 4.5: reason.append("Strong reputation fit.")
    return {"area_code": area_code, "lead_score": round(score,1), "reasons": reason}

# ---------- E) Marketing Optimisation ----------
@app.get("/api/marketing")
def marketing():
    ranked = []
    for a in AREAS:
        code = a["code"]
        m = BASE[code]
        roi_proxy = (m["demand"] - m["comp"]) - (AD_INTENSITY[code] - 50)
        ranked.append({
            "area_code": code,
            "roi_proxy": round(roi_proxy,1),
            "suggested_action": "Increase" if roi_proxy>0 else "Reduce",
            "note": f"Demand {m['demand']} vs Comp {m['comp']}; Ad intensity {AD_INTENSITY[code]}"
        })
    ranked.sort(key=lambda x: x["roi_proxy"], reverse=True)
    return {"ranking": ranked}
