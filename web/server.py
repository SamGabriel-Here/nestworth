"""FastAPI backend for the NestWorth web app — serves the model and the frontend."""

from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
STATIC = Path(__file__).resolve().parent / "static"

model = joblib.load(ROOT / "models" / "house_price_model.pkl")
interval = joblib.load(ROOT / "models" / "prediction_interval.pkl")
data = pd.read_csv(ROOT / "data" / "housing_clean.csv")
metrics = pd.read_csv(ROOT / "reports" / "model_comparison.csv")
R2 = float(metrics.iloc[0]["R2"])

NUMERIC_RAW = ["area", "bedrooms", "bathrooms", "stories", "house_age", "parking"]
CATEGORICAL_RAW = ["city", "location", "main_road", "furnishing_status"]

FACTOR_LABELS = {
    "area": lambda v: f"Area · {int(v):,} sq ft",
    "city": lambda v: f"City · {v}",
    "location": lambda v: f"Location · {v}",
    "bedrooms": lambda v: f"Bedrooms · {int(v)}",
    "bathrooms": lambda v: f"Bathrooms · {int(v)}",
    "stories": lambda v: f"Stories · {int(v)}",
    "house_age": lambda v: f"Age · {int(v)} yrs",
    "parking": lambda v: f"Parking · {int(v)}",
    "main_road": lambda v: f"Main road · {v}",
    "furnishing_status": lambda v: f"Furnishing · {v}",
}

BASELINE = {c: data[c].mode()[0] for c in CATEGORICAL_RAW}
for _c in NUMERIC_RAW:
    BASELINE[_c] = int(round(data[_c].median()))
BASELINE["area"] = float(data["area"].median())


def build_input(raw: dict) -> pd.DataFrame:
    row = pd.DataFrame([raw])
    row["total_rooms"] = row["bedrooms"] + row["bathrooms"]
    row["is_new"] = (row["house_age"] <= 5).astype(int)
    return row


def prediction_interval(input_df, point):
    lo = interval["lo"].predict(input_df)[0] - interval["q"]
    hi = interval["hi"].predict(input_df)[0] + interval["q"]
    lo, hi = min(lo, hi), max(lo, hi)
    lo, hi = min(lo, point), max(hi, point)
    return max(float(lo), 0.0), float(hi)


def segment_stats(city, location):
    seg = data[(data["city"] == city) & (data["location"] == location)]
    if len(seg) < 8:
        seg = data[data["city"] == city]
    if len(seg) < 8:
        return None
    low, mid, high = seg["price"].quantile([0.10, 0.50, 0.90])
    return float(low), float(mid), float(high), len(seg)


def explain(raw, full_pred, top=5):
    factors = []
    for feat, label_fn in FACTOR_LABELS.items():
        probe = dict(raw)
        probe[feat] = BASELINE[feat]
        delta = full_pred - float(model.predict(build_input(probe))[0])
        factors.append({"label": label_fn(raw[feat]), "delta": delta})
    factors.sort(key=lambda x: abs(x["delta"]), reverse=True)
    return factors[:top]


def comparables(city, location, area, k=5):
    seg = data[(data["city"] == city) & (data["location"] == location)]
    if len(seg) < k:
        seg = data[data["city"] == city]
    if seg.empty:
        return []
    seg = seg.assign(_d=(seg["area"] - area).abs()).sort_values("_d").head(k)
    out = []
    for _, r in seg.iterrows():
        out.append({
            "desc": f"{int(r['area']):,} sq ft · {int(r['bedrooms'])} BHK · {int(r['house_age'])} yrs",
            "price": float(r["price"]),
        })
    return out


class PropertyIn(BaseModel):
    area: int
    bedrooms: int
    bathrooms: int
    stories: int
    city: str
    location: str
    house_age: int
    parking: int
    main_road: str
    furnishing_status: str


app = FastAPI(title="NestWorth")


@app.post("/api/predict")
def api_predict(p: PropertyIn):
    raw = p.model_dump()
    x = build_input(raw)
    estimate = float(model.predict(x)[0])
    lo, hi = prediction_interval(x, estimate)
    stats = segment_stats(raw["city"], raw["location"])
    return {
        "estimate": estimate,
        "price_per_sqft": estimate / raw["area"],
        "r2": R2,
        "interval": {"lo": lo, "hi": hi, "coverage": int(interval["coverage"] * 100)},
        "segment": (
            {"low": stats[0], "mid": stats[1], "high": stats[2], "n": stats[3]}
            if stats else None
        ),
        "factors": explain(raw, estimate),
        "comparables": comparables(raw["city"], raw["location"], raw["area"]),
    }


app.mount("/", StaticFiles(directory=str(STATIC), html=True), name="static")
