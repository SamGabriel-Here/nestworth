"""Train and compare regression models, saving the best to models/."""

from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from data_preprocessing import (
    CLEAN_DATA_PATH,
    FEATURE_COLS,
    TARGET,
    build_preprocessor,
)

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "house_price_model.pkl"
REPORT_DIR = ROOT / "reports"

RANDOM_SEED = 42


def get_models() -> dict:
    models = {
        "Linear Regression": LinearRegression(),
        "Random Forest": RandomForestRegressor(
            n_estimators=200, random_state=RANDOM_SEED, n_jobs=-1
        ),
    }
    try:
        from xgboost import XGBRegressor
        models["XGBoost"] = XGBRegressor(
            n_estimators=300, learning_rate=0.05, max_depth=5,
            subsample=0.9, colsample_bytree=0.9, random_state=RANDOM_SEED,
        )
    except ImportError:
        print("NOTE: xgboost is not installed — skipping it. "
              "Install with: pip install xgboost\n")
    return models


def evaluate(y_true, y_pred) -> dict:
    return {
        "MAE": mean_absolute_error(y_true, y_pred),
        "RMSE": np.sqrt(mean_squared_error(y_true, y_pred)),
        "R2": r2_score(y_true, y_pred),
    }


def main() -> None:
    df = pd.read_csv(CLEAN_DATA_PATH)
    X = df[FEATURE_COLS]
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_SEED
    )
    print(f"Training rows: {len(X_train)} | Testing rows: {len(X_test)}\n")

    results = []
    trained = {}
    for name, model in get_models().items():
        pipeline = Pipeline([
            ("preprocessor", build_preprocessor()),
            ("model", model),
        ])
        pipeline.fit(X_train, y_train)
        metrics = evaluate(y_test, pipeline.predict(X_test))

        results.append({"Model": name, **metrics})
        trained[name] = pipeline
        print(f"Trained: {name}")

    results_df = (
        pd.DataFrame(results)
        .sort_values("R2", ascending=False)
        .reset_index(drop=True)
    )
    print("\n================ MODEL COMPARISON ================")
    print(results_df.round({"MAE": 0, "RMSE": 0, "R2": 4}).to_string(index=False))
    print("==================================================\n")

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(REPORT_DIR / "model_comparison.csv", index=False)

    plt.figure(figsize=(7, 4.5))
    plt.bar(results_df["Model"], results_df["R2"], color="steelblue")
    plt.ylabel("R² score (higher is better)")
    plt.title("Model Comparison — R² on the test set")
    plt.ylim(0, 1)
    for i, v in enumerate(results_df["R2"]):
        plt.text(i, v + 0.01, f"{v:.3f}", ha="center")
    plt.tight_layout()
    plt.savefig(REPORT_DIR / "figures" / "model_comparison.png", dpi=150)
    plt.close()

    best_name = results_df.iloc[0]["Model"]
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(trained[best_name], MODEL_PATH)

    print(f"Best model: {best_name}")
    print(f"Saved to:   {MODEL_PATH}")


if __name__ == "__main__":
    main()
