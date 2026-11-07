# Portfolio Optimisation Lab

This project documents a progression through classical mean-variance portfolio optimisation using the Ken French 30 Industry Portfolios value-weighted monthly-return data.

The original notebook calculations are preserved. Additional comments explain the purpose of each step and the reasoning behind the modelling choices.

## What the project covers

1. **Two-asset efficient frontier** — cleans and explores industry returns, computes risk statistics, and traces the return/volatility trade-off for two selected industries.
2. **N-asset efficient frontier** — uses constrained numerical optimisation to find the lowest-volatility portfolio for each target return across several industries.
3. **Global minimum-variance portfolio** — demonstrates why maximum-Sharpe portfolios can be sensitive to small return-estimate changes, then compares the efficient frontier with equal-weight and GMV portfolios.

## Project layout

```text
portfolio-optimization-lab/
├── data/
│   └── ind30_m_vw_rets.csv             # Ken French 30 industry monthly returns
├── notebooks/
│   ├── 01_two_asset_efficient_frontier.ipynb
│   ├── 02_n_asset_efficient_frontier.ipynb
│   └── 03_global_minimum_variance.ipynb
├── risk_kit.py                         # Reusable return, risk, and optimiser helpers
├── requirements.txt
└── README.md
```

## Getting started

Create an environment, install the dependencies, and start Jupyter from the project root:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
jupyter notebook
```

Run the notebooks in numerical order. Starting Jupyter in the project root is important because the notebooks and `risk_kit.py` load the dataset from `data/` using relative paths.

## Method notes

- Returns are monthly decimal returns; annualisation uses 12 periods per year.
- Portfolio return is calculated as `w.T @ r`, and volatility as `sqrt(w.T @ Σ @ w)`.
- The N-asset optimisation is long-only: each asset weight is constrained to the interval [0, 1], and all weights sum to 1.
- The GMV notebook illustrates estimation risk: small changes in expected-return inputs can sharply change the maximum-Sharpe allocation.

## Data

`ind30_m_vw_rets.csv` is the Ken French 30 Industry Portfolios value-weighted monthly return dataset, included here only to make these notebooks reproducible. Please refer to the original data source for licensing and methodology.
