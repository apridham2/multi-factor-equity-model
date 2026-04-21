import pandas as pd
import numpy as np
from pathlib import Path


def load_data(file_path):
    df = pd.read_csv(file_path)
    df["date"] = pd.to_datetime(df["date"])
    return df


def create_deciles(df):
    df = df.copy()

    # Need both signal and next-month return
    df = df.dropna(subset=["momentum", "ret_fwd_1m"])

    # Create momentum deciles within each month
    df["decile"] = (
        df.groupby("date")["momentum"]
        .transform(lambda x: pd.qcut(x, 10, labels=False, duplicates="drop"))
    )

    return df


def compute_portfolio_returns(df):
    """
    Equal-weight forward returns for each decile by month.
    """
    port_ret = (
        df.groupby(["date", "decile"])["ret_fwd_1m"]
        .mean()
        .reset_index()
    )

    pivot = port_ret.pivot(index="date", columns="decile", values="ret_fwd_1m")

    # Rename columns for readability
    pivot.columns = [f"decile_{int(col)}" for col in pivot.columns]

    return pivot


def compute_long_short(pivot):
    """
    High-momentum minus low-momentum portfolio.
    """
    pivot = pivot.copy()

    decile_cols = [c for c in pivot.columns if c.startswith("decile_")]

    if len(decile_cols) < 2:
        raise ValueError("Need at least two decile portfolios to compute long-short returns.")

    # Sort decile columns numerically
    decile_cols = sorted(decile_cols, key=lambda x: int(x.split("_")[1]))

    low_col = decile_cols[0]
    high_col = decile_cols[-1]

    pivot["long_short"] = pivot[high_col] - pivot[low_col]

    return pivot


def compute_cumulative_returns(pivot):
    """
    Convert monthly returns into cumulative growth series.
    """
    cumulative = (1 + pivot).cumprod()
    return cumulative


def summarize_performance(pivot):
    """
    Print summary performance metrics for each portfolio column.
    Assumes monthly returns.
    """
    print("\nPerformance Summary:")

    summary_rows = []

    for col in pivot.columns:
        series = pivot[col].dropna()

        if len(series) == 0:
            continue

        ann_return = (1 + series.mean()) ** 12 - 1
        ann_vol = series.std() * np.sqrt(12)

        if ann_vol != 0:
            sharpe = ann_return / ann_vol
        else:
            sharpe = np.nan

        cumulative_return = (1 + series).prod() - 1

        summary_rows.append({
            "portfolio": col,
            "annualized_return": ann_return,
            "annualized_volatility": ann_vol,
            "sharpe_ratio": sharpe,
            "cumulative_return": cumulative_return,
            "num_months": len(series)
        })

    summary_df = pd.DataFrame(summary_rows)
    print(summary_df)

    return summary_df


def main():
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"

    input_file = data_dir / "momentum_factor.csv"
    output_file = data_dir / "momentum_backtest.csv"
    summary_file = data_dir / "momentum_backtest_summary.csv"
    cumulative_file = data_dir / "momentum_cumulative_returns.csv"

    df = load_data(input_file)

    df = create_deciles(df)

    pivot = compute_portfolio_returns(df)

    pivot = compute_long_short(pivot)

    cumulative = compute_cumulative_returns(pivot)
    summary = summarize_performance(pivot)

    pivot.to_csv(output_file)
    summary.to_csv(summary_file, index=False)
    cumulative.to_csv(cumulative_file)

    print(f"\nBacktest saved to: {output_file.resolve()}")
    print(f"Summary saved to: {summary_file.resolve()}")
    print(f"Cumulative returns saved to: {cumulative_file.resolve()}")

    print("\nBacktest sample:")
    print(pivot.head())


if __name__ == "__main__":
    main()