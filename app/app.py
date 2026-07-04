"""Streamlit app for house price predictions."""

from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "house_price_model.pkl"

st.set_page_config(page_title="House Price Predictor", page_icon="🏠")


@st.cache_resource
def load_model():
    return joblib.load(MODEL_PATH)


st.title("House Price Predictor")
st.write("Enter the details of a house to get an estimated market price.")

if not MODEL_PATH.exists():
    st.error(
        "No trained model found. From the project root, run:\n\n"
        "```\npython src/generate_dataset.py\npython src/data_preprocessing.py\n"
        "python src/train_model.py\n```"
    )
    st.stop()

model = load_model()

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

if st.button("Estimate price", type="primary"):
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

    st.metric(label="Estimated house price", value=f"${predicted_price:,.0f}")
    st.caption("Trained on this project's dataset — not a real valuation.")
