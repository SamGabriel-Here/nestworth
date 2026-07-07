"""Streamlit app for house price predictions."""

from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "house_price_model.pkl"
METRICS_PATH = ROOT / "reports" / "model_comparison.csv"
DATA_PATH = ROOT / "data" / "housing_clean.csv"

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


def inr(amount: float) -> str:
    if amount >= 1_00_00_000:
        return f"₹{amount / 1_00_00_000:,.2f} Cr"
    if amount >= 1_00_000:
        return f"₹{amount / 1_00_000:,.1f} Lakh"
    return f"₹{amount:,.0f}"


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
    input_df = pd.DataFrame([{
        "area": area,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "stories": stories,
        "city": city,
        "location": location,
        "house_age": house_age,
        "parking": parking,
        "main_road": main_road,
        "furnishing_status": furnishing_status,
    }])
    input_df["total_rooms"] = input_df["bedrooms"] + input_df["bathrooms"]
    input_df["is_new"] = (input_df["house_age"] <= 5).astype(int)

    predicted_price = model.predict(input_df)[0]
    price_per_sqft = predicted_price / area

    mae = metrics.iloc[0]["MAE"] if metrics is not None else None
    r2 = metrics.iloc[0]["R2"] if metrics is not None else None

    sub_bits = [f"₹{price_per_sqft:,.0f} / sq ft"]
    if mae is not None:
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
