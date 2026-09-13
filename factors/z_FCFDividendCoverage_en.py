"""
Stock Quant Strategy Framework
---------------------------------------------------
Author:    Xinhao Zheng
Contact:   Veritas428 (WeChat)
Copyright: (c) 2026 Xinhao Zheng. Licensed under the MIT License.
---------------------------------------------------
"""
import pandas as pd

fin_cols = ['C_ncf_from_oa@xbx_ttm', 'C_cash_paid_for_assets@xbx_ttm']
extra_data = {'dividend-delivery': ['近一年分红']}


def add_factor(df: pd.DataFrame, param=None, **kwargs) -> pd.DataFrame:
    """
    Compute the factor and return it as a single-column DataFrame.

    :param df: Daily K-line of one stock, ascending by trade date; columns declared in fin_cols / extra_data
        are merged in by the host.
    :param param: Factor parameter; see below.
    :param kwargs: col_name — the output column name.
    :return: pd.DataFrame with the single column col_name, on the index and length of df. The function does
        not modify df.

    FCF Dividend Coverage Factor
    ---------------------------------------------------
    Meaning: How many times TTM free cash flow covers TTM total dividends.
    Principle: > 1, free cash flow covers the dividend; < 1, the dividend exceeds free cash flow and the gap is
         paid from reserves or borrowing; ≤ 0, free cash flow is negative and the dividend rests entirely on
         reserves or borrowing. The multiple answers "can it be sustained", not "how much is paid" — a filter
         threshold.
    Formula: FCF_TTM / Total Dividend TTM
      FCF_TTM = Operating Cash Flow TTM − CapEx TTM
      Total Dividend TTM = Dividend per Share (TTM) × Total Shares, Total Shares = Market Cap / Close
    param: None (pass '')
    Sorting: Not applicable (filter factor)
    Boundary: NaN when any input is missing, Close ≤ 0, or the TTM dividend is 0.
    Selection Case: None
    Filter Case:    ('z_FCFDividendCoverage_en', '', 'val:>=1', False)
    """
    col_name = kwargs['col_name']

    fcf_ttm = df['C_ncf_from_oa@xbx_ttm'] - df['C_cash_paid_for_assets@xbx_ttm']
    close = df['收盘价'].where(df['收盘价'] > 0)
    total_dividend = df['近一年分红'] * df['总市值'] / close

    return pd.DataFrame({col_name: fcf_ttm / total_dividend.where(total_dividend > 0)}, index=df.index)
