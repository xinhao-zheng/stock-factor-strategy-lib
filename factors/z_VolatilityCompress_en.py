"""
Stock Quant Strategy Framework
---------------------------------------------------
Author:    Xinhao Zheng
Contact:   Veritas428 (WeChat)
Copyright: (c) 2026 Xinhao Zheng. Licensed under the MIT License.
---------------------------------------------------
"""
import pandas as pd

# Long-window volatility below this is treated as no volatility and returns NaN
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

    Volatility Compression Factor
    ---------------------------------------------------
    Meaning: Ratio of short-window to long-window volatility.
    Principle: Ratio > 1, recent volatility has expanded and the stock has left consolidation for an active
         phase; Ratio < 1, recent volatility has contracted and the stock is still consolidating. A large value
         ⇔ volatility is expanding.
    Formula: std(Return, short) / std(Return, long)
    param: (short, long), integers with 2 ≤ short < long, e.g. (10, 60)
    Sorting: False (larger is better)
    Boundary: NaN for the first long − 1 rows and when long-window volatility is below 1e-10 (no volatility).
         Suspension days are filled by the host with zero volume, amount and return, and count toward the window.
    Selection Case: ('z_VolatilityCompress_en', False, (10, 60), 1)
    """
    col_name = kwargs['col_name']
    short, long = (int(x) for x in param)
    if not 1 < short < long:
        raise ValueError(f'param must be (short, long) with 2 ≤ short < long, got {param!r}')

    short_vol = df['涨跌幅'].rolling(short, min_periods=short).std()
    long_vol = df['涨跌幅'].rolling(long, min_periods=long).std()

    return pd.DataFrame({col_name: short_vol / long_vol.where(long_vol > _EPS)}, index=df.index)
