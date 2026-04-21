import pandas as pd
import yfinance as yf
from pathlib import Path


def load_tickers(ticker_file):
    df = pd.read_csv(ticker_file)

    if "ticker" not in df.columns:
        raise ValueError(f"'ticker' column not found in {ticker_file}")

    tickers = (
        df["ticker"]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )

    if not tickers:
        raise ValueError("No tickers found in ticker file.")

    return tickers


def download_daily_prices(tickers, start_date="2018-01-01", end_date=None):
    """
    Download daily price data and return it in long format.
    """
    print(f"Downloading data for {len(tickers)} tickers...")

    data = yf.download(
        tickers=tickers,
        start=start_date,
        end=end_date,
        auto_adjust=False,
        progress=True,
        threads=True
    )

    if data.empty:
        raise ValueError("No data downloaded from yfinance.")

    # yfinance returns a wide DataFrame with MultiIndex columns for multi-ticker downloads.
    # We stack it into long format so ticker labels stay correct.
    if isinstance(data.columns, pd.MultiIndex):
        # Expect structure like:
        # level 0 = field (Open, High, Low, Close, Adj Close, Volume)
        # level 1 = ticker
        data = data.stack(level=1, future_stack=True).reset_index()
        data.columns = [str(col).strip().lower().replace(" ", "_") for col in data.columns]

        # After stacking, yfinance usually gives:
        # ['date', 'ticker', 'open', 'high', 'low', 'close', 'adj_close', 'volume']
        # But depending on version, the ticker column might be named level_1
        if "ticker" not in data.columns:
            possible_ticker_cols = [c for c in data.columns if "level" in c]
            if possible_ticker_cols:
                data = data.rename(columns={possible_ticker_cols[0]: "ticker"})
            else:
                raise ValueError("Could not identify ticker column after reshaping yfinance data.")
    else:
        # Single ticker fallback
        data = data.reset_index()
        data.columns = [str(col).strip().lower().replace(" ", "_") for col in data.columns]
        data["ticker"] = tickers[0]

    keep_cols = ["date", "ticker", "open", "high", "low", "close", "adj_close", "volume"]
    existing_cols = [c for c in keep_cols if c in data.columns]
    data = data[existing_cols].copy()

    data["date"] = pd.to_datetime(data["date"])
    data["ticker"] = data["ticker"].astype(str).str.strip()

    data = data.sort_values(["ticker", "date"]).reset_index(drop=True)

    return data


def create_monthly_panel(daily_prices):
    """
    Convert daily data to month-end data and calculate:
    - ret_1m: backward-looking 1-month return
    - ret_fwd_1m: forward 1-month return
    """
    df = daily_prices.copy()

    if "adj_close" in df.columns:
        price_col = "adj_close"
    elif "close" in df.columns:
        price_col = "close"
    else:
        raise ValueError("No valid price column found. Expected 'adj_close' or 'close'.")

    df = df.dropna(subset=[price_col])
    df = df.sort_values(["ticker", "date"]).reset_index(drop=True)

    monthly_frames = []

    for ticker, grp in df.groupby("ticker", sort=True):
        temp = (
            grp.set_index("date")
            .resample("ME")
            .last()
            .reset_index()
        )

        temp["ticker"] = ticker
        monthly_frames.append(temp)

    if not monthly_frames:
        raise ValueError("No monthly data could be created.")

    monthly = pd.concat(monthly_frames, ignore_index=True)
    monthly = monthly.sort_values(["ticker", "date"]).reset_index(drop=True)

    monthly["ret_1m"] = monthly.groupby("ticker")[price_col].pct_change()
    monthly["ret_fwd_1m"] = monthly.groupby("ticker")["ret_1m"].shift(-1)

    return monthly


def main():
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    data_dir.mkdir(exist_ok=True)

    ticker_file = data_dir / "sp500_tickers.csv"

    tickers = load_tickers(ticker_file)

    # Limit to first 200 names for version 1
    tickers = tickers[:200]

    print(f"Using {len(tickers)} tickers")
    print("Sample input tickers:", tickers[:10])

    # Download daily prices
    daily_prices = download_daily_prices(
        tickers=tickers,
        start_date="2018-01-01",
        end_date=None
    )

    print("\nSample downloaded tickers:")
    print(daily_prices["ticker"].drop_duplicates().head(10).tolist())

    daily_output = data_dir / "daily_prices.csv"
    daily_prices.to_csv(daily_output, index=False)
    print(f"Saved daily data to: {daily_output.resolve()}")

    # Create monthly panel
    monthly_panel = create_monthly_panel(daily_prices)

    monthly_output = data_dir / "monthly_price_panel.csv"
    monthly_panel.to_csv(monthly_output, index=False)
    print(f"Saved monthly panel to: {monthly_output.resolve()}")

    print("\nMonthly panel sample:")
    print(monthly_panel.head())


if __name__ == "__main__":
    main()