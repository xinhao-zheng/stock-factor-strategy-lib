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
extra_data = {'dividend-delivery': ['分红率_登记日_近年均值', '分红率_登记日_近年标准差']}


def add_factor(df: pd.DataFrame, param=None, **kwargs) -> pd.DataFrame:
    """
    Compute the factor and return it as a single-column DataFrame.

    :param df: Daily K-line of one stock, ascending by trade date; columns declared in fin_cols / extra_data
        are merged in by the host.
    :param param: Factor parameter; see below.
    :param kwargs: col_name — the output column name.
    :return: pd.DataFrame with the single column col_name, on the index and length of df. The function does
        not modify df.

    Dividend Quality Factor
    ---------------------------------------------------
    Meaning: Three-year mean dividend yield, discounted by its volatility.
    Principle: Discount = Mean / (Mean + k × Std), in (0, 1]. A high and stable mean scores high; a high but
         volatile mean is discounted; a low mean cannot rank up however stable it is. A larger k is more
         sensitive to volatility; k = 0 degenerates to a pure mean ranking.
    Formula: Mean × Mean / (Mean + k × Std)
      Mean = 分红率_登记日_近年均值, Std = 分红率_登记日_近年标准差
      (computed by the host's data_bridge over record-date entries within three years of the report period)
    param: k (volatility penalty, default 1; 0.5 lenient, 2 strict)
    Sorting: False (larger is better)
    Boundary: NaN when Mean or Std is missing — with a single record within three years Std is undefined,
         stability cannot be judged, and 0 is not substituted; NaN when the denominator is 0.
    Selection Case: ('z_DividendQuality_en', False, 1, 1)
    Filter Case:    ('z_DividendQuality_en', 1, 'pct:<=0.5', False)
    """
    col_name = kwargs['col_name']
    k = float(param) if param not in (None, '') else 1.0

    mean = df['分红率_登记日_近年均值']
    std = df['分红率_登记日_近年标准差']
    denominator = mean + k * std

    return pd.DataFrame({col_name: mean * mean / denominator.where(denominator > 0)}, index=df.index)
