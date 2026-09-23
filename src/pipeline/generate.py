"""Generate the housing dataset (data/housing_data.csv)."""

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "housing_data.csv"

N_ROWS = 6000
RANDOM_SEED = 42

# average residential rate per sq ft (INR) and share of listings
CITIES = {
    "Mumbai": (18_000, .12), "Delhi": (11_000, .11), "Bangalore": (8_500, .11), "Pune": (8_000, .08),
    "Hyderabad": (7_500, .09), "Chennai": (7_000, .08), "Chandigarh": (6_500, .05), "Kochi": (6_000, .05),
    "Ahmedabad": (5_500, .07), "Kolkata": (5_500, .08), "Jaipur": (5_000, .06), "Lucknow": (4_800, .05),
    "Indore": (4_500, .05),
}
# price multiplier on the city rate and share of listings
LOCATIONS = {
    "City Centre": (1.8, .12), "Prime Suburb": (1.25, .16), "Suburb": (1.0, .24), "Outskirts": (0.55, .14),
    "Premium Township": (1.5, .08), "Gated Community": (1.3, .10), "Near Metro": (1.15, .10), "Waterfront": (1.65, .06),
}
# price multiplier and share of listings
TYPES = {
    "Apartment": (1.0, .42), "Studio": (1.08, .10), "Row House": (1.05, .12),
    "Independent House": (1.12, .18), "Villa": (1.35, .11), "Penthouse": (1.5, .07),
}


def pick(rng, table: dict, n: int):
    names = list(table)
    p = np.array([v[1] for v in table.values()])
    return rng.choice(names, n, p=p / p.sum())


def generate_houses(n: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    city = pick(rng, CITIES, n)
    location = pick(rng, LOCATIONS, n)
    kind = pick(rng, TYPES, n)

    area = rng.normal(1150, 420, n).clip(350, 3500)
    bedrooms = rng.choice([1, 2, 3, 4, 5], n, p=[0.15, 0.35, 0.32, 0.14, 0.04])
    stories = rng.choice([1, 2, 3, 4], n, p=[0.35, 0.40, 0.20, 0.05])
    parking = rng.choice([0, 1, 2, 3], n, p=[0.25, 0.45, 0.22, 0.08])

    # each type has its own shape: studios are one small room, villas and penthouses are large
    studio, villa, pent = kind == "Studio", kind == "Villa", kind == "Penthouse"
    flat, row = kind == "Apartment", kind == "Row House"
    area = np.where(studio, rng.uniform(300, 650, n), area)
    area = np.where(villa, rng.normal(2800, 700, n).clip(1600, 6000), area)
    area = np.where(pent, rng.normal(2400, 600, n).clip(1500, 4500), area)
    bedrooms = np.where(studio, 1, np.where(villa | pent, np.maximum(bedrooms, 3), bedrooms))
    stories = np.where(studio, 1, stories)
    stories = np.where(flat, rng.choice([1, 2], n, p=[0.8, 0.2]), stories)          # duplexes are rarer
    stories = np.where(pent, rng.choice([1, 2], n, p=[0.6, 0.4]), stories)
    stories = np.where(villa | row, np.maximum(stories, 2), stories)
    parking = np.where(villa, np.maximum(parking, 1), parking)
    bathrooms = np.clip(bedrooms - rng.choice([0, 1, 2], n, p=[0.5, 0.4, 0.1]), 1, 4)
    area = area.round(0)

    house_age = rng.integers(0, 61, n)
    main_road = rng.choice(["yes", "no"], n, p=[0.70, 0.30])
    furnishing = rng.choice(["furnished", "semi-furnished", "unfurnished"], n, p=[0.20, 0.45, 0.35])

    city_rate = np.array([CITIES[c][0] for c in city])
    location_multiplier = np.array([LOCATIONS[l][0] for l in location])
    type_multiplier = np.array([TYPES[k][0] for k in kind])
    furnishing_bonus = pd.Series(furnishing).map(
        {"furnished": 6_00_000, "semi-furnished": 2_50_000, "unfurnished": 0}
    ).to_numpy()

    # amenity premiums scale with how expensive the city is
    premium_scale = city_rate / 8_500

    price = (
        3_00_000
        + area * city_rate * location_multiplier * type_multiplier
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
        "property_type": kind,
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

    duplicates = df.sample(100, random_state=seed)
    df = pd.concat([df, duplicates], ignore_index=True)

    outlier_idx = rng.choice(df.index, size=40, replace=False)
    df.loc[outlier_idx, "price"] = df.loc[outlier_idx, "price"] * rng.uniform(3.5, 5.0, 40)

    big_area_idx = rng.choice(df.index, size=20, replace=False)
    df.loc[big_area_idx, "area"] = rng.uniform(9000, 14000, 20).round(0)

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
