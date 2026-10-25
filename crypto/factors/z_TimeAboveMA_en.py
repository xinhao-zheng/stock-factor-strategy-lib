"""
Crypto Quant Strategy Framework
---------------------------------------------------
Author:    Xinhao Zheng
Contact:   Veritas428 (WeChat)
Copyright: (c) 2026 Xinhao Zheng. Licensed under the MIT License.
---------------------------------------------------
"""
import pandas as pd


def signal_multi_params(df: pd.DataFrame, param_list) -> dict:
    """
    Compute the factor and return one Series per param.

    :param df: K-line of one symbol, ascending by time; requires high, low and close.
    :param param_list: Sequence of factor parameters; see below.
    :return: dict[param, pd.Series], preserving df's index and length without modifying df.

    Time Above MA Factor
    ---------------------------------------------------
    Meaning: Share of the last N bars in which the typical price stood above its N-bar mean.
    Principle: Each bar counts only which side of its mean it falls on, so the factor measures how long price
         has held above, not how far. A large value ⇔ mostly above; a small value ⇔ mostly below.
    Formula: mean(1{TP > MA_N}, N), in [0, 1]
      TP = (high + low + close) / 3; MA_N = mean(TP, N)
    param: N (lookback window in bars, integer ≥ 2, e.g. 225)
    Sorting: False (descending: long takes the largest values, short the smallest)
    Boundary: Ties and missing prices count as below. Before N bars both windows are partial (min_periods=1):
         new symbols carry values from their first bar, which is 0, and rank alongside full windows.
    Selection Case: ('z_TimeAboveMA_en', False, 225, 1)
    """
    tp = (df['high'] + df['low'] + df['close']) / 3
    result = {}
    for n in param_list:
        above = (tp > tp.rolling(n, min_periods=1).mean()).astype(float)
        result[n] = above.rolling(n, min_periods=1).mean()
    return result
