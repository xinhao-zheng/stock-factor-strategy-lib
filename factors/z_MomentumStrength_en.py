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

    Momentum Strength Factor
    ---------------------------------------------------
    Meaning: N-day cumulative return weighted by the share of up days.
    Principle: The same cumulative return can come from one or two jumps or from many small gains; the former
         does not persist. Weight = 2 × up-day share − 1, in [−1, 1]: a share of 1 keeps the full return, 0.5
         zeroes it, and a lower share flips its sign. A large value ⇔ a large gain with most days closing up.
    Formula: pct_change(收盘价_复权, N) × (2 × up_ratio − 1)
      up_ratio = share of days with 涨跌幅 > 0 within N days
    param: N (lookback window, e.g. 20)
    Sorting: False (larger is better)
    Boundary: NaN for the first N rows.
    Selection Case: ('z_MomentumStrength_en', False, 20, 1)
    """
    col_name = kwargs['col_name']
    n = int(param)

    total_return = df['收盘价_复权'].pct_change(n, fill_method=None)
    up_ratio = df['涨跌幅'].gt(0).astype(float).rolling(n, min_periods=n).mean()

    return pd.DataFrame({col_name: total_return * (2 * up_ratio - 1)}, index=df.index)
