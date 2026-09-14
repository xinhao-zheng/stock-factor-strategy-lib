"""
Stock Quant Strategy Framework
---------------------------------------------------
Author:    Xinhao Zheng
Contact:   Veritas428 (WeChat)
Copyright: (c) 2026 Xinhao Zheng. Licensed under the MIT License.
---------------------------------------------------
"""
import pandas as pd

# 长窗口波动率低于此值视为无波动，返回 NaN
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

    波动压缩因子
    ---------------------------------------------------
    含义：短窗口波动率与长窗口波动率之比。
    原理：比值 > 1，近期波动相对放大，个股脱离盘整进入活跃期；比值 < 1，近期波动收敛，仍在盘整。
         因子值大 ⇔ 波动正在放大。
    公式：std(涨跌幅, short) / std(涨跌幅, long)
    param: (short, long)，整数且 2 ≤ short < long，如 (10, 60)
    排序：False（值越大越优）
    边界：前 long − 1 行、长窗口波动率低于 1e-10（视为无波动）时为 NaN。停牌日由框架补为成交量、成交额、涨跌幅
         为 0 的行，计入窗口。
    选股因子案例：('z_波动压缩_zh', False, (10, 60), 1)
    """
    col_name = kwargs['col_name']
    short, long = (int(x) for x in param)
    if not 1 < short < long:
        raise ValueError(f'param 须为 (short, long) 且 2 ≤ short < long，收到 {param!r}')

    short_vol = df['涨跌幅'].rolling(short, min_periods=short).std()
    long_vol = df['涨跌幅'].rolling(long, min_periods=long).std()

    return pd.DataFrame({col_name: short_vol / long_vol.where(long_vol > _EPS)}, index=df.index)
