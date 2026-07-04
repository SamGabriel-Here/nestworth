"""Exploratory data analysis: summary stats and charts saved to reports/figures/."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "housing_data.csv"
FIG_DIR = ROOT / "reports" / "figures"

sns.set_theme(style="whitegrid")


def explore(df: pd.DataFrame) -> None:
    print("--- First 5 rows ---")
    print(df.head(), "\n")

    print("--- Column types & non-null counts ---")
    df.info()

    print("\n--- Summary statistics (numeric columns) ---")
    print(df.describe().round(1), "\n")

    print("--- Missing values per column ---")
    print(df.isna().sum(), "\n")

    print(f"Duplicate rows: {df.duplicated().sum()}")


def save_plots(df: pd.DataFrame) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(8, 5))
    sns.histplot(df["price"], bins=50, kde=True, color="steelblue")
    plt.title("House Price Distribution")
    plt.xlabel("Price ($)")
    plt.ylabel("Number of houses")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "price_distribution.png", dpi=150)
    plt.close()

    plt.figure(figsize=(8, 5))
    sns.scatterplot(data=df, x="area", y="price", hue="location", alpha=0.6, s=25)
    plt.title("Area vs Price (colored by location)")
    plt.xlabel("Area (sq ft)")
    plt.ylabel("Price ($)")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "area_vs_price.png", dpi=150)
    plt.close()

    plt.figure(figsize=(8, 5))
    sns.boxplot(data=df, x="bedrooms", y="price", color="lightseagreen")
    plt.title("Bedrooms vs Price")
    plt.xlabel("Number of bedrooms")
    plt.ylabel("Price ($)")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "bedrooms_vs_price.png", dpi=150)
    plt.close()

    plt.figure(figsize=(8, 6))
    corr = df.select_dtypes("number").corr()
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", vmin=-1, vmax=1)
    plt.title("Correlation Heatmap (numeric features)")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "correlation_heatmap.png", dpi=150)
    plt.close()

    plt.figure(figsize=(8, 5))
    order = df.groupby("location")["price"].mean().sort_values(ascending=False).index
    sns.barplot(data=df, x="location", y="price", order=order,
                errorbar=None, color="coral")
    plt.title("Average Price by Location")
    plt.xlabel("Location")
    plt.ylabel("Average price ($)")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "location_vs_price.png", dpi=150)
    plt.close()

    print(f"Saved 5 figures to: {FIG_DIR}")


def main() -> None:
    df = pd.read_csv(DATA_PATH)
    explore(df)
    save_plots(df)


if __name__ == "__main__":
    main()
