import pandas as pd
import requests
from io import StringIO
from pathlib import Path


def get_sp500_tickers(save_csv=True):
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    tables = pd.read_html(StringIO(response.text))
    sp500_table = tables[0]

    tickers = (
        sp500_table["Symbol"]
        .astype(str)
        .str.replace(".", "-", regex=False)
        .tolist()
    )

    if save_csv:
        base_dir = Path(__file__).parent
        out_dir = base_dir / "data"
        out_dir.mkdir(exist_ok=True)

        output_file = out_dir / "sp500_tickers.csv"
        pd.DataFrame({"ticker": tickers}).to_csv(output_file, index=False)

        print(f"Ticker file saved to: {output_file.resolve()}")

    return tickers


if __name__ == "__main__":
    tickers = get_sp500_tickers()

    print(f"Total tickers pulled: {len(tickers)}")
    print("Sample tickers:", tickers[:10])