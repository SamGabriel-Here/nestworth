"""Streamlit app for house price predictions."""

from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "house_price_model.pkl"
METRICS_PATH = ROOT / "reports" / "model_comparison.csv"

st.set_page_config(page_title="House Price Predictor", page_icon="🏠", layout="centered")


@st.cache_resource
def load_model():
    return joblib.load(MODEL_PATH)


@st.cache_data
def load_metrics():
    if METRICS_PATH.exists():
        return pd.read_csv(METRICS_PATH)
    return None


st.title("House Price Predictor")
st.write("Estimate a house's market price from its key characteristics.")

if not MODEL_PATH.exists():
    st.error(
        "No trained model found. From the project root, run:\n\n"
        "```\npython src/generate_dataset.py\npython src/data_preprocessing.py\n"
        "python src/train_model.py\n```"
    )
    st.stop()

model = load_model()
metrics = load_metrics()

with st.form("house"):
    col1, col2 = st.columns(2)

    with col1:
        area = st.number_input("Area (sq ft)", min_value=300, max_value=12000,
                               value=1800, step=50)
        bedrooms = st.selectbox("Bedrooms", [1, 2, 3, 4, 5], index=2)
        bathrooms = st.selectbox("Bathrooms", [1, 2, 3, 4], index=1)
        stories = st.selectbox("Stories", [1, 2, 3, 4], index=1)

    with col2:
        location = st.selectbox(
            "Location", ["Downtown", "Midtown", "Suburban", "Rural", "Waterfront"]
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
        "location": location,
        "house_age": house_age,
        "parking": parking,
        "main_road": main_road,
        "furnishing_status": furnishing_status,
    }])
    input_df["total_rooms"] = input_df["bedrooms"] + input_df["bathrooms"]
    input_df["is_new"] = (input_df["house_age"] <= 5).astype(int)

    predicted_price = model.predict(input_df)[0]

    st.divider()

    m1, m2, m3 = st.columns(3)
    m1.metric("Estimated price", f"${predicted_price:,.0f}")
    m2.metric("Price per sq ft", f"${predicted_price / area:,.0f}")
    if metrics is not None:
        mae = metrics.iloc[0]["MAE"]
        m3.metric("Typical error", f"± ${mae:,.0f}")
        st.caption(
            f"Likely range: **\\${predicted_price - mae:,.0f} – "
            f"\\${predicted_price + mae:,.0f}** based on the model's mean "
            "absolute error on held-out test data."
        )

    st.caption("Trained on this project's dataset — not a real valuation.")

st.divider()

with st.expander("About the model"):
    st.write(
        "A scikit-learn pipeline (imputation, one-hot encoding, scaling, and "
        "the best of three compared regressors) trained on ~1,500 listings. "
        "Test-set results:"
    )
    if metrics is not None:
        st.dataframe(
            metrics.style.format({"MAE": "${:,.0f}", "RMSE": "${:,.0f}", "R2": "{:.3f}"}),
            hide_index=True,
            width="stretch",
        )
    st.write(
        "Source code and full pipeline: "
        "[github.com/SamGabriel-Here/house-price-prediction]"
        "(https://github.com/SamGabriel-Here/house-price-prediction)"
    )
