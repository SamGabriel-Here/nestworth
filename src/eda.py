"""Exploratory data analysis: summary stats and charts saved to reports/figures/."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from data_preprocessing import clean_dataset, load_data

ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "reports" / "figures"

sns.set_theme(style="whitegrid")


def explore(df: pd.DataFrame) -> None:
    print("--- First 5 rows ---")
    print(df.head(), "\n")

    print("--- Column types & non-null counts ---")
    df.info()

    print("\n--- Summary statistics (numeric columns) ---")
    print(df.describe().round(1), "\n")

    print(f"Unique localities: {df['location'].nunique()}")


def save_plots(df: pd.DataFrame) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    df = df.assign(price_lakh=df["price"] / 1_00_000)

    plt.figure(figsize=(8, 5))
    sns.histplot(df["price_lakh"].clip(upper=df["price_lakh"].quantile(0.99)),
                 bins=50, kde=True, color="steelblue")
    plt.title("House Price Distribution")
    plt.xlabel("Price (₹ Lakh)")
    plt.ylabel("Number of houses")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "price_distribution.png", dpi=150)
    plt.close()

    plt.figure(figsize=(8, 5))
    sns.scatterplot(data=df, x="area", y="price_lakh", hue="bedrooms",
                    alpha=0.5, s=20, palette="viridis")
    plt.title("Area vs Price (colored by BHK)")
    plt.xlabel("Area (sq ft)")
    plt.ylabel("Price (₹ Lakh)")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "area_vs_price.png", dpi=150)
    plt.close()

    plt.figure(figsize=(8, 5))
    sns.boxplot(data=df, x="bedrooms", y="price_lakh", color="lightseagreen")
    plt.title("Bedrooms (BHK) vs Price")
    plt.xlabel("Bedrooms (BHK)")
    plt.ylabel("Price (₹ Lakh)")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "bedrooms_vs_price.png", dpi=150)
    plt.close()

    plt.figure(figsize=(8, 6))
    corr = df[["area", "bedrooms", "bathrooms", "balcony", "price"]].corr()
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", vmin=-1, vmax=1)
    plt.title("Correlation Heatmap (numeric features)")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "correlation_heatmap.png", dpi=150)
    plt.close()

    plt.figure(figsize=(8, 6))
    top = df["location"].value_counts().head(15).index
    order = (df[df["location"].isin(top)].groupby("location")["price_lakh"]
             .median().sort_values(ascending=False).index)
    sns.barplot(data=df[df["location"].isin(top)], y="location", x="price_lakh",
                order=order, errorbar=None, color="coral")
    plt.title("Median Price by Locality (15 most common)")
    plt.xlabel("Median price (₹ Lakh)")
    plt.ylabel("Locality")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "location_vs_price.png", dpi=150)
    plt.close()

    plt.figure(figsize=(8, 5))
    order = (df.groupby("area_type")["price_lakh"].median()
             .sort_values(ascending=False).index)
    sns.boxplot(data=df, x="area_type", y="price_lakh", order=order,
                color="mediumseagreen")
    plt.title("Price by Area Type")
    plt.xlabel("Area type")
    plt.ylabel("Price (₹ Lakh)")
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "area_type_vs_price.png", dpi=150)
    plt.close()

    print(f"Saved 6 figures to: {FIG_DIR}")


def main() -> None:
    df = clean_dataset(load_data())
    explore(df)
    save_plots(df)


if __name__ == "__main__":
    main()
