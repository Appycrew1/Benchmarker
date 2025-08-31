from fastapi import FastAPI, Query

app = FastAPI(title="Moving Benchmark + Heatmap — MVP (No DB)")

SEED = [
    {"code":"E1","name":"Whitechapel","lat":51.517,"lng":-0.059},
    {"code":"SE1","name":"Southwark","lat":51.503,"lng":-0.091},
    {"code":"SW11","name":"Battersea","lat":51.464,"lng":-0.163},
    {"code":"W2","name":"Paddington","lat":51.515,"lng":-0.187},
    {"code":"NW3","name":"Hampstead","lat":51.555,"lng":-0.175},
    {"code":"N1","name":"Islington","lat":51.536,"lng":-0.103},
    {"code":"EC1","name":"Clerkenwell","lat":51.524,"lng":-0.109},
    {"code":"WC2","name":"Covent Garden","lat":51.512,"lng":-0.124}
]
METRICS = {
    "E1":  {"demand":78,"comp":55,"rate":98,"rev":4.5,"close":33,"ont":92,"job":520},
    "SE1": {"demand":73,"comp":47,"rate":102,"rev":4.4,"close":31,"ont":93,"job":560},
    "SW11":{"demand":80,"comp":52,"rate":108,"rev":4.3,"close":28,"ont":94,"job":590},
    "W2":  {"demand":68,"comp":60,"rate":95,"rev":4.6,"close":34,"ont":91,"job":500},
    "NW3": {"demand":62,"comp":42,"rate":110,"rev":4.2,"close":27,"ont":95,"job":640},
    "N1":  {"demand":70,"comp":58,"rate":97,"rev":4.5,"close":33,"ont":90,"job":510},
    "EC1": {"demand":65,"comp":53,"rate":100,"rev":4.4,"close":30,"ont":92,"job":540},
    "WC2": {"demand":77,"comp":45,"rate":112,"rev":4.3,"close":29,"ont":93,"job":610}
}

@app.get("/api/areas")
def areas():
    return SEED

@app.get("/api/heatmap")
def heatmap():
    def intensity(d,c): return max(0,min(100,d-c+50))/100.0
    return [[a["lat"],a["lng"],intensity(METRICS[a["code"]]["demand"], METRICS[a["code"]]["comp"])] for a in SEED]

@app.get("/api/metrics")
def metrics(area_code: str = Query(...)):
    if area_code not in METRICS: return {"error":"not found"}
    m = METRICS[area_code]
    return {"area_code":area_code,"demand_index":m["demand"],"competition_index":m["comp"],
            "avg_hourly_rate":m["rate"],"avg_review_score":m["rev"],
            "close_rate_pct":m["close"],"on_time_pct":m["ont"],"avg_job_value":m["job"]}

@app.get("/api/benchmark")
def benchmark(area_code: str, your_hourly_rate: float = 0.0, your_review_score: float = 0.0):
    data = metrics(area_code)
    if "error" in data: return data
    return {"area_code":area_code,
            "area_avg":{"hourly_rate":data["avg_hourly_rate"],"review_score":data["avg_review_score"],
                        "close_rate_pct":data["close_rate_pct"],"on_time_pct":data["on_time_pct"],"avg_job_value":data["avg_job_value"]},
            "your_vs_area":{"hourly_rate_diff": (your_hourly_rate - data["avg_hourly_rate"]) if your_hourly_rate else None,
                            "review_score_diff": (your_review_score - data["avg_review_score"]) if your_review_score else None}}

@app.get("/api/insights")
def insights(area_code: str):
    data = metrics(area_code)
    if "error" in data: return data
    tips = []
    if data["avg_hourly_rate"]>100: tips.append("Premium pricing area; test discounts or bundle packing.")
    if data["demand_index"]>70 and data["competition_index"]<50: tips.append("High demand + low competition; boost ads here.")
    if data["avg_review_score"]<4.5: tips.append("Reviews under 4.5★; automate review requests.")
    return {"area_code":area_code, "insights": tips}
