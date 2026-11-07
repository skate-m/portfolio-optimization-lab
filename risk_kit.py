import pandas as pd 
import numpy as np
import scipy

def drawdown(return_series):
    wealth_index=1000*(1+return_series).cumprod()
    previous_peaks=wealth_index.cummax()
    drawdown=(wealth_index-previous_peaks)/previous_peaks
    return pd.DataFrame({
        'Wealth': wealth_index,
        'Peaks': previous_peaks,
        'Drawdown': drawdown
    })

def get_ffme_returns():
    me_m=pd.read_csv("data/Portfolios_Formed_on_ME_monthly_EW.csv",
                 header=0,
                 index_col=0,
                 na_values=-99.99
                )
    me_m.index=pd.to_datetime(me_m.index,format="%Y%m") 
    rets=me_m[['Lo 10','Hi 10']]
    rets.columns=['SmallCap','LargeCap']
    rets=rets/100
    return rets

def get_hfi_returns():
    """
    Load and format EDHEC headge fund index returns
    """
    hfi = pd.read_csv("data/edhec-hedgefundindices.csv",
                     header=0,
                     index_col=0,
                     )
    hfi.index=pd.to_datetime(hfi.index,dayfirst=True)
    hfi=hfi/100
    return hfi

def get_ind_returns():
    """
    Load and format the Ken French 30 Industry Portfolios Value Weighted Monthly Returns
    """
    ind = pd.read_csv("data/ind30_m_vw_rets.csv", header=0, index_col=0)/100
    ind.index = pd.to_datetime(ind.index, format="%Y%m").to_period('M')
    ind.columns = ind.columns.str.strip()
    return ind
    
def get_ind_size():
    """
    """
    ind=pd.read_csv("data/ind30_m_size.csv",header=0,index_col=0)
    ind.index=pd.to_datetime(ind.index,format="%Y%m").to_period("M")
    ind.columns=ind.columns.str.strip()
    return ind
    
def get_ind_nfirms():
    """
    Load and format the Ken French 30 Industry Portfolios Value Weighted monthly returns
    """
    ind=pd.read_csv("data/ind30_m_nfirms.csv",header=0,index_col=0)
    ind.index=pd.to_datetime(ind.index,format="%Y%m").to_period("M")
    ind.columns=ind.columns.str.strip()
    return ind

def get_total_market_index_returns():
    """
    Load the 30 industry portfolio data and derive the returns of a capweighted total market index
    """
    ind_nfirms = get_ind_nfirms()
    ind_size = get_ind_size()
    ind_return = get_ind_returns()
    ind_mktcap = ind_nfirms * ind_size
    total_mktcap = ind_mktcap.sum(axis=1)
    ind_capweight = ind_mktcap.divide(total_mktcap, axis="rows")
    total_market_return = (ind_capweight * ind_return).sum(axis="columns")
    return total_market_return
    
def semi_deviation(r):
    """
    Returns the semideviation aka negative semideviation of r 
    r must be series or DataFrame
    """
    is_negative=r<0
    return r[is_negative].std(ddof=0)
    
def skewness(r):
    """
    Alternative to scipy.stats.skew()
    Computes the skewness of given series or DataFrame
    Returns a float or Series
    """
    demeaned_r=r-r.mean()
    # using population std so set dof=0
    sigma_r=r.std(ddof=0)
    exp=(demeaned_r**3).mean()
    return exp/sigma_r**3 

def kurtosis(r):
    """
    Alternative to scipy.stats.kurtosis()
    Computes the kurtosis of given series or DataFrame
    Returns a float or Series
    """
    demeaned_r=r-r.mean()
    # using population std so set dof=0
    sigma_r=r.std(ddof=0)
    exp=(demeaned_r**4).mean()
    return exp/sigma_r**4 

def is_normal(r,level=0.01):
    """
    Applies jarque-bera test to determing if a Series is normal or nor 
    Test is applied at the 1% level by default
    Returns true if the hypothesis of normality is accepted, False otherwise 
    """
    statistics,p_value=scipy.stats.jarque_bera(r)
    return bool(p_value>level)

def var_historic(r,level=5):
    """
    Returns historic value at risk at specific level
    i.e. returns the number such that "level" percent of returns 
    fall below that number, and the (100-level) percent are above 
    """
    if isinstance(r,pd.DataFrame):
        return r.aggregate(var_historic,level=level)
    elif isinstance(r,pd.Series):
        return -np.percentile(r,level)
    else:
        raise TypeError("Expected r to be Series or DataFrame ")

from scipy.stats import norm
def var_gaussian(r,level=5,modified=False):
    """
    Returns the parametric Gaussian VaR of a Series or DataFrame 
    If modified is "True", then the modified VaR is returned,
    using Cornish-Fisher modification
    """
    # Compute the z-score assuming it was Gaussian 
    z = norm.ppf(level/100)
    if modified:
        # modify the z-score based on observed skewness and kurtosis 
        s=skewness(r)
        k=kurtosis(r)

        z=(z+
               (z**2-1)*s/6+
               (z**3-3*z)*(k-3)/24-
               (2*z**3-5*z)*(s**2)/36
          ) 
    return -(r.mean()+(z*r.std(ddof=0)))

def cvar_historic(r, level=5):
    """
    Computes the conditional var of Series of DataFrame
    """
    if isinstance(r,pd.Series):
        is_beyond = r <= -var_historic(r, level=level)
        return -r[is_beyond].mean()
    elif isinstance(r,pd.DataFrame):
        return r.aggregate(cvar_historic, level=level)
    else:
        raise TypeError("Expected r to be a Series or DataFrame")

def annualize_rets(r,periods_per_year):
    """
    annualizes set of returns 
    We should infer the periods per year 
    but that is left as an excercise for reader 
    """
    compounded_growth=(1+r).prod()
    n_periods=r.shape[0]
    return compounded_growth**(periods_per_year/n_periods)-1

def annualize_vol(r,periods_per_year):
    """
    annualizes the volatility of a set of returns 
    """
    return r.std()*(periods_per_year**0.5)

def sharpe_ratio(r,riskfree_rate,periods_per_year):
    """
    Computes annualized sharpe ratio of set of returns 
    """
    # convert annual risk free rate to period
    rf_per_period=(1+riskfree_rate)**(1/periods_per_year)-1
    excess_ret=r-rf_per_period
    ann_ex_ret=annualize_rets(excess_ret,periods_per_year)
    ann_vol=annualize_vol(r,periods_per_year)
    return ann_ex_ret/ann_vol

def portfolio_return(weights, returns):
    """
    Computes the return on a portfolio from constituent returns and weights
    weights are a numpy array or Nx1 matrix and returns are a numpy array or Nx1 matrix
    """
    return weights.T @ returns

def portfolio_vol(weights, covmat):
    """
    Computes the vol of a portfolio from a covariance matrix and constituent weights
    weights are a numpy array or N x 1 maxtrix and covmat is an N x N matrix
    """
    return (weights.T @ covmat @ weights)**0.5

def plot_ef2(n_points,er,cov):
    """
    Plots the 2 asset efficient frontier 
    """
    if er.shape[0] != 2 or er.shape[0] != 2:
        raise ValueError("plot_ef2 can only plot 2-asset frontiers")
    weights=[np.array([w,1-w])for w in np.linspace(0,1,n_points)]
    rets = [portfolio_return(w,er) for w in weights]
    vols = [portfolio_vol(w,cov) for w in weights]
    ef = pd.DataFrame({
        "Returns":rets,
        "Volatility":vols
    })
    ef.plot.line(x="Volatility",y="Returns",style=".-")

from scipy.optimize import minimize
def minimize_vol(target_return,er,cov):
    """
    target return --> weight
    """
    n=er.shape[0]
    init_guess=np.repeat(1/n,n)
    bounds=((0.0,1.0),)*n
    # Checking whether return is target or not 
    return_is_target={
        'type':'eq',
        'args':(er,),
        'fun': lambda weights,er: target_return - portfolio_return(weights,er) 
    }#To check if target is met (=0)
    weights_sum_to_1 = {
        'type':'eq',
        'fun': lambda weights: np.sum(weights)-1
    }
    results = minimize(
        portfolio_vol,
        init_guess,
        args=(cov,),
        method="SLSQP",#Quadratic programming optimizer
        constraints=(return_is_target,weights_sum_to_1),
        bounds=bounds
    )
    return results.x

def optimal_weights(n_points, er, cov):
    """
    List of weights to run the optimizer on to minimize vol
    """
    target_rets = np.linspace(er.min(),er.max())
    weights = [minimize_vol(target_return,er,cov) for target_return in target_rets]
    return weights

from scipy.optimize import minimize


def msr(riskfree_rate,er,cov):
    """
    Return the weights of the portfolio that gives you the maximum sharpe ratio given 
    the riskfree rate and expected returns and a covariance matrix
    """
    n=er.shape[0]
    init_guess=np.repeat(1/n,n)
    bounds=((0.0,1.0),)*n

    weights_sum_to_1 = {
        'type':'eq',
        'fun': lambda weights: np.sum(weights)-1
    }

    #Creating function to calculate sharpe ratio (negative)
    def neg_sharpe_ratio(weights,riskfree_rate,er,cov):
        """
        Returns the negative of the sharpe ratio, given weights
        """
        r = portfolio_return(weights,er)
        vol = portfolio_vol(weights,cov)
        return -(r - riskfree_rate)/vol

    results = minimize(
        neg_sharpe_ratio,#minimizing negative sharpe ratio is maximizing it
        init_guess,
        args=(riskfree_rate,er,cov,),
        method="SLSQP",#Quadratic programming optimizer
        constraints=(weights_sum_to_1),
        bounds=bounds
    )
    return results.x

def gmv(cov):
    """
    Returns the weight of the Global Minimum Volatilty portfolio
    given the covariance matrix 
    """
    # Logic : Give equal ER to all assets in MSR so only thing it can minimize is volatility, hence give GMV
    n = cov.shape[0]
    return msr(0,np.repeat(1,n),cov)

    
def plot_ef(n_points,er,cov,style=".-",riskfree_rate=0,show_cml=False,show_ew=False,show_gmv=False):
    """
    Plots the N-asset efficient frontier 
    """
    weights= optimal_weights(n_points,er,cov)
    rets = [portfolio_return(w,er) for w in weights]
    vols = [portfolio_vol(w,cov) for w in weights]
    ef = pd.DataFrame({
        "Returns":rets,
        "Volatility":vols
    })
    ax=ef.plot.line(
        x="Volatility",
        y="Returns",
        style=style)
    if show_ew:
        n = er.shape[0]
        w_ew=np.repeat(1/n,n)
        r_ew=portfolio_return(w_ew,er)
        vol_ew=portfolio_vol(w_ew,cov)
        #display EW
        ax.plot([vol_ew],[r_ew],color="goldenrod",marker="o",markersize="10")

    if show_gmv:
        w_gmv=gmv(cov) #Since gmv weights will only depend on covaariance and nothing else.
        r_gmv=portfolio_return(w_gmv,er)
        vol_gmv=portfolio_vol(w_gmv,cov)
        #display GMV
        ax.plot([vol_gmv],[r_gmv],color="midnightblue",marker="o",markersize="10")
           
    if show_cml:
        ax.set_xlim(left=0)
        w_msr = msr(riskfree_rate,er,cov)
        r_msr = portfolio_return(w_msr,er)
        vol_msr = portfolio_vol(w_msr,cov)
        # Plot CML 
        cml_x=[0,vol_msr]
        cml_y=[riskfree_rate,r_msr]
        ax.plot(cml_x,cml_y,
                color='green',
                marker='o',
                linestyle='dashed',
                markersize=12,
                linewidth=2)
        return ax

def run_cppi(risky_r,safe_r=None,m=3,start=1000,floor=0.8,riskfree_rate=0.03,drawdown=None):
    """
    Run backtest of the CPPI strategy, given a set of returns for the risky asset 
    Returns a dictionary containing: Asset Value History, Risk Budget History, Risky Weight History
    """
    # Set up CPPI parameters 
    dates = risky_r.index
    n_steps = len(dates) 
    account_value = start 
    floor_value = start*floor 
    peak = start

    if isinstance(risky_r,pd.Series):
        risky_r = pd.DataFrame(risky_r,columns=["R"])

    if safe_r is None:
        safe_r = pd.DataFrame().reindex_like(risky_r)
        safe_r[:] = riskfree_rate/12
    
    account_history = pd.DataFrame().reindex_like(risky_r)
    cushion_history = pd.DataFrame().reindex_like(risky_r)
    risky_w_history = pd.DataFrame().reindex_like(risky_r)
    
    for step in range(n_steps):
        if drawdown is not None:
            peak = np.maximum(peak,account_value)
            floor_value = peak*(1-drawdown) 
        cushion = (account_value-floor_value)/account_value
        risky_w = m*cushion
        risky_w = np.minimum(risky_w,1)
        risky_w = np.maximum(risky_w,0)
        safe_w = 1-risky_w
        risky_allocation = account_value*risky_w
        safe_allocation = account_value*safe_w
        # Update the account value for this time stamp
        account_value = (risky_allocation*(1+risky_r.iloc[step]) + safe_allocation*(1+safe_r.iloc[step]))
        # Save values to keep history 
        cushion_history.iloc[step] = cushion
        risky_w_history.iloc[step] = risky_w
        account_history.iloc[step] = account_value
    
    risky_wealth = start*(1+risky_r).cumprod()
    backtest_result = {
        "Wealth" : account_history,
        "Risky Wealth" : risky_wealth,
        "Risk Budget" : cushion_history,
        "Risky Allocation" : risky_w_history,
        "m" : m,
        "start" : start,
        "floor" : floor,
        "risky_r" : risky_r,
        "safe_r" : safe_r
    }
    return backtest_result

def summary_stats(r, riskfree_rate=0.03):
    """
    Return a DataFrame that contains aggregated summary stats for the returns in the columns of r
    """
    ann_r = r.aggregate(annualize_rets, periods_per_year=12)
    ann_vol = r.aggregate(annualize_vol, periods_per_year=12)
    ann_sr = r.aggregate(sharpe_ratio, riskfree_rate=riskfree_rate, periods_per_year=12)
    dd = r.aggregate(lambda r: drawdown(r).Drawdown.min())
    skew = r.aggregate(skewness)
    kurt = r.aggregate(kurtosis)
    cf_var5 = r.aggregate(var_gaussian, modified=True)
    hist_cvar5 = r.aggregate(cvar_historic)
    return pd.DataFrame({
        "Annualized Return": ann_r,
        "Annualized Vol": ann_vol,
        "Skewness": skew,
        "Kurtosis": kurt,
        "Cornish-Fisher VaR (5%)": cf_var5,
        "Historic CVaR (5%)": hist_cvar5,
        "Sharpe Ratio": ann_sr,
        "Max Drawdown": dd
    })

def gbm(n_years=10, n_scenarios=1000, mu=0.07, sigma=0.15, steps_per_year=12, s_0=100.0, prices=True):
    """
    Evolution of Geometric Brownian Motion trajectories, such as for Stock Prices through Monte Carlo
    n_years:  The number of years to generate data for
    n_paths: The number of scenarios/trajectories
    mu: Annualized Drift, e.g. Market Return
    sigma: Annualized Volatility
    steps_per_year: granularity of the simulation
    s_0: initial value
    return: a array of n_paths columns and n_years*steps_per_year rows
    """
    dt = 1/steps_per_year
    n_steps = int(n_years*steps_per_year) + 1
   
    rets_plus_1 = np.random.normal(loc=(1+mu*dt), scale=(sigma*np.sqrt(dt)), size=(n_steps, n_scenarios))
    rets_plus_1[0] = 1
    ret_val = s_0*pd.DataFrame(rets_plus_1).cumprod() if prices else (rets_plus_1-1)
    return ret_val