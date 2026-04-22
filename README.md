# Multi-Factor Equity Model (In Progress)

## Overview

This project builds a systematic equity factor model from first principles, following a full quantitative workflow from universe construction through factor design, combination, and backtesting.

The current state of the project includes:

* A reproducible data pipeline
* A monthly return panel
* Two core factors: momentum and low volatility
* Multiple factor combination approaches explored and evaluated

This repository documents both working and non-working approaches to factor construction and combination.

---

## Project Structure

```text
multi-factor-equity-model/
├── data/                           # Generated data (not tracked)
├── src/
│   ├── get_sp500_tickers.py
│   ├── get_price_data.py
│   ├── build_momentum_factor.py
│   ├── backtest_momentum.py
│   ├── build_volatility_factor.py
│   ├── backtest_volatility.py
│   ├── combine_factors_filtered.py
│   ├── backtest_combined_filtered.py
│   └── Deprecated/
│       ├── combine_factors_weighted_deprecated.py
│       └── backtest_combined_weighted_deprecated.py
├── README.md
├── LICENSE
└── .gitignore
```

---

## Methodology

### 1. Universe Construction

* Universe: S&P 500 constituents (current snapshot)
* Tickers scraped and cleaned for compatibility (e.g., BRK.B → BRK-B)

**Limitation:**
This introduces survivorship bias since historical index membership is not point-in-time.

---

### 2. Data Pipeline

* Daily price data sourced via `yfinance`
* Converted to month-end frequency
* Returns computed as:

```text
ret_1m       = backward-looking monthly return  
ret_fwd_1m   = forward-looking monthly return
```

Forward returns are used as the target to avoid look-ahead bias.

---

## Factor Construction

### Momentum Factor

* Definition: 12-1 momentum (cumulative return from t-12 to t-1)
* Most recent month excluded to avoid short-term reversal
* Ranked cross-sectionally each month

Backtest:

* Decile portfolios constructed
* Positive spread observed between top and bottom deciles

---

### Low Volatility Factor

* Definition: 12-month rolling standard deviation of returns
* Lower volatility preferred
* Ranked cross-sectionally each month

Backtest:

* Captures a risk-based signal
* Performance is weaker than momentum when used independently

---

## Factor Combination Experiments

### 1. Linear Combination (Deprecated)

* Combined momentum and volatility using weighted averages
* Signals normalized via percentile ranks

**Observed outcome:**

* Negative long-short performance
* Loss of monotonic decile structure

**Interpretation:**

* Momentum and volatility signals conflicted
* High-momentum stocks were penalized due to higher volatility
* Linear combination diluted predictive power

This approach is retained in `/src/Deprecated` for reference.

---

### 2. Filter-Based Combination

A sequential approach was tested:

1. Select top momentum stocks (top 30%)
2. Within this subset, rank by volatility (favoring lower volatility)

This approach preserves the primary momentum signal while applying volatility as a secondary filter.

**Observed outcome:**

* Improved separation between higher and lower ranked stocks
* Stronger long-short spread compared to linear combination
* Sensitivity to ranking direction and implementation details

---

## Key Learnings

* Factor compatibility is critical when combining signals
* Linear averaging can degrade performance when factors are negatively correlated
* Sequential filtering can preserve primary signals more effectively
* Ranking direction (signal sign) has a material impact on results
* Backtesting must evaluate both decile structure and long-short performance

---

## Project Status

### Completed

* Universe construction (S&P 500)
* Price data pipeline
* Monthly return panel
* Momentum factor (12-1)
* Low volatility factor
* Individual factor backtests
* Linear factor combination (tested and deprecated)
* Filter-based factor combination (initial implementation)
* Combined model backtesting

### In Progress

* Validation and robustness checks of combined approach
* Review of decile stability and concentration effects
* Visualization of cumulative returns

### Planned

* Additional factors (value, quality)
* Alternative combination methods
* Transaction cost modeling
* Expanded universe (e.g., Russell 1000/3000)
* Additional risk metrics (drawdown, information coefficient)

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

3. Build factors:

```bash
python src/build_momentum_factor.py
python src/build_volatility_factor.py
```

4. Run individual backtests:

```bash
python src/backtest_momentum.py
python src/backtest_volatility.py
```

5. Test factor combinations:

```bash
python src/combine_factors_filtered.py
python src/backtest_combined_filtered.py
```

---

## Summary

This project currently implements a full factor research workflow, including:

* Data ingestion and preprocessing
* Factor construction
* Cross-sectional ranking
* Portfolio backtesting
* Iterative factor combination testing

The focus is on understanding how different signals interact and how implementation choices affect performance, rather than presenting a finalized model.
