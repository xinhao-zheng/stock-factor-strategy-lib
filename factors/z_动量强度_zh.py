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
    计算因子，以单列 DataFrame 返回。

    :param df: 单只股票的日频 K 线，按交易日期升序；fin_cols / extra_data 声明的列已由框架合并入 df。
    :param param: 因子参数，含义见下。
    :param kwargs: col_name —— 输出列名。
    :return: pd.DataFrame，仅含 col_name 一列，与 df 同索引、同长度。本函数不修改 df。

    动量强度因子
    ---------------------------------------------------
    含义：N 日累计涨幅按上涨天数占比加权。
    原理：同样的累计涨幅，可由一两日跳涨贡献，也可由多日小涨累积；前者不可持续。权重 = 2 × 上涨天数占比 − 1，
         取值 [−1, 1]：占比 1 得满权，占比 0.5 归零，占比更低则反号。因子值大 ⇔ 涨幅大且多数交易日收涨。
    公式：pct_change(收盘价_复权, N) × (2 × up_ratio − 1)
      up_ratio = N 日内涨跌幅 > 0 的天数占比
    param: N（回看窗口，如 20）
    排序：False（值越大越优）
    边界：前 N 行为 NaN。
    选股因子案例：('z_动量强度_zh', False, 20, 1)
    """
    col_name = kwargs['col_name']
    n = int(param)

    total_return = df['收盘价_复权'].pct_change(n, fill_method=None)
    up_ratio = df['涨跌幅'].gt(0).astype(float).rolling(n, min_periods=n).mean()

    return pd.DataFrame({col_name: total_return * (2 * up_ratio - 1)}, index=df.index)
