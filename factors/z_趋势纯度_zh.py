"""
Stock Quant Strategy Framework
---------------------------------------------------
Author:    Xinhao Zheng
Contact:   Veritas428 (WeChat)
Copyright: (c) 2026 Xinhao Zheng. Licensed under the MIT License.
---------------------------------------------------
"""
import pandas as pd

# 路径长度低于此值视为无位移，返回 NaN
_EPS = 1e-10

fin_cols = []
extra_data = {}


def add_factor(df: pd.DataFrame, param=None, **kwargs) -> pd.DataFrame:
    """
    计算因子，以单列 DataFrame 返回。

    :param df: 单只股票的日频 K 线，按交易日期升序；fin_cols / extra_data 声明的列已由框架合并入 df。
    :param param: 因子参数，含义见下。
    :param kwargs: col_name —— 输出列名。
    :return: pd.DataFrame，仅含 col_name 一列，与 df 同索引、同长度。本函数不修改 df。

    趋势纯度因子
    ---------------------------------------------------
    含义：N 日净收益与路径长度之比——考夫曼效率系数（Kaufman Efficiency Ratio）。
    原理：路径长度 = 日收益绝对值之和。价格单向运行时净收益接近路径长度，纯度趋近 ±1；反复震荡后微涨，路径长
         而位移小，纯度趋近 0。因子值大 ⇔ 上涨且路径少折返。
    公式：(收盘价_复权_t / 收盘价_复权_{t−N} − 1) / Σ|日收益|
      简单收益下近似有界于 [−1, 1]
    param: N（回看窗口，如 20）
    排序：False（值越大越优）
    边界：前 N 行、路径长度低于 1e-10（视为无位移）时为 NaN。
    选股因子案例：('z_趋势纯度_zh', False, 20, 1)
    """
    col_name = kwargs['col_name']
    n = int(param)

    price = df['收盘价_复权']
    net_return = price / price.shift(n) - 1
    path_length = price.pct_change(fill_method=None).abs().rolling(n, min_periods=n).sum()

    return pd.DataFrame({col_name: net_return / path_length.where(path_length > _EPS)}, index=df.index)
