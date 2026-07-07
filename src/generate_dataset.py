"""Generate the housing dataset (data/housing_data.csv)."""

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "housing_data.csv"

N_ROWS = 1500
RANDOM_SEED = 42


def generate_houses(n: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    area = rng.normal(1150, 420, n).clip(350, 3500).round(0)
    bedrooms = rng.choice([1, 2, 3, 4, 5], n, p=[0.15, 0.35, 0.32, 0.14, 0.04])
    bathrooms = np.clip(bedrooms - rng.choice([0, 1, 2], n, p=[0.5, 0.4, 0.1]), 1, None)
    stories = rng.choice([1, 2, 3, 4], n, p=[0.35, 0.40, 0.20, 0.05])
    house_age = rng.integers(0, 61, n)
    parking = rng.choice([0, 1, 2, 3], n, p=[0.25, 0.45, 0.22, 0.08])

    cities = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Kolkata"]
    city = rng.choice(cities, n, p=[0.22, 0.22, 0.22, 0.17, 0.17])

    locations = ["City Centre", "Prime Suburb", "Suburb", "Outskirts", "Premium Township"]
    location = rng.choice(locations, n, p=[0.15, 0.22, 0.33, 0.20, 0.10])
    main_road = rng.choice(["yes", "no"], n, p=[0.70, 0.30])
    furnishing = rng.choice(
        ["furnished", "semi-furnished", "unfurnished"], n, p=[0.20, 0.45, 0.35]
    )

    # average city rates in rupees per sq ft, adjusted by locality
    city_rate = pd.Series(city).map(
        {"Mumbai": 18_000, "Delhi": 11_000, "Bangalore": 8_500,
         "Chennai": 7_000, "Kolkata": 5_500}
    ).to_numpy()

    location_multiplier = pd.Series(location).map(
        {"City Centre": 1.8, "Prime Suburb": 1.25, "Suburb": 1.0,
         "Outskirts": 0.55, "Premium Township": 1.5}
    ).to_numpy()

    furnishing_bonus = pd.Series(furnishing).map(
        {"furnished": 6_00_000, "semi-furnished": 2_50_000, "unfurnished": 0}
    ).to_numpy()

    # amenity premiums scale with how expensive the city is
    premium_scale = city_rate / 8_500

    price = (
        3_00_000
        + area * city_rate * location_multiplier
        + (
            bedrooms * 3_00_000
            + bathrooms * 2_00_000
            + stories * 1_00_000
            + parking * 2_00_000
            - house_age * 40_000
            + (main_road == "yes") * 2_50_000
            + furnishing_bonus
        ) * premium_scale
    )
    price = (price * (1 + rng.normal(0, 0.08, n))).clip(10_00_000).round(0)

    return pd.DataFrame({
        "area": area,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "stories": stories,
        "city": city,
        "location": location,
        "house_age": house_age,
        "parking": parking,
        "main_road": main_road,
        "furnishing_status": furnishing,
        "price": price,
    })


def add_real_world_messiness(df: pd.DataFrame, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed + 1)
    df = df.copy()

    for col, frac in {"area": 0.02, "bathrooms": 0.015,
                      "parking": 0.02, "furnishing_status": 0.015}.items():
        idx = rng.choice(df.index, size=int(len(df) * frac), replace=False)
        df.loc[idx, col] = np.nan

    duplicates = df.sample(25, random_state=seed)
    df = pd.concat([df, duplicates], ignore_index=True)

    outlier_idx = rng.choice(df.index, size=10, replace=False)
    df.loc[outlier_idx, "price"] = df.loc[outlier_idx, "price"] * rng.uniform(3.5, 5.0, 10)

    big_area_idx = rng.choice(df.index, size=5, replace=False)
    df.loc[big_area_idx, "area"] = rng.uniform(6000, 9000, 5).round(0)

    return df.sample(frac=1, random_state=seed).reset_index(drop=True)


def main() -> None:
    df = generate_houses(N_ROWS, RANDOM_SEED)
    df = add_real_world_messiness(df, RANDOM_SEED)

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(DATA_PATH, index=False)

    print(f"Dataset saved to: {DATA_PATH}")
    print(f"Shape: {df.shape[0]} rows x {df.shape[1]} columns")
    print(f"Missing values:\n{df.isna().sum()[df.isna().sum() > 0]}")
    print(f"Duplicate rows: {df.duplicated().sum()}")


if __name__ == "__main__":
    main()
