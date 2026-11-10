# Output figures

This directory contains selected, genuine chart outputs captured from executed research notebooks. The images are cropped from the submitted notebook screenshots to remove the notebook interface; the plotted data and visualisations are unchanged.

## Portfolio construction and stochastic simulation

| Figure | Source notebook | Description |
|---|---|---|
| `two_asset_frontier.svg` | `01_efficient_frontier.ipynb` | Two-asset feasible risk–return set. |
| `n_asset_frontier.svg` | `01_efficient_frontier.ipynb` | Long-only N-asset efficient frontier. |
| `gmv_and_cml.svg` | `01_efficient_frontier.ipynb` | Efficient frontier with GMV and capital-market-line references. |
| `03_maximum_sharpe_frontier.png` | `03_maximum_sharpe_ratio.ipynb` | Efficient frontier and maximum-Sharpe portfolio with the CML. |
| `04_gbm_simulated_paths.png` | `04_random_walk_gbm.ipynb` | 1,000 simulated geometric Brownian motion price paths. |

## CPPI and portfolio insurance

| Figure | Source notebook | Description |
|---|---|---|
| `05_cppi_wealth_comparison.png` | `05_cppi_drawdown_constraints.ipynb` | Historical wealth paths: buy-and-hold risky wealth versus CPPI wealth for Steel, Finance and Beer. |
| `05_cppi_risky_allocation.png` | `05_cppi_drawdown_constraints.ipynb` | Historical CPPI risky-asset allocation weights. |
| `05_cppi_crash_comparison.png` | `05_cppi_drawdown_constraints.ipynb` | CPPI and risky-asset wealth paths through the 2007–08 market crash. |
| `06_cppi_monte_carlo_paths.png` | `06_cppi_monte_carlo.ipynb` | Simulated CPPI wealth paths with floor reference. |
| `06_cppi_terminal_wealth_distribution.png` | `06_cppi_monte_carlo.ipynb` | Monte Carlo wealth paths and terminal-wealth frequency distribution, including mean and median. |

## Diversification and market behaviour

| Figure | Source notebook | Description |
|---|---|---|
| `08_market_cap_weighted_index.png` | `08_limits_of_diversification.ipynb` | Historical total-market cap-weighted wealth index. |
| `08_rolling_correlation.png` | `08_limits_of_diversification.ipynb` | Rolling 36-month correlation over the full sample. |
| `08_returns_vs_correlation_2007_2018.png` | `08_limits_of_diversification.ipynb` | Trailing 36-month returns and correlation since 2007. |

Only selected plots are included; redundant intermediate charts and raw-return plots were intentionally left out. The funding-ratio notebook did not produce a chart in the run supplied for this update.

These are historical or simulated illustrations, not forecasts. CPPI floors are not guaranteed in real markets, and simulated GBM paths rely on simplified model assumptions.
