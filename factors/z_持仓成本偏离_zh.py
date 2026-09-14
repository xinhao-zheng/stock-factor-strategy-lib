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

    持仓成本偏离因子
    ---------------------------------------------------
    含义：收盘价相对 N 日成交量加权均价（VWAP）的偏离。
    原理：VWAP 近似窗口内成交者的平均持仓成本。偏离 > 0，现价高于成本，持仓者浮盈，上方套牢盘少；偏离 < 0，
         现价低于成本，持仓者浮亏，上方存在解套抛压。因子值大 ⇔ 现价在成本线上方更远。
    公式：(收盘价 − VWAP_N) / VWAP_N
      VWAP_N = sum(成交额, N) / sum(成交量, N)
    param: N（回看窗口，正整数，如 20）
    排序：False（值越大越优）
    边界：前 N − 1 行、窗口内成交量之和或成交额之和为 0 时为 NaN。停牌日由框架补为成交量、成交额、涨跌幅为 0
         的行，计入窗口。价格与成交量均为未复权口径：窗口跨越除权除息日时，VWAP 与现价的基准不一致，偏离中含
         除权跳空。
    选股因子案例：('z_持仓成本偏离_zh', False, 20, 1)
    """
    col_name = kwargs['col_name']
    n = int(param)
    if n <= 0:
        raise ValueError(f'param 须为正整数窗口，收到 {param!r}')

    amount_sum = df['成交额'].rolling(n, min_periods=n).sum()
    volume_sum = df['成交量'].rolling(n, min_periods=n).sum()
    vwap = amount_sum.where(amount_sum > 0) / volume_sum.where(volume_sum > 0)

    return pd.DataFrame({col_name: (df['收盘价'] - vwap) / vwap}, index=df.index)
