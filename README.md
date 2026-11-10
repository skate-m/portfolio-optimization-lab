# Portfolio Optimization Lab

A reproducible Python research project covering portfolio construction, risk measurement, stochastic simulation, CPPI portfolio insurance, liability valuation and the limits of diversification. The project uses the Ken French 30-industry monthly value-weighted return dataset bundled in this repository.

## Research notebooks

Run the notebooks in numerical order. Each notebook imports the shared implementation through `import risk_kit as rk`; reusable calculations are not duplicated across notebooks.

| Notebook | Topic |
|---|---|
| [01 — Efficient frontier](notebooks/01_efficient_frontier.ipynb) | Two-asset feasible set, N-asset frontier, GMV, equal-weight and CML comparisons |
| [02 — Global minimum variance](notebooks/02_global_minimum_variance.ipynb) | GMV construction and estimation risk |
| [03 — Maximum Sharpe ratio](notebooks/03_maximum_sharpe_ratio.ipynb) | Tangency portfolio, CML and expected-return sensitivity |
| [04 — Random walks and GBM](notebooks/04_random_walk_gbm.ipynb) | Geometric Brownian motion and stochastic price paths |
| [05 — CPPI and drawdown constraints](notebooks/05_cppi_drawdown_constraints.ipynb) | Static-floor CPPI, ratcheting drawdown floors and historical comparisons |
| [06 — Monte Carlo CPPI](notebooks/06_cppi_monte_carlo.ipynb) | Scenario simulation, terminal wealth and floor-breach statistics |
| [07 — Liabilities and funding ratio](notebooks/07_liabilities_funding_ratio.ipynb) | Discount factors, present value and funding-ratio sensitivity |
| [08 — Limits of diversification](notebooks/08_limits_of_diversification.ipynb) | Rolling correlations and diversification through market stress |

## Results

Standalone SVG previews are stored in [outputs/](outputs/) and linked from the corresponding notebooks. The efficient-frontier figures are based on the bundled historical dataset and the documented estimation window. Additional GBM, CPPI, Monte Carlo and diversification previews are explicitly marked illustrative; rerun the relevant notebook cells to generate exact data-driven plots. The funding-ratio sensitivity figure is calculated from the liability cash flows and assumptions defined in notebook 07.

| Research area | Output figures |
|---|---|
| Efficient frontier | [Two-asset frontier](outputs/two_asset_frontier.svg), [N-asset frontier](outputs/n_asset_frontier.svg), [GMV and CML](outputs/gmv_and_cml.svg) |
| Maximum Sharpe | [Allocation sensitivity](outputs/03_maximum_sharpe_weights.svg) |
| Geometric Brownian motion | [Price paths](outputs/04_gbm_price_paths.svg), [Volatility comparison](outputs/04_gbm_volatility_comparison.svg) |
| CPPI and drawdown | [Wealth comparison](outputs/05_cppi_wealth_comparison.svg), [Drawdown floor](outputs/05_cppi_drawdown_floor.svg) |
| Monte Carlo CPPI | [Wealth paths](outputs/06_cppi_monte_carlo_paths.svg), [Terminal wealth](outputs/06_cppi_terminal_wealth.svg), [Volatility sensitivity](outputs/06_cppi_volatility_sensitivity.svg) |
| Liability valuation | [Funding-ratio sensitivity](outputs/07_funding_ratio_sensitivity.svg) |
| Diversification | [Rolling correlation](outputs/08_rolling_correlation.svg) |

## Repository structure

```text
portfolio-optimization-lab/
├── data/
│   ├── ind30_m_vw_rets.csv
│   └── README.md
├── notebooks/
│   ├── 01_efficient_frontier.ipynb
│   ├── 02_global_minimum_variance.ipynb
│   ├── 03_maximum_sharpe_ratio.ipynb
│   ├── 04_random_walk_gbm.ipynb
│   ├── 05_cppi_drawdown_constraints.ipynb
│   ├── 06_cppi_monte_carlo.ipynb
│   ├── 07_liabilities_funding_ratio.ipynb
│   └── 08_limits_of_diversification.ipynb
├── outputs/
│   ├── two_asset_frontier.svg
│   ├── n_asset_frontier.svg
│   ├── gmv_and_cml.svg
│   └── README.md
├── tests/
│   └── test_risk_kit.py
├── .github/workflows/tests.yml
├── risk_kit.py
└── requirements.txt
```

## Setup

Python 3.10 or newer is recommended.

```bash
git clone https://github.com/skate-m/portfolio-optimization-lab.git
cd portfolio-optimization-lab
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
jupyter lab
```

Run JupyterLab from the repository root so that the notebooks can import `risk_kit.py` and locate the bundled dataset. On Windows, activate the environment with `.venv\\Scripts\\activate`.

Run the automated checks with:

```bash
pytest -q
```

## Shared toolkit

`risk_kit.py` is the common API for the notebooks. It includes industry-data loading, drawdowns, skewness/kurtosis, historical and Gaussian VaR, annualisation, Sharpe ratios, portfolio statistics, constrained optimisation (GMV/MSR/frontier), geometric Brownian motion, CPPI backtesting with optional drawdown ratchets, and liability discounting/funding ratios.

All return inputs are decimal returns: `0.01` represents 1%. Annual rates are expressed as decimals. The industry-return CSV stores percentage points and is converted by `get_ind_returns()`.

## Data provenance and optional extensions

The included `data/ind30_m_vw_rets.csv` snapshot contains 1,110 monthly observations across 30 industries from July 1926 through December 2018. It is a Ken French Data Library 30-industry value-weighted return series. See [data/README.md](data/README.md).

The market-cap-weighted extension in the diversification and CPPI notebooks additionally requires the companion firm-count and average-firm-size files. Those source files were not part of the supplied repository data and are intentionally not fabricated. The core notebooks run without them; the affected optional sections explain how to enable the extension.

## Methodology and limitations

- Historical estimation window in the efficient-frontier examples: January 1996–December 2000.
- Monthly returns are geometrically annualised; monthly covariance matrices are multiplied by 12.
- Portfolio optimisers use long-only weights in [0, 1] that sum to one.
- The illustrative 3% annual risk-free rate and flat discount rates are assumptions, not market quotes.
- CPPI is exposed to gap risk and discrete-rebalancing risk; a floor is not guaranteed in real markets.
- GBM assumes constant drift and volatility with lognormal returns; it omits jumps, volatility clustering and regime changes.
- Liability valuation uses a flat curve and simplified annual compounding.
- Backtests exclude transaction costs, taxes, market impact, liquidity constraints and out-of-sample execution.

This is an educational research project, not investment advice. Historical results and simulated scenarios do not predict future performance.
