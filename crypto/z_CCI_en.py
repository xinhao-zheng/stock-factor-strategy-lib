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

    Commodity Channel Index Factor
    ---------------------------------------------------
    Meaning: Deviation of the typical price from its N-bar mean, scaled by mean deviation — the Commodity
         Channel Index (CCI).
    Principle: Dividing by the mean deviation cancels price units and each symbol's own volatility, so symbols
         rank on one scale. A large value ⇔ price far above its recent mean; a small value ⇔ far below.
    Formula: (TP − MA_N) / (0.015 × MD_N)
      TP = (high + low + close) / 3; MA_N = mean(TP, N); MD_N = mean(|TP − MA_N|, N)
      MD_N averages each bar's deviation from its own MA_N; Lambert's definition, used by TA-Lib, measures the
      whole window from the current MA_N, so values differ
    param: N (lookback window in bars, integer ≥ 2, e.g. 150)
    Sorting: False (descending: long takes the largest values, short the smallest)
    Boundary: NaN when MD_N = 0, including the first bar. Before N bars the window is partial (min_periods=1):
         new symbols carry values from their second bar and rank alongside full windows.
    Selection Case: ('z_CCI_en', False, 150, 1)
    """
    tp = (df['high'] + df['low'] + df['close']) / 3
    result = {}
    for n in param_list:
        deviation = tp - tp.rolling(n, min_periods=1).mean()
        mean_deviation = deviation.abs().rolling(n, min_periods=1).mean()
        result[n] = deviation / (0.015 * mean_deviation)
    return result
