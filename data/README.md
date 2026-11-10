# Data

## Included dataset

- `ind30_m_vw_rets.csv`: monthly value-weighted returns for the 30 Ken French industry portfolios.
- Source: [Kenneth R. French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html).
- Snapshot in this repository: July 1926–December 2018, 1,110 observations.
- The CSV stores percentage points. The loader in `risk_kit.py` converts these to decimal returns.

The dataset is committed to make the core analyses reproducible without a network download.

## Optional market-cap companion data

The original market-cap-weighting exercise also needs monthly firm counts and average firm sizes by industry. These two companion inputs are not bundled in this repository snapshot:

- `ind30_m_nfirms.csv`: industry firm counts.
- `ind30_m_size.csv`: average firm size by industry.

To enable the optional market-cap-weighted index section, obtain the corresponding monthly 30-industry files from the Ken French Data Library and save them with those filenames. Normalize each to a CSV with a `YYYYMM` first/index column and matching industry column names. Values should be numeric; return observations alone are expressed in percentage points. Counts and size values are not returns and must not be divided by 100.

If the companion inputs are absent, `get_ind_nfirms()`, `get_ind_size()` and `get_total_market_index_returns()` raise a descriptive `FileNotFoundError`. Notebooks catch this only around optional sections; the included-data analyses continue to run. No market-cap values are imputed or invented.
