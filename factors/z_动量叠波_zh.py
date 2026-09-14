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

    动量叠波因子
    ---------------------------------------------------
    含义：N 日涨跌幅均值与标准差之积。
    原理：均值给方向与幅度，标准差给活跃度。乘积在均值为正且波动大时最大，均值为负时随波动放大而更负。
         因子值大 ⇔ 上涨且波动放大——趋势与活跃度同时成立。
    公式：mean(涨跌幅, N) × std(涨跌幅, N)
    param: N（回看窗口，整数且 ≥ 2，如 20）
    排序：False（值越大越优）
    边界：前 N − 1 行为 NaN。停牌日由框架补为成交量、成交额、涨跌幅为 0 的行，计入窗口。
    选股因子案例：('z_动量叠波_zh', False, 20, 1)
    """
    col_name = kwargs['col_name']
    n = int(param)
    if n < 2:
        raise ValueError(f'param 须为不小于 2 的整数窗口，收到 {param!r}')

    window = df['涨跌幅'].rolling(n, min_periods=n)

    return pd.DataFrame({col_name: window.mean() * window.std()}, index=df.index)
