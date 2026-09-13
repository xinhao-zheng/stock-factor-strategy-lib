"""
Stock Quant Strategy Framework
---------------------------------------------------
Author:    Xinhao Zheng
Contact:   Veritas428 (WeChat)
Copyright: (c) 2026 Xinhao Zheng. Licensed under the MIT License.
---------------------------------------------------
"""
import pandas as pd

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

    Momentum Volatility Factor
    ---------------------------------------------------
    Meaning: Product of the N-day mean and standard deviation of daily returns.
    Principle: The mean gives direction and magnitude; the standard deviation gives activity. The product peaks
         when the mean is positive and volatility is high, and turns more negative with volatility when the
         mean is negative. A large value ⇔ rising with expanding volatility — trend and activity at once.
    Formula: mean(Return, N) × std(Return, N)
    param: N (lookback window, e.g. 20)
    Sorting: False (larger is better)
    Boundary: NaN for the first N − 1 rows.
    Selection Case: ('z_MomentumVolatility_en', False, 20, 1)
    """
    col_name = kwargs['col_name']
    n = int(param)

    window = df['涨跌幅'].rolling(n, min_periods=n)

    return pd.DataFrame({col_name: window.mean() * window.std()}, index=df.index)
