"""
Stock Quant Strategy Framework
---------------------------------------------------
Author:    Xinhao Zheng
Contact:   Veritas428 (WeChat)
Copyright: (c) 2026 Xinhao Zheng. Licensed under the MIT License.
---------------------------------------------------
"""
import pandas as pd

# Path length below this is treated as no displacement and returns NaN
_EPS = 1e-10

fin_cols = []
extra_data = {}


def add_factor(df: pd.DataFrame, param=None, **kwargs) -> pd.DataFrame:
    """
    Compute the factor and return it as a single-column DataFrame.

    :param df: Daily K-line of one stock, ascending by trade date; columns declared in fin_cols / extra_data
        are merged in by the host.
    :param param: Factor parameter; see below.
    :param kwargs: col_name — the output column name.
    :return: pd.DataFrame with the single column col_name, on the index and length of df. The function does
        not modify df.

    Trend Purity Factor
    ---------------------------------------------------
    Meaning: N-day net return over path length — the Kaufman Efficiency Ratio.
    Principle: Path length = sum of absolute daily returns. When price runs one way the net return approaches
         the path length and purity tends to ±1; after repeated oscillation with a small net gain, the path is
         long and the displacement small, and purity tends to 0. A large value ⇔ rising with few reversals.
    Formula: (收盘价_复权_t / 收盘价_复权_{t−N} − 1) / Σ|Daily Return|
      The lower bound −1 is strict; the upper bound 1 can be exceeded under simple returns by upside compounding
      (strictly bounded in [−1, 1] under log returns)
    param: N (lookback window, positive integer, e.g. 20)
    Sorting: False (larger is better)
    Boundary: NaN for the first N rows and when the path length is below 1e-10 (no displacement). Suspension
         days are filled by the host with zero volume, amount and return, and count toward the window.
    Selection Case: ('z_TrendPurity_en', False, 20, 1)
    """
    col_name = kwargs['col_name']
    n = int(param)
    if n <= 0:
        raise ValueError(f'param must be a positive integer window, got {param!r}')

    price = df['收盘价_复权']
    net_return = price / price.shift(n) - 1
    path_length = price.pct_change(fill_method=None).abs().rolling(n, min_periods=n).sum()

    return pd.DataFrame({col_name: net_return / path_length.where(path_length > _EPS)}, index=df.index)
