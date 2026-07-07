"""Streamlit app for house price predictions."""

from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "house_price_model.pkl"
INTERVAL_PATH = ROOT / "models" / "prediction_interval.pkl"
METRICS_PATH = ROOT / "reports" / "model_comparison.csv"
DATA_PATH = ROOT / "data" / "housing_clean.csv"

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

st.set_page_config(page_title="NestWorth", page_icon="🏠", layout="centered")

BASE_CSS = """
<style>
h1 { letter-spacing: -0.02em; }
.nw-hero { border-radius: 14px; padding: 28px 24px; text-align: center; margin: 4px 0 6px; }
.nw-hero-label { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.12em; }
.nw-hero-price { font-weight: 800; line-height: 1; font-size: clamp(2.4rem, 9vw, 3.3rem); margin: 8px 0 6px; letter-spacing: -0.02em; }
.nw-hero-sub { font-size: 0.95rem; font-weight: 500; }
.nw-badge { display: inline-block; margin-top: 15px; border-radius: 7px; padding: 5px 13px; font-size: 0.76rem; font-weight: 700; }
.nw-bar-wrap { margin: 26px 0 2px; }
.nw-bar-track { position: relative; height: 11px; border-radius: 999px; }
.nw-bar-marker { position: absolute; top: -5px; width: 4px; height: 21px; border-radius: 2px; }
.nw-bar-mark-label { position: absolute; top: -31px; transform: translateX(-50%); white-space: nowrap; font-size: 0.72rem; font-weight: 700; padding: 3px 8px; border-radius: 6px; }
.nw-bar-ends { display: flex; justify-content: space-between; font-size: 0.75rem; font-weight: 600; margin-top: 9px; }
.nw-factor { margin: 10px 0; }
.nw-factor-top { display: flex; justify-content: space-between; align-items: baseline; font-size: 0.9rem; }
.nw-factor-label { font-weight: 600; }
.nw-factor-val { font-weight: 800; font-variant-numeric: tabular-nums; }
.nw-factor-bar { height: 6px; border-radius: 999px; margin-top: 5px; overflow: hidden; }
.nw-factor-fill { height: 100%; border-radius: 999px; }
[data-testid="stHeader"] { background: transparent; }
</style>
"""

LEDGER_CSS = """
<style>
.stApp { background-color: #F1F2EE; }
h1, .nw-hero-price { font-family: Georgia, "Iowan Old Style", "Palatino Linotype", serif; font-weight: 700; color: #1B1E1C; }
.nw-hero { background: #FBFBF8; border: 1px solid #E3E4DD; }
.nw-hero-label { color: #9A9E94; }
.nw-hero-sub { color: #6E736C; }
.nw-badge { background: #E7EFEA; color: #1F5C43; }
.nw-bar-track { background: linear-gradient(90deg,#2E7D5B,#C9A227,#C0563B); }
.nw-bar-marker { background: #1B1E1C; box-shadow: 0 0 0 2px #FBFBF8; }
.nw-bar-mark-label { background: #1B1E1C; color: #FBFBF8; }
.nw-bar-ends { color: #9A9E94; }
.nw-factor-label { color: #45463F; }
.nw-factor-bar { background: #E7E8E0; }
.nw-pos { color: #1F5C43; } .nw-neg { color: #9A3B34; }
.nw-pos-bg { background: #2E7D5B; } .nw-neg-bg { background: #C06A5C; }
[data-testid="stForm"] { border-color: #DEDFD8; }
button[kind="primaryFormSubmit"] { background-color: #1F5C43; border-color: #1F5C43; color: #FBFBF8; }
button[kind="primaryFormSubmit"]:hover { background-color: #17472F; border-color: #17472F; color: #FBFBF8; }
</style>
"""

INSTRUMENT_CSS = """
<style>
.stApp { background: radial-gradient(130% 90% at 50% -10%, #15212C 0%, #0B0E13 58%) #0B0E13; }
h1 { color: #F4F7FB; font-weight: 800; }
.nw-hero-price { color: #F4F7FB; text-shadow: 0 0 30px rgba(70,224,166,0.18); }
.nw-hero { background: #12161E; border: 1px solid rgba(70,224,166,0.16); }
.nw-hero-label { color: #5C687A; }
.nw-hero-sub { color: #8892A4; }
.nw-badge { background: rgba(70,224,166,0.14); color: #7CE9BE; }
.nw-bar-track { background: linear-gradient(90deg,#1E5C43,#8A6B22,#8A3A2E); }
.nw-bar-marker { background: #E9ECF2; box-shadow: 0 0 0 2px #0B0E13; }
.nw-bar-mark-label { background: #46E0A6; color: #06231A; }
.nw-bar-ends { color: #5C687A; }
.nw-factor-label { color: #B7BECC; }
.nw-factor-bar { background: #1A212B; }
.nw-pos { color: #46E0A6; } .nw-neg { color: #FF8A7A; }
.nw-pos-bg { background: #35C08C; } .nw-neg-bg { background: #E06A5A; }
[data-testid="stMain"], [data-testid="stMarkdownContainer"] { color: #E9ECF2; }
[data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label, .stRadio label p, [data-testid="stExpander"] summary span { color: #C2C8DC !important; }
[data-testid="stForm"] { background: #0E121A; border: 1px solid #1E2530; }
[data-baseweb="select"] > div, [data-baseweb="input"], [data-baseweb="base-input"], [data-testid="stNumberInputContainer"] { background-color: #12161E !important; border-color: #28303C !important; }
input, textarea { background-color: transparent !important; color: #E9ECF2 !important; }
[data-baseweb="select"] div, [data-baseweb="select"] span, .stSlider label { color: #E9ECF2 !important; }
[data-testid="stNumberInputContainer"] button { background-color: #161B25 !important; color: #C2C8DC !important; border-color: #28303C !important; }
[data-testid="stSegmentedControl"] button { background-color: #12161E !important; color: #B7BECC !important; border-color: #28303C !important; }
[data-baseweb="popover"] ul[role="listbox"], [data-baseweb="menu"] { background-color: #12161E !important; }
[data-baseweb="popover"] li { color: #E9ECF2 !important; }
[data-testid="stExpander"] details { background: #0E121A; border-color: #1E2530; }
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] p { color: #C2C8DC; }
button[kind="primaryFormSubmit"] { background-color: #35C08C; border-color: #35C08C; color: #06231A; }
button[kind="primaryFormSubmit"]:hover { background-color: #2CA97B; border-color: #2CA97B; color: #06231A; }
</style>
"""

st.markdown(BASE_CSS, unsafe_allow_html=True)
st.markdown(
    LEDGER_CSS if st.session_state.get("theme", "Ledger") == "Ledger" else INSTRUMENT_CSS,
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


def prediction_interval(bundle, input_df, point):
    """Conformalized [low, high] band, widened to always contain the point."""
    lo = bundle["lo"].predict(input_df)[0] - bundle["q"]
    hi = bundle["hi"].predict(input_df)[0] + bundle["q"]
    lo, hi = min(lo, hi), max(lo, hi)
    lo, hi = min(lo, point), max(hi, point)
    return max(lo, 0.0), hi


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
    row = pd.DataFrame([raw])
    row["total_rooms"] = row["bedrooms"] + row["bathrooms"]
    row["is_new"] = (row["house_age"] <= 5).astype(int)
    return row


def market_position(df: pd.DataFrame, city: str, location: str, price: float):
    """Position of an estimate within its city/location segment.

    Returns (delta_pct, bar_html, n_listings), or (None, None, 0) if the
    segment is too small to be meaningful.
    """
    seg = df[(df["city"] == city) & (df["location"] == location)]
    if len(seg) < 8:
        seg = df[df["city"] == city]
    if len(seg) < 8:
        return None, None, 0

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
    """Per-feature contribution to the estimate.

    Each feature is set back to its typical value one at a time; the resulting
    change in the prediction is that feature's contribution versus a typical
    listing.
    """
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


def comparable_homes(df: pd.DataFrame, city: str, location: str, area: float, k=5):
    seg = df[(df["city"] == city) & (df["location"] == location)]
    if len(seg) < k:
        seg = df[df["city"] == city]
    if seg.empty:
        return None
    seg = seg.assign(_d=(seg["area"] - area).abs()).sort_values("_d").head(k)
    out = seg[["area", "bedrooms", "bathrooms", "house_age", "price"]].copy()
    out.columns = ["Area (sq ft)", "Beds", "Baths", "Age (yrs)", "Price"]
    return out


_, theme_col = st.columns([3, 1])
with theme_col:
    st.segmented_control(
        "Theme", ["Ledger", "Instrument"], default="Ledger",
        key="theme", label_visibility="collapsed",
    )

st.title("NestWorth")
st.write("Know what a home is worth — price estimates for Indian metro cities.")

if not MODEL_PATH.exists():
    st.error(
        "No trained model found. From the project root, run:\n\n"
        "```\npython src/generate_dataset.py\npython src/data_preprocessing.py\n"
        "python src/train_model.py\n```"
    )
    st.stop()

model = load_model()
metrics = load_metrics()
data = load_data()
interval = load_interval()

with st.form("house"):
    col1, col2 = st.columns(2)

    with col1:
        area = st.number_input("Area (sq ft)", min_value=300, max_value=9000,
                               value=1100, step=50)
        bedrooms = st.selectbox("Bedrooms", [1, 2, 3, 4, 5], index=2)
        bathrooms = st.selectbox("Bathrooms", [1, 2, 3, 4], index=1)
        stories = st.selectbox("Stories", [1, 2, 3, 4], index=1)

    with col2:
        city = st.selectbox(
            "City", ["Mumbai", "Delhi", "Bangalore", "Chennai", "Kolkata"]
        )
        location = st.selectbox(
            "Location",
            ["City Centre", "Prime Suburb", "Suburb", "Outskirts", "Premium Township"],
            index=2,
        )
        house_age = st.slider("House age (years)", min_value=0, max_value=60, value=10)
        parking = st.selectbox("Parking spots", [0, 1, 2, 3], index=1)

    main_road = st.radio("On a main road?", ["yes", "no"], horizontal=True)

    furnishing_status = st.selectbox(
        "Furnishing status", ["furnished", "semi-furnished", "unfurnished"], index=1
    )

    submitted = st.form_submit_button("Estimate price", type="primary",
                                      width="stretch")

if submitted:
    raw = {
        "area": area, "bedrooms": bedrooms, "bathrooms": bathrooms,
        "stories": stories, "city": city, "location": location,
        "house_age": house_age, "parking": parking, "main_road": main_road,
        "furnishing_status": furnishing_status,
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
        delta_pct, bar_html, n_seg = market_position(
            data, city, location, predicted_price
        )
        if bar_html:
            direction = "above" if delta_pct >= 0 else "below"
            st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
            st.markdown("###### How it compares")
            st.markdown(
                f"About **{abs(delta_pct):.0f}% {direction}** the typical price for "
                f"**{city} · {location}** homes."
            )
            st.markdown(bar_html, unsafe_allow_html=True)
            st.caption(
                f"Bar spans the typical range (10th–90th percentile) of {n_seg} "
                f"comparable {city} · {location} homes."
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

        comps = comparable_homes(data, city, location, area)
        if comps is not None:
            with st.expander(f"Comparable homes in {city} · {location}"):
                st.dataframe(
                    comps.style.format({
                        "Area (sq ft)": "{:,.0f}", "Beds": "{:.0f}",
                        "Baths": "{:.0f}", "Age (yrs)": "{:.0f}", "Price": inr,
                    }),
                    hide_index=True,
                    width="stretch",
                )
                st.caption("Closest listings by size in the same city and locality.")

    st.caption("Trained on this project's dataset — not a real valuation.")

st.divider()

with st.expander("About the model"):
    st.write(
        "A scikit-learn pipeline (imputation, one-hot encoding, scaling, and "
        "the best of three compared regressors) trained on ~1,500 listings "
        "priced at Indian metro-city rates. Test-set results:"
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
