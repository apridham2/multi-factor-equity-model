import pandas as pd
import numpy as np
from pathlib import Path


def load_data(file_path):
    df = pd.read_csv(file_path)
    df["date"] = pd.to_datetime(df["date"])
    return df


def compute_momentum(df, lookback=12, skip=1):
    """
    Compute 12-1 momentum:
    cumulative return from t-12 to t-1
    """

    df = df.copy()
    df = df.sort_values(["ticker", "date"])

    # Convert to log returns (numerically stable compounding)
    df["log_ret"] = np.log(1 + df["ret_1m"])

    # Rolling sum of log returns
    rolling_log = (
        df.groupby("ticker")["log_ret"]
        .rolling(window=lookback, min_periods=lookback)
        .sum()
        .reset_index(level=0, drop=True)
    )

    # Convert back to normal return
    df["momentum"] = np.exp(rolling_log) - 1

    # Shift to exclude most recent month
    df["momentum"] = df.groupby("ticker")["momentum"].shift(skip)

    return df


def rank_momentum(df):
    """
    Rank momentum cross-sectionally each month
    """

    df = df.copy()

    df["momentum_rank"] = (
        df.groupby("date")["momentum"]
        .rank(method="first", ascending=False)
    )

    df["momentum_percentile"] = (
        df.groupby("date")["momentum"]
        .rank(pct=True)
    )

    return df


def main():

    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"

    input_file = data_dir / "monthly_price_panel.csv"
    output_file = data_dir / "momentum_factor.csv"

    df = load_data(input_file)

    df = compute_momentum(df)
    df = rank_momentum(df)

    df.to_csv(output_file, index=False)

    print(f"Momentum factor saved to: {output_file.resolve()}")
    print(df.head())


if __name__ == "__main__":
    main()