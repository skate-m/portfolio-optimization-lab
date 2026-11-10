# Research notebooks

This directory contains the eight research notebooks that make up the Portfolio Optimization Lab. They are ordered as a learning and analysis sequence: portfolio construction, estimation risk, stochastic modelling, portfolio insurance, liability valuation and diversification.

## Notebook map

| Notebook | Research question | Main methods |
|---|---|---|
| [01 — Efficient frontier](01_efficient_frontier.ipynb) | What risk–return combinations are feasible under long-only constraints? | Two-asset opportunity set, N-asset efficient frontier, GMV, equal weight and CML |
| [02 — Global minimum variance](02_global_minimum_variance.ipynb) | How does avoiding expected-return inputs affect portfolio construction? | GMV optimisation and expected-return sensitivity |
| [03 — Maximum Sharpe ratio](03_maximum_sharpe_ratio.ipynb) | Which long-only allocation maximises estimated excess return per unit of volatility? | Tangency portfolio, Sharpe ratio, CML and sensitivity analysis |
| [04 — Random walks and GBM](04_random_walk_gbm.ipynb) | How do drift and volatility shape stochastic price paths? | Geometric Brownian motion, simulated returns and reproducibility |
| [05 — CPPI and drawdown constraints](05_cppi_drawdown_constraints.ipynb) | How does CPPI adjust risky exposure as wealth moves relative to a floor? | Static-floor CPPI, buy-and-hold comparison and ratcheting drawdown floor |
| [06 — Monte Carlo CPPI](06_cppi_monte_carlo.ipynb) | How does CPPI behave across a distribution of simulated scenarios? | Monte Carlo paths, terminal wealth, floor breaches and parameter experiments |
| [07 — Liabilities and funding ratio](07_liabilities_funding_ratio.ipynb) | How do discount-rate assumptions affect liability value and asset coverage? | Discount factors, present value and funding-ratio sensitivity |
| [08 — Limits of diversification](08_limits_of_diversification.ipynb) | How does dependence between industries change over time? | Rolling pairwise correlation, trailing returns and optional market-cap weighting |

## Run order and environment

Run notebooks from the repository root so Python can import `risk_kit.py` and locate the data files.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
jupyter lab
```

Open a notebook and use **Kernel → Restart Kernel and Run All Cells**. This avoids hidden state from out-of-order cell execution.

## Conventions

- Returns are decimal simple returns: `0.01` means 1%.
- Risk-free rates, expected returns and volatility parameters are annualised unless a cell explicitly says otherwise.
- The core industry dataset contains monthly observations. Monthly covariance is annualised by multiplying by 12; volatility uses square-root-of-time scaling.
- Optimisation examples use long-only weights constrained to [0, 1] that sum to one.
- Random simulations use explicit seeds where reproducibility is important.
- Reusable calculations belong in `risk_kit.py`; notebooks should contain analysis, experiments, plots and interpretation rather than duplicate toolkit implementations.
- Code-cell outputs are cleared in the committed notebooks. Execute the notebooks locally to reproduce figures and results.

## Data dependencies

The core analyses use `data/ind30_m_vw_rets.csv`. Optional market-cap-weighted extensions also require `data/ind30_m_nfirms.csv` and `data/ind30_m_size.csv`; these companion files are not included in the repository snapshot. The notebooks skip those optional sections when the files are unavailable rather than fabricating data.

## Research integrity

Historical backtests and model simulations are conditional on their data and assumptions. They do not constitute forecasts or investment advice. The notebooks document important limitations, including estimation error, simplified return distributions, CPPI gap risk, omitted trading costs and the use of flat discount rates.
