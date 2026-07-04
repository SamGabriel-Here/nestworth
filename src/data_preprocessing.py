"""Data cleaning, feature engineering, and the preprocessing transformer."""

from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_PATH = ROOT / "data" / "housing_data.csv"
CLEAN_DATA_PATH = ROOT / "data" / "housing_clean.csv"

TARGET = "price"

NUMERIC_COLS = ["area", "bedrooms", "bathrooms", "stories", "house_age", "parking"]
CATEGORICAL_COLS = ["location", "main_road", "furnishing_status"]
ENGINEERED_COLS = ["total_rooms", "is_new"]

NUMERIC_FEATURES = NUMERIC_COLS + ENGINEERED_COLS
FEATURE_COLS = NUMERIC_FEATURES + CATEGORICAL_COLS


def load_data(path: Path = RAW_DATA_PATH) -> pd.DataFrame:
    return pd.read_csv(path)


def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in NUMERIC_COLS:
        if df[col].isna().any():
            df[col] = df[col].fillna(df[col].median())
    for col in CATEGORICAL_COLS:
        if df[col].isna().any():
            df[col] = df[col].fillna(df[col].mode()[0])
    return df


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop_duplicates().reset_index(drop=True)


def treat_outliers(df: pd.DataFrame, cols=("price", "area")) -> pd.DataFrame:
    df = df.copy()
    for col in cols:
        q1, q3 = df[col].quantile(0.25), df[col].quantile(0.75)
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        df[col] = df[col].clip(lower, upper)
    return df


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["total_rooms"] = df["bedrooms"] + df["bathrooms"]
    df["is_new"] = (df["house_age"] <= 5).astype(int)
    return df


def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    df = handle_missing_values(df)
    df = remove_duplicates(df)
    df = treat_outliers(df)
    df = add_features(df)
    return df


def build_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            ("numeric", StandardScaler(), NUMERIC_FEATURES),
            ("categorical", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_COLS),
        ]
    )


def main() -> None:
    df_raw = load_data()
    print("--- BEFORE cleaning ---")
    print(f"Shape: {df_raw.shape}")
    print(f"Missing values: {int(df_raw.isna().sum().sum())}")
    print(f"Duplicate rows: {int(df_raw.duplicated().sum())}")
    print(f"Max price: {df_raw['price'].max():,.0f}")

    df_clean = clean_dataset(df_raw)
    print("\n--- AFTER cleaning ---")
    print(f"Shape: {df_clean.shape}")
    print(f"Missing values: {int(df_clean.isna().sum().sum())}")
    print(f"Duplicate rows: {int(df_clean.duplicated().sum())}")
    print(f"Max price: {df_clean['price'].max():,.0f}")

    df_clean.to_csv(CLEAN_DATA_PATH, index=False)
    print(f"\nClean dataset saved to: {CLEAN_DATA_PATH}")


if __name__ == "__main__":
    main()
