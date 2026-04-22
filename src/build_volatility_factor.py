import pandas as pd
import numpy as np
from pathlib import Path


def load_data(file_path):
    df = pd.read_csv(file_path)
    df["date"] = pd.to_datetime(df["date"])
    return df


def compute_volatility(df, window=12):
    """
    Compute rolling volatility using monthly returns.
    """

    df = df.copy()
    df = df.sort_values(["ticker", "date"])

    # Rolling standard deviation of monthly returns
    df["volatility"] = (
        df.groupby("ticker")["ret_1m"]
        .rolling(window=window, min_periods=window)
        .std()
        .reset_index(level=0, drop=True)
    )

    return df


def rank_volatility(df):
    """
    Rank volatility cross-sectionally each month.
    Lower volatility = better (ascending=True)
    """

    df = df.copy()

    df["vol_rank"] = (
        df.groupby("date")["volatility"]
        .rank(method="first", ascending=True)
    )

    df["vol_percentile"] = (
        df.groupby("date")["volatility"]
        .rank(pct=True, ascending=True)
    )

    return df


def main():

    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"

    input_file = data_dir / "monthly_price_panel.csv"
    output_file = data_dir / "volatility_factor.csv"

    df = load_data(input_file)

    df = compute_volatility(df)
    df = rank_volatility(df)

    df.to_csv(output_file, index=False)

    print(f"Volatility factor saved to: {output_file.resolve()}")
    print(df.head())


if __name__ == "__main__":
    main()