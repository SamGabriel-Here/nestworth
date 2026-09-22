"""Exploratory charts saved to reports/figures/."""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src.pipeline.prepare import RAW_DATA_PATH, ROOT

FIG_DIR = ROOT / "reports" / "figures"


def by_mean(df: pd.DataFrame, col: str):
    return df.groupby(col)["price"].mean().sort_values(ascending=False).index


def main() -> None:
    df = pd.read_csv(RAW_DATA_PATH)
    df.info()
    print(df.describe().round(1))

    charts = {
        "price_distribution": ("House price distribution",
            lambda ax: sns.histplot(df["price"], bins=50, kde=True, ax=ax)),
        "area_vs_price": ("Area vs price, by locality",
            lambda ax: sns.scatterplot(data=df, x="area", y="price", hue="location",
                                       alpha=0.6, s=25, ax=ax)),
        "bedrooms_vs_price": ("Bedrooms vs price",
            lambda ax: sns.boxplot(data=df, x="bedrooms", y="price", ax=ax)),
        "correlation_heatmap": ("Correlation, numeric features",
            lambda ax: sns.heatmap(df.select_dtypes("number").corr(), annot=True, fmt=".2f",
                                   cmap="coolwarm", vmin=-1, vmax=1, ax=ax)),
        "location_vs_price": ("Average price by locality",
            lambda ax: sns.barplot(data=df, x="location", y="price",
                                   order=by_mean(df, "location"), errorbar=None, ax=ax)),
        "city_vs_price": ("Average price by city",
            lambda ax: sns.barplot(data=df, x="city", y="price",
                                   order=by_mean(df, "city"), errorbar=None, ax=ax)),
    }
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    for name, (title, draw) in charts.items():
        fig, ax = plt.subplots(figsize=(8, 5))
        draw(ax)
        ax.set_title(title)
        fig.tight_layout()
        fig.savefig(FIG_DIR / f"{name}.png", dpi=150)
        plt.close(fig)
    print(f"Saved {len(charts)} charts to {FIG_DIR}")


if __name__ == "__main__":
    main()
