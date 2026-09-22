import numpy as np
import pandas as pd

from src.pipeline.prepare import add_features, clean_dataset


def test_clean_dataset_fills_gaps_and_drops_duplicates():
    df = pd.DataFrame({
        "area": [1000, np.nan, 1200, 1200],
        "bedrooms": [2, 3, 3, 3],
        "bathrooms": [1, 2, 2, 2],
        "stories": [1, 2, 1, 1],
        "house_age": [5, 10, 3, 3],
        "parking": [1, 0, 2, 2],
        "city": ["Mumbai", "Delhi", "Chennai", "Chennai"],
        "location": ["Suburb", "Outskirts", "Suburb", "Suburb"],
        "main_road": ["yes", "no", "yes", "yes"],
        "furnishing_status": ["furnished", None, "unfurnished", "unfurnished"],
        "price": [9e6, 7e6, 8e6, 8e6],
    })
    out = clean_dataset(df)
    assert out.isna().sum().sum() == 0
    assert not out.duplicated().any()


def test_add_features():
    out = add_features(pd.DataFrame({"bedrooms": [3, 2], "bathrooms": [2, 1],
                                     "house_age": [4, 20]}))
    assert out["total_rooms"].tolist() == [5, 3]
    assert out["is_new"].tolist() == [1, 0]
