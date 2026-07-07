"""Streamlit app for Bengaluru house price predictions."""

from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "house_price_model.pkl"
INTERVAL_PATH = ROOT / "models" / "prediction_interval.pkl"
METRICS_PATH = ROOT / "reports" / "model_comparison.csv"
DATA_PATH = ROOT / "data" / "housing_clean.csv"

NUMERIC_RAW = ["area", "bedrooms", "bathrooms", "balcony", "ready_to_move"]
CATEGORICAL_RAW = ["location", "area_type"]
AREA_TYPES = ["Super built-up Area", "Built-up Area", "Plot Area", "Carpet Area"]

FACTOR_LABELS = {
    "location": lambda v: f"Location · {v}",
    "area": lambda v: f"Area · {int(v):,} sq ft",
    "bedrooms": lambda v: f"Bedrooms · {int(v)} BHK",
    "bathrooms": lambda v: f"Bathrooms · {int(v)}",
    "balcony": lambda v: f"Balcony · {int(v)}",
    "area_type": lambda v: f"Type · {v}",
    "ready_to_move": lambda v: f"Status · {'Ready to move' if v else 'Under construction'}",
}

st.set_page_config(page_title="NestWorth", page_icon="🏠", layout="centered")

st.markdown(
    """
<style>
.nw-hero {
  background: linear-gradient(135deg, #1A2029 0%, #232C3A 100%);
  border: 1px solid #2A3542; border-radius: 16px;
  padding: 26px 24px; text-align: center; margin: 4px 0 6px;
}
.nw-hero-label {
  color: #8A93A5; font-size: 0.78rem; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.09em;
}
.nw-hero-price {
  color: #E6E9EF; font-weight: 700; line-height: 1.05;
  font-size: clamp(2.1rem, 8vw, 2.9rem); margin: 6px 0 4px;
}
.nw-hero-sub { color: #9AA4B4; font-size: 0.95rem; }
.nw-badge {
  display: inline-block; margin-top: 14px;
  background: rgba(91, 141, 239, 0.15); color: #8FB2F5;
  border: 1px solid rgba(91, 141, 239, 0.35); border-radius: 999px;
  padding: 4px 13px; font-size: 0.78rem; font-weight: 600;
}
.nw-bar-wrap { margin: 26px 0 2px; }
.nw-bar-track {
  position: relative; height: 10px; border-radius: 999px;
  background: linear-gradient(90deg, #2E7D5B 0%, #C9A227 55%, #C0563B 100%);
}
.nw-bar-marker {
  position: absolute; top: -5px; width: 3px; height: 20px;
  background: #E6E9EF; border-radius: 2px; box-shadow: 0 0 0 2px #0E1117;
}
.nw-bar-mark-label {
  position: absolute; top: -30px; transform: translateX(-50%);
  white-space: nowrap; background: #E6E9EF; color: #0E1117;
  font-size: 0.72rem; font-weight: 700; padding: 2px 8px; border-radius: 6px;
}
.nw-bar-ends {
  display: flex; justify-content: space-between;
  color: #8A93A5; font-size: 0.75rem; margin-top: 9px;
}
.nw-factor { margin: 10px 0; }
.nw-factor-top {
  display: flex; justify-content: space-between; align-items: baseline;
  font-size: 0.9rem;
}
.nw-factor-label { color: #C7CEDA; }
.nw-factor-val { font-weight: 700; font-variant-numeric: tabular-nums; }
.nw-factor-bar {
  height: 6px; border-radius: 999px; background: #171C24;
  margin-top: 5px; overflow: hidden;
}
.nw-factor-fill { height: 100%; border-radius: 999px; }
.nw-pos { color: #5FBF8B; }
.nw-neg { color: #E08A7A; }
.nw-pos-bg { background: #3E7D5E; }
.nw-neg-bg { background: #9E5142; }
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_resource
def load_model():
    return joblib.load(MODEL_PATH)


@st.cache_data
def load_metrics():
    if METRICS_PATH.exists():
        return pd.read_csv(METRICS_PATH)
    return None


@st.cache_data
def load_data():
    if DATA_PATH.exists():
        return pd.read_csv(DATA_PATH)
    return None


@st.cache_resource
def load_interval():
    if INTERVAL_PATH.exists():
        return joblib.load(INTERVAL_PATH)
    return None


@st.cache_data
def baseline_features(df: pd.DataFrame) -> dict:
    """A 'typical' listing: median for numerics, mode for categoricals."""
    base = {c: df[c].mode()[0] for c in CATEGORICAL_RAW}
    for c in NUMERIC_RAW:
        base[c] = int(round(df[c].median()))
    base["area"] = float(df["area"].median())
    return base


def inr(amount: float) -> str:
    if amount >= 1_00_00_000:
        return f"₹{amount / 1_00_00_000:,.2f} Cr"
    if amount >= 1_00_000:
        return f"₹{amount / 1_00_000:,.1f} Lakh"
    return f"₹{amount:,.0f}"


def build_input(raw: dict) -> pd.DataFrame:
    return pd.DataFrame([raw])


def prediction_interval(bundle, input_df, point):
    """Conformalized [low, high] band, widened to always contain the point."""
    lo = bundle["lo"].predict(input_df)[0] - bundle["q"]
    hi = bundle["hi"].predict(input_df)[0] + bundle["q"]
    lo, hi = min(lo, hi), max(lo, hi)
    lo, hi = min(lo, point), max(hi, point)
    return max(lo, 0.0), hi


def market_position(df: pd.DataFrame, location: str, price: float):
    """Position of an estimate within its locality (falls back to all of Bengaluru)."""
    seg = df[df["location"] == location]
    if len(seg) < 8:
        seg = df
    low, mid, high = seg["price"].quantile([0.10, 0.50, 0.90])
    span = max(high - low, 1.0)
    pct = min(max((price - low) / span * 100, 4.0), 96.0)
    delta_pct = (price - mid) / mid * 100

    bar_html = (
        '<div class="nw-bar-wrap">'
        '<div class="nw-bar-track">'
        f'<div class="nw-bar-marker" style="left:{pct:.1f}%"></div>'
        f'<div class="nw-bar-mark-label" style="left:{pct:.1f}%">{inr(price)}</div>'
        "</div>"
        f'<div class="nw-bar-ends"><span>{inr(low)}</span><span>{inr(high)}</span></div>'
        "</div>"
    )
    return delta_pct, bar_html, len(seg)


def explain_prediction(_model, raw: dict, baseline: dict, full_pred: float, top=5):
    """Per-feature contribution: set each feature to its typical value, re-predict."""
    factors = []
    for feat, label_fn in FACTOR_LABELS.items():
        probe = dict(raw)
        probe[feat] = baseline[feat]
        delta = full_pred - _model.predict(build_input(probe))[0]
        factors.append((label_fn(raw[feat]), delta))
    factors.sort(key=lambda x: abs(x[1]), reverse=True)
    return factors[:top]


def factors_html(factors) -> str:
    max_abs = max((abs(d) for _, d in factors), default=1) or 1
    rows = []
    for label, delta in factors:
        cls = "nw-pos" if delta >= 0 else "nw-neg"
        sign = "+" if delta >= 0 else "−"
        width = abs(delta) / max_abs * 100
        rows.append(
            '<div class="nw-factor">'
            '<div class="nw-factor-top">'
            f'<span class="nw-factor-label">{label}</span>'
            f'<span class="nw-factor-val {cls}">{sign}{inr(abs(delta))}</span>'
            "</div>"
            '<div class="nw-factor-bar">'
            f'<div class="nw-factor-fill {cls}-bg" style="width:{width:.0f}%"></div>'
            "</div></div>"
        )
    return "".join(rows)


def comparable_homes(df: pd.DataFrame, location: str, area: float, k=5):
    seg = df[df["location"] == location]
    if len(seg) < k:
        seg = df
    if seg.empty:
        return None
    seg = seg.assign(_d=(seg["area"] - area).abs()).sort_values("_d").head(k)
    out = seg[["area", "bedrooms", "bathrooms", "area_type", "price"]].copy()
    out.columns = ["Area (sq ft)", "BHK", "Baths", "Type", "Price"]
    return out


st.title("NestWorth")
st.write("Know what a home is worth — price estimates for Bengaluru.")

if not MODEL_PATH.exists():
    st.error(
        "No trained model found. From the project root, run:\n\n"
        "```\npython src/data_preprocessing.py\npython src/train_model.py\n```"
    )
    st.stop()

model = load_model()
metrics = load_metrics()
data = load_data()
interval = load_interval()

locations = sorted(data["location"].unique()) if data is not None else ["Whitefield"]
loc_default = locations.index("Whitefield") if "Whitefield" in locations else 0

with st.form("house"):
    col1, col2 = st.columns(2)

    with col1:
        area = st.number_input("Area (sq ft)", min_value=300, max_value=30000,
                               value=1200, step=50)
        bedrooms = st.selectbox("Bedrooms (BHK)", [1, 2, 3, 4, 5, 6], index=1)
        bathrooms = st.selectbox("Bathrooms", [1, 2, 3, 4, 5, 6], index=1)
        balcony = st.selectbox("Balconies", [0, 1, 2, 3], index=1)

    with col2:
        location = st.selectbox("Locality", locations, index=loc_default)
        area_type = st.selectbox("Area type", AREA_TYPES)
        status = st.radio("Possession", ["Ready to move", "Under construction"],
                          horizontal=True)

    submitted = st.form_submit_button("Estimate price", type="primary",
                                      width="stretch")

if submitted:
    raw = {
        "area": area, "bedrooms": bedrooms, "bathrooms": bathrooms,
        "balcony": balcony, "ready_to_move": int(status == "Ready to move"),
        "location": location, "area_type": area_type,
    }
    input_df = build_input(raw)

    predicted_price = model.predict(input_df)[0]
    price_per_sqft = predicted_price / area

    mae = metrics.iloc[0]["MAE"] if metrics is not None else None
    r2 = metrics.iloc[0]["R2"] if metrics is not None else None

    sub_bits = [f"₹{price_per_sqft:,.0f} / sq ft"]
    if interval is not None:
        lo, hi = prediction_interval(interval, input_df, predicted_price)
        cov = int(interval["coverage"] * 100)
        sub_bits.append(f"{cov}% interval {inr(lo)} – {inr(hi)}")
    elif mae is not None:
        sub_bits.append(
            f"likely {inr(predicted_price - mae)} – {inr(predicted_price + mae)}"
        )
    sub_line = "&nbsp;&nbsp;·&nbsp;&nbsp;".join(sub_bits)
    badge = (
        f'<span class="nw-badge">Model R² {r2:.2f} on held-out test data</span>'
        if r2 is not None else ""
    )

    st.markdown(
        f'<div class="nw-hero">'
        f'<div class="nw-hero-label">Estimated value</div>'
        f'<div class="nw-hero-price">{inr(predicted_price)}</div>'
        f'<div class="nw-hero-sub">{sub_line}</div>'
        f"{badge}"
        f"</div>",
        unsafe_allow_html=True,
    )

    if data is not None:
        delta_pct, bar_html, n_seg = market_position(data, location, predicted_price)
        direction = "above" if delta_pct >= 0 else "below"
        st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
        st.markdown("###### How it compares")
        st.markdown(
            f"About **{abs(delta_pct):.0f}% {direction}** the typical price for "
            f"**{location}** homes."
        )
        st.markdown(bar_html, unsafe_allow_html=True)
        st.caption(
            f"Bar spans the typical range (10th–90th percentile) of {n_seg} "
            f"comparable listings in {location}."
        )

        factors = explain_prediction(
            model, raw, baseline_features(data), predicted_price
        )
        st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
        st.markdown("###### Why this price?")
        st.markdown(factors_html(factors), unsafe_allow_html=True)
        st.caption(
            "How much each feature adds to or subtracts from the estimate, "
            "versus a typical listing."
        )

        comps = comparable_homes(data, location, area)
        if comps is not None:
            with st.expander(f"Comparable homes in {location}"):
                st.dataframe(
                    comps.style.format({
                        "Area (sq ft)": "{:,.0f}", "BHK": "{:.0f}",
                        "Baths": "{:.0f}", "Price": inr,
                    }),
                    hide_index=True,
                    width="stretch",
                )
                st.caption("Closest listings by size in the same locality.")

    st.caption("Estimates from real Bengaluru listings — not a formal valuation.")

st.divider()

with st.expander("About the model"):
    st.write(
        "A scikit-learn pipeline (one-hot encoding, scaling, and the best of "
        "three compared regressors) trained on ~7,300 real Bengaluru listings "
        "after cleaning. Test-set results:"
    )
    if metrics is not None:
        st.dataframe(
            metrics.style.format({"MAE": inr, "RMSE": inr, "R2": "{:.3f}"}),
            hide_index=True,
            width="stretch",
        )
    st.write(
        "Source code and full pipeline: "
        "[github.com/SamGabriel-Here/nestworth]"
        "(https://github.com/SamGabriel-Here/nestworth)"
    )
