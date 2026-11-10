import numpy as np
import pandas as pd
import pytest

import risk_kit as rk


def test_included_industry_returns_load_as_decimal():
    returns = rk.get_ind_returns()
    assert returns.shape == (1110, 30)
    assert isinstance(returns.index, pd.PeriodIndex)
    assert returns.index[0] == pd.Period("1926-07", freq="M")
    assert returns.abs().max().max() < 2


def test_annualize_returns_monthly_series():
    monthly = pd.Series([0.01] * 12)
    assert rk.annualize_rets(monthly, 12) == pytest.approx((1.01 ** 12) - 1)


def test_portfolio_optimisation_constraints():
    er = np.array([0.08, 0.12, 0.10])
    cov = np.array([[0.04, 0.01, 0.00], [0.01, 0.09, 0.01], [0.00, 0.01, 0.05]])
    weights = rk.gmv(cov)
    assert weights.sum() == pytest.approx(1.0, abs=1e-6)
    assert np.all(weights >= -1e-8)
    assert np.all(weights <= 1 + 1e-8)
    target = rk.minimize_vol(0.10, er, cov)
    assert target.sum() == pytest.approx(1.0, abs=1e-6)
    assert rk.portfolio_return(target, er) == pytest.approx(0.10, abs=1e-6)


def test_drawdown_uses_initial_wealth_once():
    result = rk.drawdown(pd.Series([0.10, -0.20]))
    assert result["Wealth"].iloc[0] == pytest.approx(1100)
    assert result["Wealth"].iloc[1] == pytest.approx(880)
    assert result["Drawdown"].iloc[1] == pytest.approx(-0.20)


def test_summary_stats_includes_initial_wealth_in_drawdown():
    returns = pd.Series([-0.10, 0.05, -0.05], name="Strategy")
    stats = rk.summary_stats(returns, riskfree_rate=0.0, periods_per_year=12)
    expected_wealth = (1 - 0.10) * (1 + 0.05) * (1 - 0.05)
    expected_drawdown = min(0.90 / 1.0 - 1, expected_wealth / 1.0 - 1)
    assert stats.loc["Strategy", "Max Drawdown"] == pytest.approx(expected_drawdown)


def test_gbm_is_seed_reproducible_and_shapes_are_consistent():
    a = rk.gbm(1, 3, prices=False, seed=12)
    b = rk.gbm(1, 3, prices=False, seed=12)
    assert a.equals(b)
    assert a.shape == (12, 3)
    prices = rk.gbm(1, 3, seed=12)
    assert prices.shape == (13, 3)
    assert (prices.iloc[0] == 100).all()


def test_gbm_rejects_invalid_parameters():
    with pytest.raises(ValueError):
        rk.gbm(0.01, 10, steps_per_year=1)
    with pytest.raises(ValueError):
        rk.gbm(1, 10, sigma=np.nan)


def test_cppi_returns_aligned_outputs_and_bounded_weights():
    returns = pd.DataFrame({"A": [0.02, -0.03, 0.01], "B": [-0.01, 0.01, 0.02]})
    result = rk.run_cppi(returns, start=100, floor=0.8, drawdown=0.25)
    assert result["Wealth"].shape == returns.shape
    assert result["Risky Allocation"].shape == returns.shape
    assert result["Risky Allocation"].to_numpy().min() >= 0
    assert result["Risky Allocation"].to_numpy().max() <= 1


def test_cppi_rejects_returns_below_minus_one():
    returns = pd.Series([-1.01])
    with pytest.raises(ValueError):
        rk.run_cppi(returns)


def test_liability_discounting_and_funding_ratio():
    liabilities = pd.Series([100, 100], index=[1.0, 2.0])
    expected = 100 / 1.05 + 100 / (1.05 ** 2)
    assert rk.pv(liabilities, 0.05) == pytest.approx(expected)
    assert rk.funding_ratio(expected, liabilities, 0.05) == pytest.approx(1.0)
