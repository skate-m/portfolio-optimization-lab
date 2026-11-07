"""Reusable functions used by this repository's portfolio analysis notebooks."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import minimize
from scipy.stats import norm

DATA_PATH = Path(__file__).resolve().parent / "data" / "ind30_m_vw_rets.csv"


def get_ind_returns(path=DATA_PATH):
    """Load monthly value-weighted industry returns as decimal returns."""
    data = pd.read_csv(path, index_col=0)
    data.index = pd.PeriodIndex(pd.to_datetime(data.index.astype(str), format="%Y%m"), freq="M")
    data.columns = data.columns.str.strip()
    return data.apply(pd.to_numeric, errors="coerce") / 100.0


def drawdown(returns):
    """Return wealth, running peaks and percentage drawdowns."""
    wealth = 1000 * (1 + returns).cumprod()
    peaks = wealth.cummax().clip(lower=1000)
    return pd.DataFrame({"Wealth": wealth, "Peaks": peaks, "Drawdown": wealth / peaks - 1})


def skewness(returns):
    """Population skewness for a return Series or DataFrame."""
    centered = returns - returns.mean()
    sigma = returns.std(ddof=0).replace(0, np.nan) if isinstance(returns, pd.DataFrame) else returns.std(ddof=0)
    return (centered ** 3).mean() / sigma ** 3


def kurtosis(returns):
    """Pearson population kurtosis for a return Series or DataFrame."""
    centered = returns - returns.mean()
    sigma = returns.std(ddof=0).replace(0, np.nan) if isinstance(returns, pd.DataFrame) else returns.std(ddof=0)
    return (centered ** 4).mean() / sigma ** 4


def var_gaussian(returns, level=5, modified=False):
    """Estimate lower-tail Gaussian VaR; optionally apply Cornish–Fisher adjustment."""
    if not 0 < level < 100:
        raise ValueError("level must be between 0 and 100.")
    z = norm.ppf(level / 100)
    if modified:
        s, k = skewness(returns), kurtosis(returns)
        z = z + (z**2 - 1)*s/6 + (z**3 - 3*z)*(k - 3)/24 - (2*z**3 - 5*z)*(s**2)/36
    return -(returns.mean() + z * returns.std(ddof=0))


def annualize_rets(returns, periods_per_year):
    """Geometrically annualise periodic returns."""
    if periods_per_year <= 0 or returns.empty:
        raise ValueError("Provide observations and a positive annual frequency.")
    return (1 + returns).prod() ** (periods_per_year / returns.shape[0]) - 1


def annualize_vol(returns, periods_per_year):
    """Annualise sample volatility using square-root-of-time scaling."""
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive.")
    return returns.std(ddof=1) * np.sqrt(periods_per_year)


def sharpe_ratio(returns, riskfree_rate, periods_per_year):
    """Annualised Sharpe ratio from periodic returns and an annual risk-free rate."""
    rf_period = (1 + riskfree_rate) ** (1 / periods_per_year) - 1
    return annualize_rets(returns - rf_period, periods_per_year) / annualize_vol(returns, periods_per_year)


def portfolio_return(weights, returns):
    """Calculate the weighted expected portfolio return."""
    return float(np.asarray(weights) @ np.asarray(returns))


def portfolio_vol(weights, covmat):
    """Calculate portfolio volatility from weights and covariance."""
    w = np.asarray(weights, dtype=float)
    return float(np.sqrt(max(w @ np.asarray(covmat, dtype=float) @ w, 0)))


def plot_ef2(n_points, er, cov, ax=None):
    """Plot the feasible long-only opportunity set for exactly two assets."""
    er = np.asarray(er, dtype=float)
    cov = np.asarray(cov, dtype=float)
    if er.size != 2 or cov.shape != (2, 2):
        raise ValueError("plot_ef2 requires exactly two assets.")
    weights = [np.array([w, 1-w]) for w in np.linspace(0, 1, n_points)]
    returns = [portfolio_return(w, er) for w in weights]
    volatilities = [portfolio_vol(w, cov) for w in weights]
    if ax is None:
        _, ax = plt.subplots(figsize=(9, 5.5))
    ax.plot(volatilities, returns, ".-", label="Feasible portfolios")
    ax.set(title="Two-asset opportunity set", xlabel="Annualised volatility", ylabel="Annualised expected return")
    ax.grid(alpha=.25)
    ax.legend()
    return ax


def minimize_vol(target_return, er, cov):
    """Find long-only weights with minimum volatility at a target return."""
    er, cov = np.asarray(er, dtype=float), np.asarray(cov, dtype=float)
    n = er.size
    if cov.shape != (n, n):
        raise ValueError("Expected-return and covariance dimensions do not match.")
    if target_return < er.min()-1e-9 or target_return > er.max()+1e-9:
        raise ValueError("Target return is outside the feasible long-only range.")
    constraints = (
        {"type": "eq", "fun": lambda w: np.sum(w)-1},
        {"type": "eq", "fun": lambda w: portfolio_return(w, er)-target_return},
    )
    result = minimize(portfolio_vol, np.repeat(1/n, n), args=(cov,), method="SLSQP",
                      bounds=((0, 1),)*n, constraints=constraints,
                      options={"ftol": 1e-12, "maxiter": 1000})
    if not result.success:
        raise RuntimeError(result.message)
    return result.x


def optimal_weights(n_points, er, cov):
    """Find minimum-volatility weights for evenly spaced target returns."""
    targets = np.linspace(np.min(er), np.max(er), n_points)
    return [minimize_vol(target, er, cov) for target in targets]


def msr(riskfree_rate, er, cov):
    """Find fully invested long-only weights maximising the Sharpe ratio."""
    er, cov = np.asarray(er, dtype=float), np.asarray(cov, dtype=float)
    def negative_sharpe(w):
        vol = portfolio_vol(w, cov)
        return np.inf if vol <= 0 else -(portfolio_return(w, er)-riskfree_rate)/vol
    result = minimize(negative_sharpe, np.repeat(1/er.size, er.size), method="SLSQP",
                      bounds=((0, 1),)*er.size,
                      constraints=({"type": "eq", "fun": lambda w: np.sum(w)-1},),
                      options={"ftol": 1e-12, "maxiter": 1000})
    if not result.success:
        raise RuntimeError(result.message)
    return result.x


def gmv(cov):
    """Find the long-only global minimum-variance allocation."""
    cov = np.asarray(cov, dtype=float)
    n = cov.shape[0]
    result = minimize(portfolio_vol, np.repeat(1/n, n), args=(cov,), method="SLSQP",
                      bounds=((0, 1),)*n,
                      constraints=({"type": "eq", "fun": lambda w: np.sum(w)-1},),
                      options={"ftol": 1e-12, "maxiter": 1000})
    if not result.success:
        raise RuntimeError(result.message)
    return result.x


def plot_ef(n_points, er, cov, style="-", riskfree_rate=0, show_cml=False, show_ew=False, show_gmv=False, ax=None):
    """Plot an N-asset long-only efficient frontier and optional reference portfolios."""
    er, cov = np.asarray(er, dtype=float), np.asarray(cov, dtype=float)
    weights = optimal_weights(n_points, er, cov)
    returns = [portfolio_return(w, er) for w in weights]
    volatilities = [portfolio_vol(w, cov) for w in weights]
    if ax is None:
        _, ax = plt.subplots(figsize=(9, 5.5))
    ax.plot(volatilities, returns, style, label="Efficient frontier")
    if show_ew:
        w = np.repeat(1/er.size, er.size)
        ax.scatter(portfolio_vol(w, cov), portfolio_return(w, er), label="Equal weight", marker="o")
    if show_gmv:
        w = gmv(cov)
        ax.scatter(portfolio_vol(w, cov), portfolio_return(w, er), label="GMV", marker="D")
    if show_cml:
        w = msr(riskfree_rate, er, cov)
        r, v = portfolio_return(w, er), portfolio_vol(w, cov)
        ax.plot([0, v], [riskfree_rate, r], "--", label="Capital market line")
        ax.scatter(v, r, marker="*", s=120, label="Maximum Sharpe")
    ax.set(title="N-asset efficient frontier", xlabel="Annualised volatility", ylabel="Annualised expected return")
    ax.grid(alpha=.25)
    ax.legend()
    return ax
