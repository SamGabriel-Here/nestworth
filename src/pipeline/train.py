"""Train and compare regressors, save the best one plus a 90% prediction interval."""

import joblib
import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor

from src.pipeline.prepare import CLEAN_DATA_PATH, INPUT_COLS, ROOT, TARGET, build_pipeline

ARTIFACTS = ROOT / "artifacts"
MODEL_PATH = ARTIFACTS / "model.pkl"
INTERVAL_PATH = ARTIFACTS / "interval.pkl"
METRICS_PATH = ARTIFACTS / "metrics.csv"
FIG_DIR = ROOT / "reports" / "figures"

SEED = 42
COVERAGE = 0.90


def xgb(**kw) -> XGBRegressor:
    return XGBRegressor(n_estimators=300, learning_rate=0.05, max_depth=5,
                        subsample=0.9, colsample_bytree=0.9, random_state=SEED, **kw)


def fit_interval(X_train, y_train, X_test, y_test):
    """Conformalized Quantile Regression (Romano et al., 2019).

    Quantile models give the band's shape; a held-out calibration split
    widens it by q so coverage holds even if the quantile models are off.
    """
    alpha = 1 - COVERAGE
    X_fit, X_cal, y_fit, y_cal = train_test_split(X_train, y_train, test_size=0.25,
                                                  random_state=SEED)
    lo = build_pipeline(xgb(objective="reg:quantileerror", quantile_alpha=alpha / 2))
    hi = build_pipeline(xgb(objective="reg:quantileerror", quantile_alpha=1 - alpha / 2))
    lo.fit(X_fit, y_fit)
    hi.fit(X_fit, y_fit)

    y_cal = y_cal.to_numpy()
    scores = np.maximum(lo.predict(X_cal) - y_cal, y_cal - hi.predict(X_cal))
    n = len(scores)
    q = float(np.quantile(scores, min(1.0, np.ceil((n + 1) * COVERAGE) / n), method="higher"))

    y_test = y_test.to_numpy()
    lo_t, hi_t = lo.predict(X_test) - q, hi.predict(X_test) + q
    coverage = float(np.mean((y_test >= lo_t) & (y_test <= hi_t)))
    return {"lo": lo, "hi": hi, "q": q, "coverage": COVERAGE}, coverage, float(np.mean(hi_t - lo_t))


def main() -> None:
    df = pd.read_csv(CLEAN_DATA_PATH)
    X_train, X_test, y_train, y_test = train_test_split(
        df[INPUT_COLS], df[TARGET], test_size=0.2, random_state=SEED)

    candidates = {
        "Linear Regression": LinearRegression(),
        "Random Forest": RandomForestRegressor(n_estimators=200, random_state=SEED, n_jobs=-1),
        "XGBoost": xgb(),
    }
    rows, fitted = [], {}
    for name, model in candidates.items():
        pipe = build_pipeline(model).fit(X_train, y_train)
        pred = pipe.predict(X_test)
        rows.append({"Model": name, "MAE": mean_absolute_error(y_test, pred),
                     "RMSE": np.sqrt(mean_squared_error(y_test, pred)),
                     "R2": r2_score(y_test, pred)})
        fitted[name] = pipe

    metrics = pd.DataFrame(rows).sort_values("R2", ascending=False).reset_index(drop=True)
    print(metrics.round({"MAE": 0, "RMSE": 0, "R2": 4}).to_string(index=False))

    ARTIFACTS.mkdir(exist_ok=True)
    metrics.to_csv(METRICS_PATH, index=False)
    joblib.dump(fitted[metrics.iloc[0]["Model"]], MODEL_PATH)

    bundle, coverage, width = fit_interval(X_train, y_train, X_test, y_test)
    joblib.dump(bundle, INTERVAL_PATH)
    print(f"Best: {metrics.iloc[0]['Model']} | 90% interval coverage {coverage:.1%}, "
          f"mean width {width / 1e5:.1f} Lakh")

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(7, 4.5))
    plt.bar(metrics["Model"], metrics["R2"], color="steelblue")
    plt.ylabel("R² on test set")
    plt.ylim(0, 1)
    for i, v in enumerate(metrics["R2"]):
        plt.text(i, v + 0.01, f"{v:.3f}", ha="center")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "model_comparison.png", dpi=150)
    plt.close()


if __name__ == "__main__":
    main()
