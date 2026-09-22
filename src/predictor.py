"""Load the trained artifacts once; turn one property into a full valuation."""

import joblib
import pandas as pd

from src.pipeline.prepare import CATEGORICAL_COLS, CLEAN_DATA_PATH, NUMERIC_COLS, ROOT

ARTIFACTS = ROOT / "artifacts"
model = joblib.load(ARTIFACTS / "model.pkl")
interval = joblib.load(ARTIFACTS / "interval.pkl")
data = pd.read_csv(CLEAN_DATA_PATH)
R2 = float(pd.read_csv(ARTIFACTS / "metrics.csv").iloc[0]["R2"])

# A "typical listing": each feature's contribution is measured against it.
BASELINE = ({c: data[c].mode()[0] for c in CATEGORICAL_COLS}
            | {c: round(data[c].median()) for c in NUMERIC_COLS}
            | {"area": float(data["area"].median())})

LABELS = {
    "area": lambda v: f"Area · {int(v):,} sq ft",
    "city": lambda v: f"City · {v}",
    "location": lambda v: f"Locality · {v}",
    "bedrooms": lambda v: f"Bedrooms · {v}",
    "bathrooms": lambda v: f"Bathrooms · {v}",
    "stories": lambda v: f"Stories · {v}",
    "house_age": lambda v: f"Age · {v} yrs",
    "parking": lambda v: f"Parking · {v}",
    "main_road": lambda v: f"Main road · {v}",
    "furnishing_status": lambda v: f"Furnishing · {v}",
}


def _predict(raw: dict) -> float:
    return float(model.predict(pd.DataFrame([raw]))[0])


def value(raw: dict) -> dict:
    x = pd.DataFrame([raw])
    estimate = float(model.predict(x)[0])
    lo = interval["lo"].predict(x)[0] - interval["q"]
    hi = interval["hi"].predict(x)[0] + interval["q"]
    lo, hi = max(min(lo, hi, estimate), 0.0), max(lo, hi, estimate)

    seg = data[(data["city"] == raw["city"]) & (data["location"] == raw["location"])]
    if len(seg) < 8:
        seg = data[data["city"] == raw["city"]]
    low, mid, high = seg["price"].quantile([0.10, 0.50, 0.90])

    # Single-feature ablation: reset one feature to typical, see how the price moves.
    factors = sorted(
        ({"label": LABELS[f](raw[f]), "delta": estimate - _predict({**raw, f: BASELINE[f]})}
         for f in LABELS),
        key=lambda f: -abs(f["delta"]))[:5]

    comps = seg.assign(_d=(seg["area"] - raw["area"]).abs()).nsmallest(5, "_d")
    return {
        "estimate": estimate,
        "price_per_sqft": estimate / raw["area"],
        "r2": R2,
        "interval": {"lo": float(lo), "hi": float(hi),
                     "coverage": round(interval["coverage"] * 100)},
        "segment": {"low": float(low), "mid": float(mid), "high": float(high), "n": len(seg)},
        "factors": factors,
        "comparables": [
            {"area": int(r.area), "bedrooms": int(r.bedrooms), "age": int(r.house_age),
             "price": float(r.price)}
            for r in comps.itertuples()],
    }
