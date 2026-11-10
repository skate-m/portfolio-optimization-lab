"""Shared risk, portfolio construction, simulation and liability analytics.

Return inputs are decimal returns (0.01 means 1%); annual rates are decimals.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import minimize
from scipy.stats import norm

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DATA_PATH = DATA_DIR / "ind30_m_vw_rets.csv"


def _read_industry_csv(path):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Required data file not found: {path}. See data/README.md.")
    frame = pd.read_csv(path, index_col=0)
    frame.columns = frame.columns.astype(str).str.strip()
    frame.index = pd.PeriodIndex(pd.to_datetime(frame.index.astype(str), format="%Y%m"), freq="M")
    return frame.apply(pd.to_numeric, errors="coerce")


def get_ind_returns(path=DATA_PATH):
    """Load monthly value-weighted industry returns as decimal returns."""
    return _read_industry_csv(path) / 100.0


def get_ind_nfirms(path=None):
    """Load monthly number of firms by industry from an optional companion file."""
    return _read_industry_csv(path or DATA_DIR / "ind30_m_nfirms.csv")


def get_ind_size(path=None):
    """Load monthly average industry firm size from an optional companion file."""
    return _read_industry_csv(path or DATA_DIR / "ind30_m_size.csv")


def get_total_market_index_returns(path=None):
    """Build a market-cap-weighted industry index from firm counts and average size."""
    if path is not None:
        return _read_industry_csv(path).iloc[:, 0] / 100.0
    returns, firms, size = get_ind_returns(), get_ind_nfirms(), get_ind_size()
    idx = returns.index.intersection(firms.index).intersection(size.index)
    cols = returns.columns.intersection(firms.columns).intersection(size.columns)
    cap = firms.loc[idx, cols] * size.loc[idx, cols]
    weights = cap.div(cap.sum(axis=1).replace(0, np.nan), axis=0)
    return (weights * returns.loc[idx, cols]).sum(axis=1).dropna()


def drawdown(returns, initial_wealth=1000):
    """Return wealth, running peaks and percentage drawdowns."""
    wealth = initial_wealth * (1 + returns).cumprod()
    peaks = wealth.cummax().clip(lower=initial_wealth)
    return pd.concat({"Wealth": wealth, "Peaks": peaks, "Drawdown": wealth / peaks - 1}, axis=1)


def skewness(returns):
    """Population skewness for a Series or DataFrame."""
    centered = returns - returns.mean()
    sigma = returns.std(ddof=0).replace(0, np.nan) if isinstance(returns, pd.DataFrame) else returns.std(ddof=0)
    return (centered ** 3).mean() / sigma ** 3


def kurtosis(returns):
    """Pearson (non-excess) population kurtosis."""
    centered = returns - returns.mean()
    sigma = returns.std(ddof=0).replace(0, np.nan) if isinstance(returns, pd.DataFrame) else returns.std(ddof=0)
    return (centered ** 4).mean() / sigma ** 4


def var_historic(returns, level=5):
    """Historical lower-tail value at risk, reported as a positive loss."""
    if not 0 < level < 100:
        raise ValueError("level must be between 0 and 100.")
    return -returns.quantile(level / 100)


def var_gaussian(returns, level=5, modified=False):
    """Gaussian lower-tail VaR with optional Cornish-Fisher adjustment."""
    if not 0 < level < 100:
        raise ValueError("level must be between 0 and 100.")
    z = norm.ppf(level / 100)
    if modified:
        s, k = skewness(returns), kurtosis(returns)
        z = z + (z**2 - 1)*s/6 + (z**3 - 3*z)*(k - 3)/24 - (2*z**3 - 5*z)*(s**2)/36
    return -(returns.mean() + z * returns.std(ddof=0))


def annualize_rets(returns, periods_per_year):
    """Geometrically annualise periodic returns (Series or DataFrame)."""
    if periods_per_year <= 0 or len(returns) == 0:
        raise ValueError("Provide observations and a positive annual frequency.")
    return (1 + returns).prod() ** (periods_per_year / len(returns)) - 1


def annualize_vol(returns, periods_per_year):
    """Annualise sample volatility with square-root-of-time scaling."""
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive.")
    return returns.std(ddof=1) * np.sqrt(periods_per_year)


def sharpe_ratio(returns, riskfree_rate, periods_per_year):
    """Annualised Sharpe ratio from periodic returns and an annual risk-free rate."""
    rf_period = (1 + riskfree_rate) ** (1 / periods_per_year) - 1
    return annualize_rets(returns - rf_period, periods_per_year) / annualize_vol(returns, periods_per_year)


def summary_stats(returns, riskfree_rate=0.03, periods_per_year=12):
    """Annual return, volatility, Sharpe, shape statistics, VaR and maximum drawdown."""
    if isinstance(returns, pd.Series):
        returns = returns.to_frame()
    stats = pd.DataFrame(index=returns.columns)
    stats["Annualized Return"] = annualize_rets(returns, periods_per_year)
    stats["Annualized Volatility"] = annualize_vol(returns, periods_per_year)
    stats["Sharpe Ratio"] = sharpe_ratio(returns, riskfree_rate, periods_per_year)
    stats["Skewness"] = skewness(returns)
    stats["Kurtosis"] = kurtosis(returns)
    stats["Historical VaR (5%)"] = var_historic(returns)
    stats["Gaussian VaR (5%)"] = var_gaussian(returns)
    compounded = (1 + returns).cumprod()
    # Include initial wealth (1.0) as the first running peak. Without this,
    # a loss in the first observation is incorrectly reported as zero drawdown.
    running_peaks = compounded.cummax().clip(lower=1.0)
    stats["Max Drawdown"] = (compounded / running_peaks - 1).min()
    return stats


def portfolio_return(weights, returns):
    """Expected portfolio return for weights and asset expected returns."""
    return float(np.asarray(weights, dtype=float) @ np.asarray(returns, dtype=float))


def portfolio_vol(weights, covmat):
    """Portfolio volatility from weights and a covariance matrix."""
    w = np.asarray(weights, dtype=float)
    return float(np.sqrt(max(w @ np.asarray(covmat, dtype=float) @ w, 0.0)))


def _validate_inputs(er, cov):
    er, cov = np.asarray(er, dtype=float).reshape(-1), np.asarray(cov, dtype=float)
    if er.size == 0 or cov.shape != (er.size, er.size):
        raise ValueError("Expected-return and covariance dimensions do not match or are empty.")
    if not np.isfinite(er).all() or not np.isfinite(cov).all():
        raise ValueError("Expected returns and covariance must be finite.")
    if not np.allclose(cov, cov.T, atol=1e-10):
        raise ValueError("Covariance matrix must be symmetric.")
    return er, cov


def minimize_vol(target_return, er, cov):
    """Find long-only weights with minimum volatility at a target return."""
    er, cov = _validate_inputs(er, cov)
    n = er.size
    if not er.min() - 1e-9 <= target_return <= er.max() + 1e-9:
        raise ValueError("Target return is outside the feasible long-only range.")
    constraints = (
        {"type": "eq", "fun": lambda w: np.sum(w) - 1},
        {"type": "eq", "fun": lambda w: portfolio_return(w, er) - target_return},
    )
    result = minimize(portfolio_vol, np.repeat(1/n, n), args=(cov,), method="SLSQP",
                      bounds=((0, 1),) * n, constraints=constraints,
                      options={"ftol": 1e-12, "maxiter": 1500})
    if not result.success:
        raise RuntimeError(f"Minimum-volatility optimisation failed: {result.message}")
    return result.x


def optimal_weights(n_points, er, cov):
    """Compute minimum-volatility weights over evenly spaced feasible returns."""
    er, cov = _validate_inputs(er, cov)
    if n_points < 2:
        raise ValueError("n_points must be at least 2.")
    minimum_variance_weights = gmv(cov)
    minimum_variance_return = portfolio_return(minimum_variance_weights, er)
    targets = np.linspace(minimum_variance_return, er.max(), n_points)
    return [minimize_vol(target, er, cov) for target in targets]


def msr(riskfree_rate, er, cov):
    """Find fully invested long-only weights maximising the Sharpe ratio."""
    er, cov = _validate_inputs(er, cov)
    n = er.size

    def negative_sharpe(w):
        vol = portfolio_vol(w, cov)
        return 1e12 if vol <= 1e-14 else -(portfolio_return(w, er) - riskfree_rate) / vol

    result = minimize(negative_sharpe, np.repeat(1/n, n), method="SLSQP",
                      bounds=((0, 1),) * n,
                      constraints=({"type": "eq", "fun": lambda w: np.sum(w) - 1},),
                      options={"ftol": 1e-12, "maxiter": 1500})
    if not result.success:
        raise RuntimeError(f"Maximum-Sharpe optimisation failed: {result.message}")
    return result.x


def gmv(cov):
    """Find the fully invested long-only global minimum-variance allocation."""
    cov = np.asarray(cov, dtype=float)
    if cov.ndim != 2 or cov.shape[0] != cov.shape[1] or cov.shape[0] == 0:
        raise ValueError("cov must be a non-empty square covariance matrix.")
    if not np.isfinite(cov).all() or not np.allclose(cov, cov.T, atol=1e-10):
        raise ValueError("cov must be finite and symmetric.")
    n = cov.shape[0]
    result = minimize(portfolio_vol, np.repeat(1/n, n), args=(cov,), method="SLSQP",
                      bounds=((0, 1),) * n,
                      constraints=({"type": "eq", "fun": lambda w: np.sum(w) - 1},),
                      options={"ftol": 1e-12, "maxiter": 1500})
    if not result.success:
        raise RuntimeError(f"GMV optimisation failed: {result.message}")
    return result.x


def plot_ef2(n_points, er, cov, ax=None):
    """Plot the two-asset feasible set on a dense allocation grid."""
    er, cov = _validate_inputs(er, cov)
    if er.size != 2:
        raise ValueError("plot_ef2 requires exactly two assets.")
    n_points = max(int(n_points), 501)
    weights = [np.array([w, 1-w]) for w in np.linspace(0, 1, n_points)]
    returns = np.array([portfolio_return(w, er) for w in weights])
    vols = np.array([portfolio_vol(w, cov) for w in weights])
    if ax is None:
        _, ax = plt.subplots(figsize=(9, 5.5))
    ax.plot(vols, returns, linewidth=2, label="Feasible portfolios")
    ax.scatter(vols[[0, -1]], returns[[0, -1]], zorder=3, label="100% allocations")
    ax.set(title="Two-asset opportunity set", xlabel="Annualised volatility", ylabel="Annualised expected return")
    ax.grid(alpha=0.25)
    ax.legend()
    return ax


def plot_ef(n_points, er, cov, style="-", riskfree_rate=0, show_cml=False,
            show_ew=False, show_gmv=False, ax=None):
    """Plot an N-asset minimum-volatility frontier and optional reference portfolios."""
    er, cov = _validate_inputs(er, cov)
    weights = optimal_weights(n_points, er, cov)
    returns = np.array([portfolio_return(w, er) for w in weights])
    vols = np.array([portfolio_vol(w, cov) for w in weights])
    if ax is None:
        _, ax = plt.subplots(figsize=(9, 5.5))
    ax.plot(vols, returns, style, linewidth=2, label="Efficient frontier")
    if show_ew:
        w = np.repeat(1/er.size, er.size)
        ax.scatter(portfolio_vol(w, cov), portfolio_return(w, er), label="Equal weight")
    if show_gmv:
        w = gmv(cov)
        ax.scatter(portfolio_vol(w, cov), portfolio_return(w, er), label="GMV", marker="D")
    if show_cml:
        w = msr(riskfree_rate, er, cov)
        r, v = portfolio_return(w, er), portfolio_vol(w, cov)
        ax.plot([0, v], [riskfree_rate, r], "--", label="Capital market line")
        ax.scatter(v, r, marker="*", s=130, label="Maximum Sharpe")
    ax.set(title="N-asset efficient frontier", xlabel="Annualised volatility", ylabel="Annualised expected return")
    ax.grid(alpha=0.25)
    ax.legend()
    return ax


def gbm(n_years=10, n_scenarios=1000, mu=0.07, sigma=0.15,
        steps_per_year=12, s_0=100, prices=True, seed=None):
    """Simulate geometric Brownian motion; prices include the initial level."""
    if (n_years <= 0 or n_scenarios <= 0 or steps_per_year <= 0
            or sigma < 0 or s_0 <= 0
            or not np.isfinite([n_years, n_scenarios, mu, sigma, steps_per_year, s_0]).all()):
        raise ValueError("Simulation inputs must be finite; dimensions and starting price positive; sigma non-negative.")
    n_steps, dt = int(n_years * steps_per_year), 1 / steps_per_year
    if n_steps < 1:
        raise ValueError("n_years * steps_per_year must produce at least one time step.")
    rng = np.random.default_rng(seed)
    z = rng.standard_normal((n_steps, n_scenarios))
    rets = np.exp((mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * z) - 1
    returns = pd.DataFrame(rets, columns=[f"Scenario {i+1}" for i in range(n_scenarios)])
    if not prices:
        return returns
    wealth = (1 + returns).cumprod() * s_0
    initial = pd.DataFrame([[s_0] * n_scenarios], columns=returns.columns)
    return pd.concat([initial, wealth], ignore_index=True)


def run_cppi(risky_r, safe_r=None, riskfree_rate=0.03, m=3, start=100,
             floor=0.8, drawdown=None, steps_per_year=12):
    """Backtest CPPI with a static floor and optional peak-ratcheting drawdown floor."""
    if isinstance(risky_r, pd.Series):
        risky_r = risky_r.to_frame()
    risky_r = risky_r.astype(float).fillna(0.0)
    if risky_r.empty or start <= 0 or m < 0 or not 0 <= floor <= 1:
        raise ValueError("Provide non-empty returns, positive start, m >= 0 and floor in [0, 1].")
    if not np.isfinite(risky_r.to_numpy()).all() or (risky_r <= -1).any().any():
        raise ValueError("Risky simple returns must be finite and greater than -100%.")
    if steps_per_year <= 0:
        raise ValueError("steps_per_year must be positive.")
    if drawdown is not None and not 0 <= drawdown < 1:
        raise ValueError("drawdown must be in [0, 1).")
    if safe_r is None:
        rp = (1 + riskfree_rate) ** (1 / steps_per_year) - 1
        safe_r = pd.DataFrame(rp, index=risky_r.index, columns=risky_r.columns)
    elif np.isscalar(safe_r):
        safe_r = pd.DataFrame(float(safe_r), index=risky_r.index, columns=risky_r.columns)
    elif isinstance(safe_r, pd.Series):
        safe_r = pd.DataFrame({c: safe_r for c in risky_r.columns}, index=risky_r.index)
    else:
        safe_r = safe_r.reindex_like(risky_r).fillna(0.0)
    if not np.isfinite(safe_r.to_numpy()).all() or (safe_r <= -1).any().any():
        raise ValueError("Safe simple returns must be finite and greater than -100%.")
    account, peak = np.repeat(float(start), risky_r.shape[1]), np.repeat(float(start), risky_r.shape[1])
    base_floor = account * floor
    wealth_rows, weights_rows, cushion_rows, floors_rows = [], [], [], []
    risky_wealth = start * (1 + risky_r).cumprod()
    for i in range(len(risky_r)):
        if drawdown is None:
            floor_value = base_floor
        else:
            floor_value = np.maximum(base_floor, peak * (1 - drawdown))
        cushion = np.maximum((account - floor_value) / np.maximum(account, 1e-12), 0)
        risky_weight = np.clip(m * cushion, 0, 1)
        account = account * (
            risky_weight * (1 + risky_r.iloc[i].to_numpy()) +
            (1 - risky_weight) * (1 + safe_r.iloc[i].to_numpy())
        )
        peak = np.maximum(peak, account)
        wealth_rows.append(account.copy())
        weights_rows.append(risky_weight.copy())
        cushion_rows.append(cushion.copy())
        floors_rows.append(floor_value.copy())
    cols, idx = risky_r.columns, risky_r.index
    return {
        "Wealth": pd.DataFrame(wealth_rows, index=idx, columns=cols),
        "Risky Wealth": risky_wealth,
        "Risky Allocation": pd.DataFrame(weights_rows, index=idx, columns=cols),
        "Cushion": pd.DataFrame(cushion_rows, index=idx, columns=cols),
        "Floor": pd.DataFrame(floors_rows, index=idx, columns=cols),
    }


def discount(t, r):
    """Price a unit zero-coupon payment due at time t under a flat annual rate."""
    if np.any(np.asarray(r) <= -1):
        raise ValueError("Discount rate must be greater than -100%.")
    return (1 + r) ** (-np.asarray(t))


def pv(liabilities, r):
    """Present value of a time-indexed Series of future liabilities."""
    if not isinstance(liabilities, pd.Series):
        raise TypeError("liabilities must be a pandas Series indexed by payment time.")
    return float((discount(liabilities.index.to_numpy(dtype=float), r) * liabilities.to_numpy()).sum())


def funding_ratio(assets, liabilities, r):
    """Assets divided by the present value of liabilities."""
    liability_value = pv(liabilities, r)
    if liability_value <= 0:
        raise ValueError("Present value of liabilities must be positive.")
    return assets / liability_value
