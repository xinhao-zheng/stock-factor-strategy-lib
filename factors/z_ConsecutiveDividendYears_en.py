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
extra_data = {'dividend-delivery': ['连续分红年份']}


def add_factor(df: pd.DataFrame, param=None, **kwargs) -> pd.DataFrame:
    """
    Compute the factor and return it as a single-column DataFrame.

    :param df: Daily K-line of one stock, ascending by trade date; columns declared in fin_cols / extra_data
        are merged in by the host.
    :param param: Factor parameter; see below.
    :param kwargs: col_name — the output column name.
    :return: pd.DataFrame with the single column col_name, on the index and length of df. The function does
        not modify df.

    Consecutive Dividend Years Factor
    ---------------------------------------------------
    Meaning: Passthrough of the consecutive dividend years computed by the host's data_bridge.
    Principle: Counting back from the report period of the latest dividend, the number of years with an
         unbroken dividend record, as an integer (1, 2, 3 ...). The count records presence, not amount — a
         filter threshold, not a ranking factor.
    Formula: 连续分红年份 (passthrough)
    param: None (pass '')
    Sorting: Not applicable (filter factor)
    Boundary: NaN when no dividend record exists; 270 trading days after the latest record date with no new
         record, the host sets all dividend fields to NaN. The host's data_bridge accumulates in file order, not
         by record date: when a special or interim dividend puts report-period order at odds with record-date
         order, the span between two adjacent record dates absorbs a record not yet registered — a host-side
         limitation.
    Selection Case: None
    Filter Case:    ('z_ConsecutiveDividendYears_en', '', 'val:>=3', False)
    """
    col_name = kwargs['col_name']

    return pd.DataFrame({col_name: df['连续分红年份']}, index=df.index)
