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

    Volume Ratio Factor
    ---------------------------------------------------
    Meaning: Ratio of short-window to long-window mean turnover amount.
    Principle: Ratio > 1, recent volume has expanded above its norm; Ratio < 1, recent volume has contracted.
         A large value ⇔ a larger volume expansion.
    Formula: mean(Amount, short) / mean(Amount, long)
    param: (short, long), positive integers with short < long, e.g. (5, 60)
    Sorting: False (larger is better)
    Boundary: NaN for the first long − 1 rows and when the long-window mean amount is 0. Suspension days are
         filled by the host with zero volume, amount and return, and count toward the window.
    Selection Case: ('z_VolumeRatio_en', False, (5, 60), 1)
    """
    col_name = kwargs['col_name']
    short, long = (int(x) for x in param)
    if not 0 < short < long:
        raise ValueError(f'param must be (short, long) with 0 < short < long, got {param!r}')

    short_avg = df['成交额'].rolling(short, min_periods=short).mean()
    long_avg = df['成交额'].rolling(long, min_periods=long).mean()

    return pd.DataFrame({col_name: short_avg / long_avg.where(long_avg > 0)}, index=df.index)
