"""Load the trained artifacts once; turn one property into a full valuation."""

import joblib
import numpy as np
import pandas as pd

from src.pipeline.prepare import CATEGORICAL_COLS, CLEAN_DATA_PATH, NUMERIC_COLS, ROOT

ARTIFACTS = ROOT / "artifacts"
model = joblib.load(ARTIFACTS / "model.pkl")
interval = joblib.load(ARTIFACTS / "interval.pkl")
data = pd.read_csv(CLEAN_DATA_PATH)
best = pd.read_csv(ARTIFACTS / "metrics.csv").iloc[0]  # rows are sorted by R2, best first
R2, MAE = float(best["R2"]), float(best["MAE"])
CITIES = sorted(data["city"].unique())
OPTIONS = {c: sorted(data[c].unique()) for c in CATEGORICAL_COLS}

# A "typical listing" for the numbers: each one's contribution is measured against its median.
BASELINE = {c: round(data[c].median()) for c in NUMERIC_COLS} | {"area": float(data["area"].median())}

LABELS = {
    "area": lambda v: f"Area · {int(v):,} sq ft",
    "city": lambda v: f"City · {v}",
    "location": lambda v: f"Locality · {v}",
    "property_type": lambda v: f"Type · {v}",
    "bedrooms": lambda v: f"Bedrooms · {v}",
    "bathrooms": lambda v: f"Bathrooms · {v}",
    "stories": lambda v: f"Floors · {v}",
    "house_age": lambda v: f"Age · {v} yrs",
    "parking": lambda v: f"Parking · {v}",
    "main_road": lambda v: f"Main road · {v}",
    "furnishing_status": lambda v: f"Furnishing · {v}",
}


def _predict(rows: list[dict]) -> np.ndarray:
    return model.predict(pd.DataFrame(rows))


def _range(rows: list[dict], estimate: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Conformal 90% bounds, ordered around the estimate and never below zero."""
    x = pd.DataFrame(rows)
    lo = interval["lo"].predict(x) - interval["q"]
    hi = interval["hi"].predict(x) + interval["q"]
    return np.maximum(np.minimum.reduce([lo, hi, estimate]), 0.0), np.maximum.reduce([lo, hi, estimate])


def _segment(raw: dict) -> pd.DataFrame:
    """Listings like this one: same city, locality and type, widening until there are enough."""
    same = (data["city"] == raw["city"]) & (data["property_type"] == raw["property_type"])
    for mask in (same & (data["location"] == raw["location"]), same, data["city"] == raw["city"]):
        if mask.sum() >= 8:
            return data[mask]
    return data


def value(raw: dict) -> dict:
    estimate = float(_predict([raw])[0])
    lo, hi = (float(v[0]) for v in _range([raw], np.array([estimate])))

    seg = _segment(raw)
    low, mid, high = seg["price"].quantile([0.10, 0.50, 0.90])

    # Single-feature ablation: swap one feature for a typical value and see how the price moves.
    # Numbers reset to the median; a category is compared with the average over all its options,
    # so the most common city or type is not reported as adding nothing.
    probes, owner = [], []
    for f in LABELS:
        options = OPTIONS[f] if f in OPTIONS else [BASELINE[f]]
        probes += [{**raw, f: o} for o in options]
        owner += [f] * len(options)
    typical = pd.Series(_predict(probes)).groupby(owner).mean()
    factors = sorted(
        ({"label": LABELS[f](raw[f]), "delta": estimate - float(typical[f])} for f in LABELS),
        key=lambda f: -abs(f["delta"]))[:5]

    # The same home at other sizes: where extra area stops paying.
    top = min(9000, max(1500, raw["area"] * 2.5))
    areas = sorted({*np.linspace(300, top, 24).round(-1), float(raw["area"])})
    sized = [{**raw, "area": a} for a in areas]
    curve_est = _predict(sized)
    curve_lo, curve_hi = _range(sized, curve_est)

    # The same home in every city.
    elsewhere = _predict([{**raw, "city": c} for c in CITIES])

    comps = seg.assign(_d=(seg["area"] - raw["area"]).abs()).nsmallest(5, "_d")
    return {
        "estimate": estimate,
        "price_per_sqft": estimate / raw["area"],
        "r2": R2,
        "mae": MAE,
        "interval": {"lo": lo, "hi": hi, "coverage": round(interval["coverage"] * 100)},
        "segment": {"low": float(low), "mid": float(mid), "high": float(high), "n": len(seg)},
        "factors": factors,
        "comparables": [
            {"area": int(r.area), "bedrooms": int(r.bedrooms), "age": int(r.house_age),
             "type": r.property_type, "price": float(r.price)}
            for r in comps.itertuples()],
        "curve": [{"area": float(a), "estimate": float(e), "lo": float(l), "hi": float(h)}
                  for a, e, l, h in zip(areas, curve_est, curve_lo, curve_hi)],
        "cities": sorted(({"city": c, "estimate": float(e)} for c, e in zip(CITIES, elsewhere)),
                         key=lambda c: -c["estimate"]),
    }
