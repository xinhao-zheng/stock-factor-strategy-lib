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

    量比因子
    ---------------------------------------------------
    含义：短窗口成交额均值与长窗口成交额均值之比。
    原理：比值 > 1，近期放量，成交活跃度高于常态；比值 < 1，近期缩量。因子值大 ⇔ 放量幅度大。
    公式：mean(成交额, short) / mean(成交额, long)
    param: (short, long)，如 (5, 60)
    排序：False（值越大越优）
    边界：前 long − 1 行、长窗口成交额均值为 0 时为 NaN。
    选股因子案例：('z_量比_zh', False, (5, 60), 1)
    """
    col_name = kwargs['col_name']
    short, long = (int(x) for x in param)

    short_avg = df['成交额'].rolling(short, min_periods=short).mean()
    long_avg = df['成交额'].rolling(long, min_periods=long).mean()

    return pd.DataFrame({col_name: short_avg / long_avg.where(long_avg > 0)}, index=df.index)
