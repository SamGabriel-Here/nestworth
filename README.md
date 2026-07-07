# NestWorth

House price estimates for Bengaluru. Predicts prices from property features
(locality, built-up area, BHK, bathrooms, area type, etc.) using scikit-learn,
with a Streamlit app for making predictions interactively.

**Live demo:** https://nestworth.streamlit.app

## Dataset

The data (`data/bengaluru_house_data.csv`, ~13,300 listings) is the public
[Bengaluru house price dataset](https://www.kaggle.com/datasets/amitabhajoy/bengaluru-house-price-data)
scraped from a property portal. It is real and genuinely messy — which is the
point: the cleaning step has to do real work.

| Column | Description |
|---|---|
| `total_sqft` | Built-up area — free text, e.g. `1200`, `1133 - 1384`, `34Sq. Meter` |
| `size` | Bedrooms as text, e.g. `2 BHK`, `4 Bedroom` |
| `bath`, `balcony` | Bathroom / balcony counts (with missing values) |
| `location` | One of ~1,300 Bengaluru localities |
| `area_type` | Super built-up / Built-up / Plot / Carpet area |
| `availability` | `Ready To Move` or a possession date |
| `society` | Mostly missing — dropped |
| `price` | Target — price in **lakhs** of rupees |

Cleaning turns this into `data/housing_clean.csv` (~7,300 rows, 223 localities).

## Setup

```bash
git clone https://github.com/SamGabriel-Here/nestworth.git
cd nestworth

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Running the pipeline

```bash
python src/data_preprocessing.py   # clean raw -> data/housing_clean.csv
python src/eda.py                  # save charts to reports/figures/
python src/train_model.py          # train + compare -> models/house_price_model.pkl
streamlit run app/app.py           # web app
```

## How it works

**EDA** (`src/eda.py`) saves six charts to `reports/figures/`: price
distribution, area vs price by BHK, bedrooms vs price, a correlation heatmap,
median price for the most common localities, and price by area type. Area and
locality drive price the most; the price distribution is heavily right-skewed.

**Preprocessing** (`src/data_preprocessing.py`) — most of the work is turning
the messy raw columns into something a model can use:

- `size` → `bedrooms` (parse the leading number out of `"2 BHK"` / `"4 Bedroom"`)
- `total_sqft` → `area` (average ranges like `"1133 - 1384"`, drop odd units)
- `availability` → `ready_to_move` flag; `society` dropped (mostly missing)
- missing `bath` / `balcony` filled with the median
- **locality cardinality** cut from ~1,300 to 223 by bucketing rare localities
  (≤10 listings) into `Other`
- **outlier removal**: drop listings beyond one std of the per-sq-ft price
  *within their locality*, and the classic BHK check — an N-BHK unit priced per
  sq ft below the typical (N−1)-BHK nearby is dropped as an anomaly
- one-hot encoding for categoricals, `StandardScaler` for numerics, both inside
  a scikit-learn `Pipeline` so the saved model preprocesses new inputs the same
  way it was trained

**Training** (`src/train_model.py`) compares three models on an 80/20 split
and saves whichever scores highest on the test set:

| Model | MAE (₹) | RMSE (₹) | R² |
|---|---:|---:|---:|
| XGBoost | 16.5 Lakh | 29.9 Lakh | 0.863 |
| Linear Regression | 17.9 Lakh | 33.9 Lakh | 0.824 |
| Random Forest | 15.8 Lakh | 38.9 Lakh | 0.769 |

XGBoost wins on R² and RMSE — locality and area interact (locality changes the
price *per square foot*), which the tree model captures better. Random Forest
has the lowest MAE but the worst RMSE: it nails typical homes but misses harder
on the expensive tail. Exact numbers vary slightly by library version.

Training also fits a **90% prediction interval** via conformalized quantile
regression (CQR): gradient-boosted regressors for the 5th and 95th percentiles,
then a conformal calibration step on held-out data that corrects the bounds to
hit the target coverage regardless of how well the quantile models are
specified. On the test set it lands at ~90% empirical coverage, and the interval
is *adaptive* — tens of lakhs wide for a modest flat, over a crore for a premium
home. The point model's own train/test split is untouched, so the headline R²
is unaffected.

**App** (`app/app.py`) — a Streamlit form for the property features. On submit it
returns the estimate as a headline figure with price per sq ft, the 90%
prediction interval, and the model's R². Below that:

- **How it compares** — where the estimate sits within the 10th–90th-percentile
  price range of comparable homes in the same locality, shown as a bar.
- **Why this price?** — each feature's contribution to the estimate, measured by
  setting that feature back to a typical value and re-predicting (single-feature
  ablation against a median/mode baseline listing).
- **Comparable homes** — the closest listings by size in the same locality.

## Possible improvements

- Hyperparameter tuning (`GridSearchCV`) and k-fold cross-validation
- Richer features (geocoded lat/long, distance to tech parks, amenities)
- Proper SHAP/Shapley attributions for the explanation panel (in place of the
  single-feature ablation it uses now)

## Stack

Python, pandas, NumPy, Matplotlib, Seaborn, scikit-learn, XGBoost, Streamlit, joblib
