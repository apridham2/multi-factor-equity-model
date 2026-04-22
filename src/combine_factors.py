import pandas as pd
from pathlib import Path


def load_factor_file(file_path, factor_col, required_cols=None):
    df = pd.read_csv(file_path)
    df["date"] = pd.to_datetime(df["date"])

    base_cols = ["date", "ticker", factor_col]
    if required_cols:
        for col in required_cols:
            if col not in base_cols:
                base_cols.append(col)

    missing = [col for col in base_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {file_path.name}: {missing}")

    return df[base_cols].copy()

"""
Normalize factor signals cross-sectionally by month using percentile ranks.  
Lower volatility = better, so invert percentile rank
"""
def normalize_factors(df):
    df = df.copy()

    # Momentum: high is good
    df["momentum_score"] = (
        df.groupby("date")["momentum"]
        .rank(method="average", pct=True, ascending=True)
    )

    # Volatility: low is good, so invert
    vol_pct = (
        df.groupby("date")["volatility"]
        .rank(method="average", pct=True, ascending=True)
    )
    df["volatility_score"] = 1 - vol_pct

    return df

"""
Combine normalized factor scores into a single composite score.
"""
def combine_scores(df, weights=None):
    df = df.copy()

    if weights is None:
        weights = {
            "momentum_score": 0.5,
            "volatility_score": 0.5
        }

    missing = [col for col in weights if col not in df.columns]
    if missing:
        raise ValueError(f"Missing score columns required for combination: {missing}")

    weight_sum = sum(weights.values())
    if weight_sum == 0:
        raise ValueError("Sum of weights must be greater than zero.")

    # Normalize weights to sum to 1
    weights = {k: v / weight_sum for k, v in weights.items()}

    df["combined_score"] = 0.0
    for col, weight in weights.items():
        df["combined_score"] += df[col] * weight

    return df

"""
Rank the combined factor score cross-sectionally by month.
Higher score = better.
"""
def rank_combined_signal(df):
    df = df.copy()

    df["combined_rank"] = (
        df.groupby("date")["combined_score"]
        .rank(method="first", ascending=False)
    )

    df["combined_percentile"] = (
        df.groupby("date")["combined_score"]
        .rank(method="average", pct=True, ascending=True)
    )

    return df

"""
Merge individual factor files into one combined factor dataset.
"""
def build_combined_factor(momentum_df, volatility_df):
    # Keep forward return for later backtesting from one side only
    merge_cols = ["date", "ticker", "momentum", "ret_fwd_1m"]
    momentum_subset = momentum_df[merge_cols].copy()

    vol_subset = volatility_df[["date", "ticker", "volatility"]].copy()

    df = momentum_subset.merge(
        vol_subset,
        on=["date", "ticker"],
        how="inner",
        validate="one_to_one"
    )

    return df


def main():
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    data_dir.mkdir(exist_ok=True)

    momentum_file = data_dir / "momentum_factor.csv"
    volatility_file = data_dir / "volatility_factor.csv"
    output_file = data_dir / "combined_factor.csv"

    momentum_df = load_factor_file(
        momentum_file,
        factor_col="momentum",
        required_cols=["ret_fwd_1m"]
    )

    volatility_df = load_factor_file(
        volatility_file,
        factor_col="volatility"
    )

    combined = build_combined_factor(momentum_df, volatility_df)

    # Drop rows where either factor is unavailable
    combined = combined.dropna(subset=["momentum", "volatility"]).copy()

    combined = normalize_factors(combined)

    combined = combine_scores(
        combined,
        weights={
            "momentum_score": 0.5,
            "volatility_score": 0.5
        }
    )

    combined = rank_combined_signal(combined)

    combined = combined.sort_values(["date", "combined_rank"]).reset_index(drop=True)

    combined.to_csv(output_file, index=False)

    print(f"Combined factor saved to: {output_file.resolve()}")
    print("\nSample output:")
    print(
        combined[
            [
                "date",
                "ticker",
                "momentum",
                "volatility",
                "momentum_score",
                "volatility_score",
                "combined_score",
                "combined_rank",
                "combined_percentile",
                "ret_fwd_1m"
            ]
        ].head(10)
    )


if __name__ == "__main__":
    main()