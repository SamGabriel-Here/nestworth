"""Data cleaning and the model pipeline (features -> preprocessing -> regressor)."""

from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_PATH = ROOT / "data" / "housing_data.csv"
CLEAN_DATA_PATH = ROOT / "data" / "housing_clean.csv"

TARGET = "price"
NUMERIC_COLS = ["area", "bedrooms", "bathrooms", "stories", "house_age", "parking"]
CATEGORICAL_COLS = ["city", "location", "main_road", "furnishing_status"]
INPUT_COLS = NUMERIC_COLS + CATEGORICAL_COLS
ENGINEERED_COLS = ["total_rooms", "is_new"]


def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in NUMERIC_COLS:
        df[col] = df[col].fillna(df[col].median())
    for col in CATEGORICAL_COLS:
        df[col] = df[col].fillna(df[col].mode()[0])
    df = df.drop_duplicates().reset_index(drop=True)
    for col in ("price", "area"):
        q1, q3 = df[col].quantile([0.25, 0.75])
        iqr = q3 - q1
        df[col] = df[col].clip(q1 - 1.5 * iqr, q3 + 1.5 * iqr)
    return df


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["total_rooms"] = df["bedrooms"] + df["bathrooms"]
    df["is_new"] = (df["house_age"] <= 5).astype(int)
    return df


def build_pipeline(model) -> Pipeline:
    """Raw property columns in, prediction out. Saved whole, so inference can't drift."""
    return Pipeline([
        ("features", FunctionTransformer(add_features)),
        ("preprocessor", ColumnTransformer([
            ("numeric", StandardScaler(), NUMERIC_COLS + ENGINEERED_COLS),
            ("categorical", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_COLS),
        ])),
        ("model", model),
    ])


def main() -> None:
    raw = pd.read_csv(RAW_DATA_PATH)
    clean = clean_dataset(raw)
    clean.to_csv(CLEAN_DATA_PATH, index=False)
    print(f"{raw.shape} -> {clean.shape}, missing {int(raw.isna().sum().sum())} -> 0")
    print(f"Saved {CLEAN_DATA_PATH}")


if __name__ == "__main__":
    main()
