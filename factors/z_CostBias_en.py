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

    VWAP Bias Factor
    ---------------------------------------------------
    Meaning: Deviation of the close from the N-day volume-weighted average price (VWAP).
    Principle: VWAP approximates the average holding cost of those who traded within the window. Bias > 0,
         price above cost, holders in profit, little overhead supply; Bias < 0, price below cost, holders at a
         loss, break-even selling overhead. A large value ⇔ price further above the cost line.
    Formula: (Close − VWAP_N) / VWAP_N
      VWAP_N = sum(Amount, N) / sum(Volume, N)
    param: N (lookback window, positive integer, e.g. 20)
    Sorting: False (larger is better)
    Boundary: NaN for the first N − 1 rows and when the window's volume sum or amount sum is 0. Suspension days
         are filled by the host with zero volume, amount and return, and count toward the window. Price and
         volume are unadjusted: when the window spans an ex-dividend or ex-rights date, VWAP and the close rest
         on different bases, and the bias carries the ex-date gap.
    Selection Case: ('z_CostBias_en', False, 20, 1)
    """
    col_name = kwargs['col_name']
    n = int(param)
    if n <= 0:
        raise ValueError(f'param must be a positive integer window, got {param!r}')

    amount_sum = df['成交额'].rolling(n, min_periods=n).sum()
    volume_sum = df['成交量'].rolling(n, min_periods=n).sum()
    vwap = amount_sum.where(amount_sum > 0) / volume_sum.where(volume_sum > 0)

    return pd.DataFrame({col_name: (df['收盘价'] - vwap) / vwap}, index=df.index)
