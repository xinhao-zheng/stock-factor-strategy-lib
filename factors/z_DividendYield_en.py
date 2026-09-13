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
extra_data = {'dividend-delivery': ['分红率_最近日']}


def add_factor(df: pd.DataFrame, param=None, **kwargs) -> pd.DataFrame:
    """
    Compute the factor and return it as a single-column DataFrame.

    :param df: Daily K-line of one stock, ascending by trade date; columns declared in fin_cols / extra_data
        are merged in by the host.
    :param param: Factor parameter; see below.
    :param kwargs: col_name — the output column name.
    :return: pd.DataFrame with the single column col_name, on the index and length of df. The function does
        not modify df.

    Current Dividend Yield Factor
    ---------------------------------------------------
    Meaning: Dividend yield measured at today's close.
    Principle: 分红率_最近日 = TTM dividend per share / daily close, refreshed every trading day by the host's
         data_bridge; 分红率_登记日 is fixed on the record date and forward-filled, so its denominator does not
         move with price. This factor passes the former through: the denominator moves with price, giving the
         yield locked in by buying at the current price.
    Formula: TTM Dividend per Share / Daily Close (= 分红率_最近日, passthrough)
    param: None (pass '')
    Sorting: False (larger is better)
    Boundary: NaN when no dividend record exists; 270 trading days after the latest record date with no new
         record, the host sets all dividend fields to NaN.
    Selection Case: ('z_DividendYield_en', False, '', 1)
    Filter Case:    ('z_DividendYield_en', '', 'pct:<=0.5', False)
    """
    col_name = kwargs['col_name']

    return pd.DataFrame({col_name: df['分红率_最近日']}, index=df.index)
