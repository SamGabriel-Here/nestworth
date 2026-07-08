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
GITHUB = "https://github.com/SamGabriel-Here/nestworth"

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

st.set_page_config(page_title="NestWorth — home valuation", page_icon="🏠",
                   layout="wide")

BASE_CSS = """
<style>
.block-container { max-width: 1060px; padding-top: 0.4rem; padding-bottom: 3rem; }
[data-testid="stHeader"] { background: transparent; }
.nw-header { width: 100vw; margin-left: calc(-50vw + 50%); padding: 15px clamp(18px, 6vw, 64px); display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid; margin-bottom: 8px; }
.nw-logo { font-size: 20px; font-weight: 700; letter-spacing: -0.02em; }
.nw-nav { display: flex; gap: 26px; align-items: center; }
.nw-nav a { font-size: 13.5px; text-decoration: none; }
.nw-lede p { margin: 0; font-size: 1.02rem; line-height: 1.6; }
.nw-card { border-radius: 16px; padding: 28px 30px; margin: 4px 0; }
.nw-grid { display: grid; grid-template-columns: 0.82fr 1.18fr; gap: 40px; }
@media (max-width: 680px) { .nw-grid { grid-template-columns: 1fr; gap: 22px; } }
.nw-spec-title, .nw-comp-title { font-size: 11px; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 8px; font-weight: 600; }
.nw-spec-row { display: flex; justify-content: space-between; gap: 12px; padding: 9px 0; border-bottom: 1px solid; font-size: 14px; }
.nw-spec-row .v { font-weight: 600; text-align: right; }
.nw-vlabel { font-size: 11px; letter-spacing: 0.12em; text-transform: uppercase; font-weight: 700; }
.nw-price { font-weight: 800; line-height: 1; font-size: clamp(2.6rem, 6vw, 3.4rem); margin: 8px 0 4px; letter-spacing: -0.02em; }
.nw-ppsf { font-size: 13px; font-variant-numeric: tabular-nums; }
.nw-badge { display: inline-block; margin-top: 14px; border-radius: 7px; padding: 5px 12px; font-size: 0.74rem; font-weight: 700; }
.nw-rail { margin: 24px 0 0; }
.nw-rail-track { position: relative; height: 8px; border-radius: 999px; }
.nw-rail-band { position: absolute; top: 0; height: 100%; border-radius: 999px; }
.nw-rail-diamond { position: absolute; top: 50%; width: 13px; height: 13px; transform: translate(-50%, -50%) rotate(45deg); }
.nw-rail-label { position: absolute; top: -27px; transform: translateX(-50%); white-space: nowrap; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 5px; }
.nw-rail-ends { display: flex; justify-content: space-between; margin-top: 12px; font-size: 11px; font-variant-numeric: tabular-nums; }
.nw-rail-cap { margin-top: 12px; font-size: 13px; }
.nw-h { font-size: 15px; font-weight: 700; margin: 32px 0 14px; }
.nw-factor { margin: 11px 0; }
.nw-factor-top { display: flex; justify-content: space-between; align-items: baseline; font-size: 0.9rem; }
.nw-factor-label { font-weight: 600; }
.nw-factor-val { font-weight: 800; font-variant-numeric: tabular-nums; }
.nw-factor-bar { height: 6px; border-radius: 999px; margin-top: 5px; overflow: hidden; }
.nw-factor-fill { height: 100%; border-radius: 999px; }
.nw-comp-row { display: flex; justify-content: space-between; gap: 12px; padding: 9px 0; border-bottom: 1px solid; font-size: 13.5px; }
.nw-comp-row b { font-weight: 700; font-variant-numeric: tabular-nums; }
.nw-cap { font-size: 12px; margin-top: 9px; }
</style>
"""

LEDGER_CSS = """
<style>
.stApp { background-color: #F1F2EE; }
h1 { font-family: Georgia, "Iowan Old Style", "Palatino Linotype", serif; font-weight: 700; color: #1B1E1C; }
.nw-header { background: #FBFBF8; border-color: #E3E4DD; }
.nw-logo { color: #1B1E1C; } .nw-logo b { color: #1F5C43; }
.nw-nav a { color: #6E736C; } .nw-nav a:hover { color: #1F5C43; }
.nw-lede p { color: #5C615A; }
.nw-card { background: #FBFBF8; border: 1px solid #E3E4DD; }
.nw-spec-title, .nw-comp-title { color: #9A9E94; }
.nw-spec-row { border-color: #ECECE5; } .nw-spec-row .k { color: #77776F; } .nw-spec-row .v { color: #1B1E1C; }
.nw-vlabel { color: #9A9E94; }
.nw-price { font-family: Georgia, "Iowan Old Style", "Palatino Linotype", serif; color: #1B1E1C; }
.nw-ppsf { color: #6E736C; }
.nw-badge { background: #E7EFEA; color: #1F5C43; }
.nw-rail-track { background: #E6E7E0; }
.nw-rail-band { background: #CFE1D6; }
.nw-rail-band::before, .nw-rail-band::after { content: ""; position: absolute; top: -3px; height: 14px; width: 1.5px; background: #8FB6A2; }
.nw-rail-band::before { left: 0; } .nw-rail-band::after { right: 0; }
.nw-rail-diamond { background: #1F5C43; box-shadow: 0 0 0 3px #FBFBF8; }
.nw-rail-label { background: #1F5C43; color: #FBFBF8; }
.nw-rail-ends { color: #9A9E94; }
.nw-rail-cap { color: #6E736C; } .nw-cap-b { color: #1F5C43; font-weight: 700; }
.nw-h { color: #1B1E1C; }
.nw-factor-label { color: #45463F; }
.nw-factor-bar { background: #E7E8E0; }
.nw-pos { color: #1F5C43; } .nw-neg { color: #9A3B34; }
.nw-pos-bg { background: #2E7D5B; } .nw-neg-bg { background: #C06A5C; }
.nw-comp-row { border-color: #ECECE5; color: #55554E; } .nw-comp-row b { color: #1B1E1C; }
.nw-cap { color: #9A9E94; }
[data-testid="stForm"] { border-color: #DEDFD8; }
button[kind="primaryFormSubmit"] { background-color: #1F5C43; border-color: #1F5C43; color: #FBFBF8; }
button[kind="primaryFormSubmit"]:hover { background-color: #17472F; border-color: #17472F; color: #FBFBF8; }
</style>
"""

INSTRUMENT_CSS = """
<style>
.stApp { background: radial-gradient(130% 90% at 50% -10%, #15212C 0%, #0B0E13 58%) #0B0E13; }
h1 { color: #F4F7FB; font-weight: 800; }
.nw-header { background: rgba(11,14,19,0.55); border-color: #1C2430; }
.nw-logo { color: #E9ECF2; } .nw-logo b { color: #46E0A6; }
.nw-nav a { color: #8892A4; } .nw-nav a:hover { color: #46E0A6; }
.nw-lede p { color: #8892A4; }
.nw-card { background: #0F141C; border: 1px solid #1C2430; }
.nw-spec-title, .nw-comp-title { color: #5C687A; }
.nw-spec-row { border-color: #1A212B; } .nw-spec-row .k { color: #7E889A; } .nw-spec-row .v { color: #D3D8E2; }
.nw-vlabel { color: #5C687A; }
.nw-price { color: #F4F7FB; text-shadow: 0 0 30px rgba(70,224,166,0.18); }
.nw-ppsf { color: #8892A4; }
.nw-badge { background: rgba(70,224,166,0.14); color: #7CE9BE; }
.nw-rail-track { background: linear-gradient(90deg,#1E5C43,#8A6B22,#8A3A2E); }
.nw-rail-band { border: 1px solid rgba(70,224,166,0.5); background: rgba(70,224,166,0.08); top: -3px; height: 14px; border-radius: 5px; }
.nw-rail-diamond { background: #46E0A6; box-shadow: 0 0 12px 2px rgba(70,224,166,0.6), 0 0 0 3px #0B0E13; }
.nw-rail-label { background: #46E0A6; color: #06231A; }
.nw-rail-ends { color: #5C687A; }
.nw-rail-cap { color: #8892A4; } .nw-cap-b { color: #46E0A6; font-weight: 700; }
.nw-h { color: #E9ECF2; }
.nw-factor-label { color: #B7BECC; }
.nw-factor-bar { background: #1A212B; }
.nw-pos { color: #46E0A6; } .nw-neg { color: #FF8A7A; }
.nw-pos-bg { background: #35C08C; } .nw-neg-bg { background: #E06A5A; }
.nw-comp-row { border-color: #1A212B; color: #9AA3B4; } .nw-comp-row b { color: #E9ECF2; }
.nw-cap { color: #5C687A; }
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


def segment_stats(df: pd.DataFrame, city: str, location: str):
    """10th / 50th / 90th-percentile prices for the city+locality segment."""
    seg = df[(df["city"] == city) & (df["location"] == location)]
    if len(seg) < 8:
        seg = df[df["city"] == city]
    if len(seg) < 8:
        return None
    low, mid, high = seg["price"].quantile([0.10, 0.50, 0.90])
    return float(low), float(mid), float(high), len(seg)


def spec_html(raw: dict) -> str:
    rows = [
        ("Locality", f"{raw['location']}, {raw['city']}"),
        ("Built-up area", f"{int(raw['area']):,} sq ft"),
        ("Configuration", f"{int(raw['bedrooms'])} BHK · {int(raw['bathrooms'])} bath"),
        ("Age", f"{int(raw['house_age'])} years"),
        ("Furnishing", raw["furnishing_status"].capitalize()),
    ]
    body = "".join(
        f'<div class="nw-spec-row"><span class="k">{k}</span>'
        f'<span class="v">{v}</span></div>'
        for k, v in rows
    )
    return f'<div class="nw-spec-title">The property</div>{body}'


def rail_html(low, high, price, int_lo, int_hi) -> str:
    span = max(high - low, 1.0)
    pct = min(max((price - low) / span * 100, 2.0), 98.0)
    band_l = min(max((max(int_lo, low) - low) / span * 100, 0.0), 100.0)
    band_r = min(max((min(int_hi, high) - low) / span * 100, 0.0), 100.0)
    band_w = max(band_r - band_l, 1.0)
    return (
        '<div class="nw-rail"><div class="nw-rail-track">'
        f'<div class="nw-rail-band" style="left:{band_l:.1f}%;width:{band_w:.1f}%"></div>'
        f'<div class="nw-rail-diamond" style="left:{pct:.1f}%"></div>'
        f'<div class="nw-rail-label" style="left:{pct:.1f}%">{inr(price)}</div>'
        "</div>"
        f'<div class="nw-rail-ends"><span>{inr(low)}</span><span>{inr(high)}</span></div>'
        "</div>"
    )


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
            '<div class="nw-factor"><div class="nw-factor-top">'
            f'<span class="nw-factor-label">{label}</span>'
            f'<span class="nw-factor-val {cls}">{sign}{inr(abs(delta))}</span></div>'
            '<div class="nw-factor-bar">'
            f'<div class="nw-factor-fill {cls}-bg" style="width:{width:.0f}%"></div>'
            "</div></div>"
        )
    return "".join(rows)


def comps_html(df: pd.DataFrame, city: str, location: str, area: float, k=5) -> str:
    seg = df[(df["city"] == city) & (df["location"] == location)]
    if len(seg) < k:
        seg = df[df["city"] == city]
    if seg.empty:
        return ""
    seg = seg.assign(_d=(seg["area"] - area).abs()).sort_values("_d").head(k)
    rows = []
    for _, r in seg.iterrows():
        desc = f"{int(r['area']):,} sq ft · {int(r['bedrooms'])} BHK · {int(r['house_age'])} yrs"
        rows.append(f'<div class="nw-comp-row"><span>{desc}</span><b>{inr(r["price"])}</b></div>')
    return "".join(rows)


st.markdown(
    f'<div class="nw-header"><div class="nw-logo">Nest<b>Worth</b></div>'
    f'<div class="nw-nav"><a href="#nw-about">How it works</a>'
    f'<a href="{GITHUB}" target="_blank">Source ↗</a></div></div>',
    unsafe_allow_html=True,
)

_, theme_col = st.columns([4, 1])
with theme_col:
    st.segmented_control(
        "Theme", ["Ledger", "Instrument"], default="Ledger",
        key="theme", label_visibility="collapsed",
    )

st.title("What's your home worth?")
st.markdown(
    '<div class="nw-lede"><p>Instant price estimates for five Indian metro cities — '
    "with a 90% confidence range and the reasons behind every number.</p></div>",
    unsafe_allow_html=True,
)

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

st.write("")
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
    st.session_state["estimated"] = True

if st.session_state.get("estimated"):
    raw = {
        "area": area, "bedrooms": bedrooms, "bathrooms": bathrooms,
        "stories": stories, "city": city, "location": location,
        "house_age": house_age, "parking": parking, "main_road": main_road,
        "furnishing_status": furnishing_status,
    }
    input_df = build_input(raw)
    predicted_price = model.predict(input_df)[0]
    price_per_sqft = predicted_price / area
    r2 = metrics.iloc[0]["R2"] if metrics is not None else None

    stats = segment_stats(data, city, location) if data is not None else None
    if interval is not None:
        int_lo, int_hi = prediction_interval(interval, input_df, predicted_price)
        cov = int(interval["coverage"] * 100)
    else:
        int_lo, int_hi, cov = predicted_price, predicted_price, 90

    low, high = (stats[0], stats[2]) if stats else (int_lo, int_hi)
    rail = rail_html(low, high, predicted_price, int_lo, int_hi)
    badge = (
        f'<span class="nw-badge">Model R² {r2:.2f} on held-out data</span>'
        if r2 is not None else ""
    )
    valuation = (
        '<div class="nw-vlabel">Estimated value</div>'
        f'<div class="nw-price">{inr(predicted_price)}</div>'
        f'<div class="nw-ppsf">₹{price_per_sqft:,.0f} per sq ft</div>'
        f"{rail}"
        f'<div class="nw-rail-cap"><span class="nw-cap-b">{cov}% confidence:</span> '
        f"{inr(int_lo)} – {inr(int_hi)} · shown against typical {city} · {location} prices</div>"
        f"{badge}"
    )
    st.markdown(
        f'<div class="nw-card"><div class="nw-grid"><div>{spec_html(raw)}</div>'
        f"<div>{valuation}</div></div></div>",
        unsafe_allow_html=True,
    )

    if data is not None:
        factors = explain_prediction(
            model, raw, baseline_features(data), predicted_price
        )
        st.markdown(
            f'<div class="nw-h">Why this price</div>{factors_html(factors)}'
            '<div class="nw-cap">How much each feature adds to or subtracts from the '
            "estimate, versus a typical listing.</div>",
            unsafe_allow_html=True,
        )
        comps = comps_html(data, city, location, area)
        if comps:
            st.markdown(
                f'<div class="nw-h">Comparable homes in {city} · {location}</div>{comps}'
                '<div class="nw-cap">Closest listings by size in the same city and '
                "locality.</div>",
                unsafe_allow_html=True,
            )

    st.markdown(
        '<div class="nw-cap" style="margin-top:16px">Trained on this project\'s '
        "dataset — not a real valuation.</div>",
        unsafe_allow_html=True,
    )

st.markdown('<div id="nw-about"></div>', unsafe_allow_html=True)
st.divider()

with st.expander("How the model works"):
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
    st.write(f"Source code and full pipeline: [{GITHUB.split('//')[1]}]({GITHUB})")
