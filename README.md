# Multi-Factor Equity Model (In Progress)

## Overview

This project builds a systematic equity factor model from first principles, following a full quantitative workflow from universe construction through factor backtesting.

The current implementation includes:

* A reproducible data pipeline
* A monthly return panel
* A fully constructed and tested momentum factor

Additional factors and multi-factor combination are under development.

---

## Project Structure

```text
multi-factor-equity-model/
├── data/                     # Generated data (not tracked)
├── src/
│   ├── get_sp500_tickers.py
│   ├── get_price_data.py
│   ├── build_momentum_factor.py
│   └── backtest_momentum.py
├── README.md
├── LICENSE
└── .gitignore
```

---

## Methodology

### 1. Define Stock Universe

* Universe: S&P 500 constituents (current snapshot)
* Tickers are scraped and cleaned for compatibility
* Serves as a proxy for a liquid large-cap universe

**Limitation:**
This approach introduces survivorship bias, as historical index membership is not point-in-time.

---

### 2. Data Pipeline

* Daily price data is downloaded using `yfinance`
* Data is converted into a monthly panel using month-end prices
* Returns are computed as:

```text
ret_1m       = backward-looking 1-month return  
ret_fwd_1m   = forward-looking 1-month return
```

Forward returns are used as the target variable to ensure proper time alignment and avoid look-ahead bias.

---

### 3. Momentum Factor Construction

* Factor: 12-1 momentum
* Definition: cumulative return from t-12 to t-1
* The most recent month is excluded to avoid short-term reversal effects

Implementation details:

* Log returns are used for stable compounding
* Rolling windows are applied per ticker
* The signal is shifted to align with future returns

---

### 4. Backtesting Framework

For each month:

1. Stocks are ranked by momentum
2. The universe is divided into deciles (10 groups)
3. Equal-weight portfolios are constructed
4. Performance is evaluated using next-month returns (`ret_fwd_1m`)

Outputs include:

* Decile portfolio returns
* Long-short portfolio (top decile minus bottom decile)

---

## Momentum Factor Results

* The highest momentum decile shows strong outperformance
* The long-short portfolio produces positive returns (approximately 8–9% annualized)
* The Sharpe ratio is positive but moderate (approximately 0.35)

### Observations

* The momentum signal demonstrates predictive power
* Performance is strongest in the top decile
* Lower deciles exhibit relatively strong returns, reducing overall spread

Potential drivers include:

* Large-cap bias from the S&P 500 universe
* Survivorship bias
* A broadly positive market environment during the sample period

---

## Key Learnings

* Proper time alignment (signal at time t predicting returns at time t+1) is critical
* Cross-sectional ranking is required for factor evaluation
* Survivorship bias can materially affect results
* Individual factors should be validated before combining into a multi-factor model

---

## Project Status

### Completed

* Universe construction (S&P 500)
* Price data pipeline
* Monthly return panel
* Momentum factor (12-1)
* Cross-sectional backtest
* Performance evaluation

### In Progress

* Additional factors (value, volatility)
* Multi-factor combination
* Portfolio construction enhancements

### Planned

* Transaction cost modeling
* Turnover constraints
* Expanded universe (e.g., Russell 1000/3000)
* Additional risk-adjusted metrics (drawdown, information coefficient)

---

## How to Run

1. Generate ticker universe:

```bash
python src/get_sp500_tickers.py
```

2. Pull and process price data:

```bash
python src/get_price_data.py
```

3. Build momentum factor:

```bash
python src/build_momentum_factor.py
```

4. Run backtest:

```bash
python src/backtest_momentum.py
```

---

## Summary

This project currently implements a complete single-factor workflow:

* Universe selection
* Data ingestion and transformation
* Factor construction
* Cross-sectional backtesting

It provides a foundation for developing a full multi-factor equity model.
