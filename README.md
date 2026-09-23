# NestWorth

Home valuations across 13 Indian cities, eight kinds of locality and six home types,
from a studio to a villa. Describe a home and NestWorth returns:

- a price in lakh or crore with a **calibrated 90% range**;
- the features pushing the price up or down;
- the same home priced **in every city**, and **at other sizes** (a price-against-size chart);
- the five most similar listings.

Every control updates the valuation live, swaps the room photograph to match the furnishing,
and redraws a section through the home: stilt parking under an apartment, a penthouse's
terrace, a villa's roof, a floor per storey, a bed per bedroom and a car per parking spot.
The answers live in the URL, so a valuation can be shared by link, and **Download report**
prints a one-page A4 summary.

**Live:** https://samgabrielofficially-nestworth.hf.space

![NestWorth: a full-bleed photograph of a residential tower under the headline "What is your home worth?"](docs/screenshot-form.png)

![The valuation: room photograph, estimate and 90% range beside the numbered specification](docs/screenshot-estimate.png)

![The section drawing in the dark theme: floors, rooms, furniture, parking and the city's landmark, with a title block and level datums](docs/screenshot-drawing.png)

A scikit-learn pipeline with XGBoost, served by FastAPI with a hand-built HTML/CSS/JS
frontend, running in Docker on Hugging Face Spaces.

## Results

Three models compared on the same 80/20 split (`artifacts/metrics.csv`):

| Model | MAE (₹) | RMSE (₹) | R² |
|---|---:|---:|---:|
| **XGBoost** | 19.6 L | 46.5 L | **0.915** |
| Random Forest | 25.6 L | 57.0 L | 0.873 |
| Linear Regression | 46.0 L | 76.6 L | 0.771 |

The tree models win because city, locality and home type multiply the price *per square
foot*, an interaction a linear model can't capture. The 90% interval held **88.9%** of
held-out prices (the conformal guarantee is 90% on average; one test split of about 1,200
homes lands within sampling noise of it).

## Project layout

```
main.py                  entry point: serves the app on :7860
pyproject.toml           dependencies (runtime, [train], [dev])
Dockerfile               the image Hugging Face Spaces runs
src/
  pipeline/
    generate.py          synthetic dataset -> data/housing_data.csv
    prepare.py           cleaning + the model Pipeline (features, encoding, scaling)
    eda.py               six charts -> reports/figures/
    train.py             compare models, fit the interval -> artifacts/
  predictor.py           loads artifacts once; one home -> full valuation
  api/
    app.py               FastAPI: POST /api/predict + the static frontend
    static/              index.html, style.css, app.js, scene.js (the section drawing), img/, fonts/
artifacts/               model.pkl, interval.pkl, metrics.csv
data/                    housing_data.csv (raw), housing_clean.csv
tests/                   test_pipeline.py, test_api.py
```

## Run it

```bash
git clone https://github.com/SamGabriel-Here/nestworth.git
cd nestworth
python -m venv .venv && source .venv/bin/activate
pip install -e ".[train,dev]"

python main.py                      # http://localhost:7860
```

Rebuild everything from scratch:

```bash
python -m src.pipeline.generate     # data/housing_data.csv
python -m src.pipeline.eda          # reports/figures/*.png
python -m src.pipeline.prepare      # data/housing_clean.csv
python -m src.pipeline.train        # artifacts/ + model_comparison.png
pytest
```

Or run the container: `docker build -t nestworth . && docker run -p 7860:7860 nestworth`.

## How it works

**Data.** `generate.py` creates about 6,000 listings priced at each city's rate per square
foot (from about ₹4,500 in Indore to about ₹18,000 in Mumbai), multiplied by locality and
home type, then adjusted for rooms, age, parking, road access and furnishing. Each type has
its own shape: studios are one small room, villas and penthouses are large. It deliberately adds missing values, duplicates
and outliers so the cleaning step has real work to do. The data is synthetic; the site
says so on every valuation.

| Column | Description |
|---|---|
| `area` | Built-up area in sq ft |
| `bedrooms`, `bathrooms`, `stories` | Room and floor counts |
| `city` | Mumbai, Delhi, Bangalore, Pune, Hyderabad, Chennai, Chandigarh, Kochi, Ahmedabad, Kolkata, Jaipur, Lucknow, Indore |
| `location` | City Centre, Prime Suburb, Suburb, Outskirts, Premium Township, Gated Community, Near Metro, Waterfront |
| `property_type` | Apartment, Studio, Row House, Independent House, Villa, Penthouse |
| `house_age` | Age in years |
| `parking` | Parking spots |
| `main_road` | Faces a main road (yes/no) |
| `furnishing_status` | furnished / semi-furnished / unfurnished |
| `price` | Target: sale price in ₹ |

**Cleaning** (`prepare.py`):
- missing values are filled with the median (numeric) or mode (categorical);
- duplicates are dropped;
- `price` and `area` outliers are capped with the IQR rule on the log scale, so genuine luxury homes survive.

**Model pipeline.** Everything the model needs happens inside one scikit-learn `Pipeline`,
so the saved model handles raw input exactly as it did in training:
- feature engineering (`total_rooms`, `is_new`);
- one-hot encoding and scaling;
- the regressor.

**90% range.** The range comes from conformalized quantile regression:
- two XGBoost quantile models (5th and 95th percentile) are fit on part of the training set;
- they're widened on a held-out calibration split until 90% of unseen prices fall inside.

The range adapts to the home: a few lakh wide for a budget flat, over a crore for a premium one.

**Reasons.** Each number is reset in turn to its median, and each category (city, locality,
type, road, furnishing) is averaged over all its options; the home is re-priced each time.
The change is that feature's contribution. The top five by size are shown.

**Comparables.** The five listings closest in area of the same type, city and locality
(widening to the city, then the whole city, when there are fewer than 8).

**API.** `POST /api/predict` validates input with Pydantic and returns:
- `estimate` and `price_per_sqft`;
- `interval` (`lo`, `hi`, `coverage`);
- the locality's price spread, `segment` (10th, 50th and 90th percentile);
- `factors` and `comparables`;
- `curve`, the estimate and 90% range at 25 areas;
- `cities`, the same home priced in every city, highest first;
- `r2` and `mae` from the trained model.

Out-of-range input returns 422.

## Design

A formal, editorial layout on a 12-column grid: a full-bleed photograph, a numbered
specification form beside a sticky estimate, and a live section drawing of the home in
architectural line style. Light and Dark themes swap the photographs (day and night).
Type is Gloock for headlines and figures with Schibsted Grotesk for text, both self-hosted
(SIL Open Font License, `src/api/static/fonts/OFL-*.txt`). The mark is an N whose walls meet
in a roof pitch (`src/api/static/favicon.svg`).

Photography, all free under the [Unsplash License](https://unsplash.com/license):

| File | Photo | Photographer |
|---|---|---|
| `img/hero-day.webp` | [Residential towers](https://unsplash.com/photos/04FfOI_aYy4) | Vaibhav Surana |
| `img/hero-night.webp` | [House at dusk](https://unsplash.com/photos/hmlP-v0vJ5o) | Elite prop |
| `img/room-unfurnished.webp` | [Empty room](https://unsplash.com/photos/4YhNRgL59Fc) | Christian Lue |
| `img/room-semi.webp` | [Living room](https://unsplash.com/photos/CfBDgt5BafU) | Dinesh Lunked |
| `img/room-furnished.webp` | [Furnished living room](https://unsplash.com/photos/CgA03H9jCKw) | Pyx Photography |

## Possible improvements

- Hyperparameter search and k-fold cross-validation
- A real dataset with richer features
- SHAP attributions in place of single-feature ablation

## Stack

Python, pandas, NumPy, scikit-learn, XGBoost, FastAPI, Pydantic, Matplotlib, Seaborn,
pytest, Docker. Deployed on Hugging Face Spaces.

## License

MIT, see [LICENSE](LICENSE).
