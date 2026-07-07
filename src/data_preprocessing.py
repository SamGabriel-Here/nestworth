"""Clean the raw Bengaluru listings and build the preprocessing transformer."""

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_PATH = ROOT / "data" / "bengaluru_house_data.csv"
CLEAN_DATA_PATH = ROOT / "data" / "housing_clean.csv"

TARGET = "price"

NUMERIC_COLS = ["area", "bedrooms", "bathrooms", "balcony", "ready_to_move"]
CATEGORICAL_COLS = ["location", "area_type"]
FEATURE_COLS = NUMERIC_COLS + CATEGORICAL_COLS

RARE_LOCATION_MAX = 10  # localities with fewer listings are bucketed as "Other"


def load_data(path: Path = RAW_DATA_PATH) -> pd.DataFrame:
    return pd.read_csv(path)


def parse_bhk(size: str) -> float:
    """'2 BHK' / '4 Bedroom' -> 2 / 4."""
    try:
        return int(str(size).split(" ")[0])
    except (ValueError, IndexError):
        return np.nan


def parse_sqft(value: str) -> float:
    """Handle ranges ('1133 - 1384' -> midpoint) and drop non-metric units."""
    text = str(value).strip()
    if "-" in text:
        parts = text.split("-")
        try:
            return (float(parts[0]) + float(parts[1])) / 2
        except ValueError:
            return np.nan
    try:
        return float(text)
    except ValueError:
        return np.nan


def _drop_pps_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows outside one std of the per-sqft price within their locality."""
    kept = []
    for _, group in df.groupby("location"):
        mean, std = group["pps"].mean(), group["pps"].std()
        if pd.isna(std):
            kept.append(group)
        else:
            kept.append(group[(group["pps"] >= mean - std) & (group["pps"] <= mean + std)])
    return pd.concat(kept)


def _drop_bhk_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """Drop an N-BHK unit priced per sqft below the average (N-1)-BHK nearby."""
    exclude = np.array([])
    for _, loc_df in df.groupby("location"):
        stats = {
            bhk: {"mean": g["pps"].mean(), "count": g.shape[0]}
            for bhk, g in loc_df.groupby("bedrooms")
        }
        for bhk, g in loc_df.groupby("bedrooms"):
            smaller = stats.get(bhk - 1)
            if smaller and smaller["count"] > 5:
                exclude = np.append(exclude, g[g["pps"] < smaller["mean"]].index.values)
    return df.drop(exclude)


def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(subset=["location", "size"]).copy()

    df["bedrooms"] = df["size"].map(parse_bhk)
    df["area"] = df["total_sqft"].map(parse_sqft)
    df["bathrooms"] = df["bath"]
    df["ready_to_move"] = (df["availability"] == "Ready To Move").astype(int)
    df["area_type"] = df["area_type"].str.replace(r"\s+", " ", regex=True).str.strip()
    df["location"] = df["location"].str.strip()
    df["price"] = df["price"] * 1_00_000  # dataset is in lakhs -> rupees

    df = df.dropna(subset=["area", "bedrooms"])
    df["bathrooms"] = df["bathrooms"].fillna(df["bathrooms"].median())
    df["balcony"] = df["balcony"].fillna(df["balcony"].median())

    # sanity filters: at least 300 sqft per bedroom, baths not wildly over rooms
    df = df[df["area"] / df["bedrooms"] >= 300]
    df = df[df["bathrooms"] <= df["bedrooms"] + 2]

    counts = df["location"].value_counts()
    rare = counts[counts <= RARE_LOCATION_MAX].index
    df["location"] = df["location"].where(~df["location"].isin(rare), "Other")

    df["pps"] = df["price"] / df["area"]
    df = _drop_pps_outliers(df)
    df = _drop_bhk_outliers(df)

    return df[FEATURE_COLS + [TARGET]].reset_index(drop=True)


def build_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            ("numeric", StandardScaler(), NUMERIC_COLS),
            ("categorical", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_COLS),
        ]
    )


def main() -> None:
    df_raw = load_data()
    print("--- BEFORE cleaning ---")
    print(f"Shape: {df_raw.shape}")
    print(f"Missing values: {int(df_raw.isna().sum().sum())}")
    print(f"Unique localities: {df_raw['location'].nunique()}")

    df_clean = clean_dataset(df_raw)
    print("\n--- AFTER cleaning ---")
    print(f"Shape: {df_clean.shape}")
    print(f"Missing values: {int(df_clean.isna().sum().sum())}")
    print(f"Unique localities: {df_clean['location'].nunique()}")
    print(f"Median price: ₹{df_clean['price'].median() / 1_00_000:,.1f} Lakh")

    df_clean.to_csv(CLEAN_DATA_PATH, index=False)
    print(f"\nClean dataset saved to: {CLEAN_DATA_PATH}")


if __name__ == "__main__":
    main()
