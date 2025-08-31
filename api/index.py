from fastapi import FastAPI, Query
import random, statistics, math

app = FastAPI(title="Moving Benchmark — Ultra Min")

AREAS = [
    {"code":"E1","name":"Whitechapel","lat":51.517,"lng":-0.059},
    {"code":"SE1","name":"Southwark","lat":51.503,"lng":-0.091},
    {"code":"SW11","name":"Battersea","lat":51.464,"lng":-0.163},
]

BASE = {
    "E1": {"demand":78,"comp":55,"rate":98,"rev":4.5,"close":33,"ont":92,"job":520},
    "SE1":{"demand":73,"comp":47,"rate":102,"rev":4.4,"close":31,"ont":93,"job":560},
    "SW11":{"demand":80,"comp":52,"rate":108,"rev":4.3,"close":28,"ont":94,"job":590},
}

def intensity(d,c): return max(0.0, min(1.0, (d - c + 50)/100.0))

@app.get("/api/areas")
def areas(): return AREAS

@app.get("/api/heatmap")
def heatmap():
    return [[a["lat"], a["lng"], intensity(BASE[a["code"]]["demand"], BASE[a["code"]]["comp"])] for a in AREAS]

@app.get("/api/metrics")
def metrics(area_code: str = Query(...)):
    if area_code not in BASE: return {"error":"not found"}
    m = BASE[area_code]
    return {"area_code":area_code,"demand_index":m["demand"],"competition_index":m["comp"],
            "avg_hourly_rate":m["rate"],"avg_review_score":m["rev"],
            "close_rate_pct":m["close"],"on_time_pct":m["ont"],"avg_job_value":m["job"]}
