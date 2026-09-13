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
extra_data = {'dividend-delivery': ['近一年分红', '分红率_最近日']}


def add_factor(df: pd.DataFrame, param=None, **kwargs) -> pd.DataFrame:
    """
    Compute the factor and return it as a single-column DataFrame.

    :param df: Daily K-line of one stock, ascending by trade date; columns declared in fin_cols / extra_data
        are merged in by the host.
    :param param: Factor parameter; see below.
    :param kwargs: col_name — the output column name.
    :return: pd.DataFrame with the single column col_name, on the index and length of df. The function does
        not modify df.

    Dividend Safety Margin Factor
    ---------------------------------------------------
    Meaning: Current dividend yield times the clipped FCF coverage — only the part of the yield backed by free
         cash flow is counted.
    Principle: The dividend is the return; free cash flow is its source. A high yield paid out of borrowing or
         reserves does not last. FCF Coverage = TTM FCF / TTM total dividends, clipped to [0, cap]: coverage
         < 0 (negative FCF) is set to 0 and the effective yield collapses to zero; coverage > cap is set to
         cap, which bounds extreme values. A large value ⇔ a high yield covered by real cash flow.
    Formula: 分红率_最近日 × clip(FCF Coverage, 0, cap)
      FCF Coverage = (Operating Cash Flow TTM − CapEx TTM) / Total Dividend TTM
      Total Dividend TTM = Dividend per Share (TTM) × Total Shares, Total Shares = Market Cap / Close
    param: cap (coverage ceiling, default 3.0; 1.0 means a dividend exactly covered scores in full)
    Sorting: False (larger is better)
    Boundary: NaN when any input is missing, Close ≤ 0, or the TTM dividend is 0.
    Selection Case: ('z_DividendSafetyMargin_en', False, 3, 1)
    Filter Case:    ('z_DividendSafetyMargin_en', 3, 'pct:<=0.5', False)
    """
    col_name = kwargs['col_name']
    cap = float(param) if param not in (None, '') else 3.0

    fcf_ttm = df['C_ncf_from_oa@xbx_ttm'] - df['C_cash_paid_for_assets@xbx_ttm']
    close = df['收盘价'].where(df['收盘价'] > 0)
    total_dividend = df['近一年分红'] * df['总市值'] / close
    coverage = fcf_ttm / total_dividend.where(total_dividend > 0)

    return pd.DataFrame({col_name: df['分红率_最近日'] * coverage.clip(lower=0.0, upper=cap)}, index=df.index)
