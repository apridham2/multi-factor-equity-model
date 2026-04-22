import pandas as pd
from pathlib import Path

def load_factor_file(file_path, factor_col, required_cols=None):
    df = pd.read_csv(file_path)
    df["date"] = pd.to_datetime(df["date"])

    keep_cols = ["date", "ticker", factor_col]
    if required_cols:
        for col in required_cols:
            if col not in keep_cols:
                keep_cols.append(col)

    missing = [col for col in keep_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {file_path.name}: {missing}")

    return df[keep_cols].copy()

"""
Merge momentum and volatility factors into one dataset.
"""
def build_base_dataframe(momentum_df, volatility_df):
    momentum_subset = momentum_df[["date", "ticker", "momentum", "ret_fwd_1m"]].copy()
    volatility_subset = volatility_df[["date", "ticker", "volatility"]].copy()

    df = momentum_subset.merge(
        volatility_subset,
        on=["date", "ticker"],
        how="inner",
        validate="one_to_one"
    )

    df = df.dropna(subset=["momentum", "volatility"]).copy()
    return df

"""
Keep only the top % of stocks by momentum.
"""
def create_momentum_filter(df, top_pct=0.30):
    df = df.copy()

    df["momentum_percentile"] = (
        df.groupby("date")["momentum"]
        .rank(method="average", pct=True, ascending=True)
    )

    threshold = 1 - top_pct
    df["passes_momentum_filter"] = df["momentum_percentile"] >= threshold

    return df

"""
Within the momentum-filtered subset, rank by volatility.
"""
def rank_filtered_volatility(df):
    df = df.copy()

    filtered = df[df["passes_momentum_filter"]].copy()

    filtered["filtered_vol_rank"] = (
        filtered.groupby("date")["volatility"]
        .rank(method="first", ascending=True)
    )

    filtered["filtered_vol_percentile"] = (
        filtered.groupby("date")["volatility"]
        .rank(method="average", pct=True, ascending=False)
    )
   
    filtered["combined_score"] = filtered["filtered_vol_percentile"]

    filtered["combined_rank"] = (
        filtered.groupby("date")["combined_score"]
        .rank(method="first", ascending=False)
    )

    filtered["combined_percentile"] = (
        filtered.groupby("date")["combined_score"]
        .rank(method="average", pct=True, ascending=True)
    )

    return filtered


def main():
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    data_dir.mkdir(exist_ok=True)

    momentum_file = data_dir / "momentum_factor.csv"
    volatility_file = data_dir / "volatility_factor.csv"
    output_file = data_dir / "combined_factor_filtered.csv"

    momentum_df = load_factor_file(
        momentum_file,
        factor_col="momentum",
        required_cols=["ret_fwd_1m"]
    )

    volatility_df = load_factor_file(
        volatility_file,
        factor_col="volatility"
    )

    df = build_base_dataframe(momentum_df, volatility_df)

    # Step 1: filter to top momentum names
    df = create_momentum_filter(df, top_pct=0.30)

    # Step 2: rank low-volatility names within filtered subset
    filtered_df = rank_filtered_volatility(df)

    filtered_df = filtered_df.sort_values(["date", "combined_rank"]).reset_index(drop=True)

    filtered_df.to_csv(output_file, index=False)

    print(f"Filtered combined factor saved to: {output_file.resolve()}")
    print("\nSample output:")
    print(
        filtered_df[
            [
                "date",
                "ticker",
                "momentum",
                "volatility",
                "momentum_percentile",
                "passes_momentum_filter",
                "filtered_vol_rank",
                "filtered_vol_percentile",
                "combined_score",
                "combined_rank",
                "combined_percentile",
                "ret_fwd_1m"
            ]
        ].head(10)
    )


if __name__ == "__main__":
    main()