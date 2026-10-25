"""
Crypto Quant Strategy Framework
---------------------------------------------------
Author:    Xinhao Zheng
Contact:   Veritas428 (WeChat)
Copyright: (c) 2026 Xinhao Zheng. Licensed under the MIT License.
---------------------------------------------------
"""
import pandas as pd


def signal_multi_params(df: pd.DataFrame, param_list) -> dict:
    """
    计算因子，每个参数返回一列 Series。

    :param df: 单个标的的 K 线，按时间升序；须包含 high、low、close 列。
    :param param_list: 因子参数序列，含义见下。
    :return: dict[param, pd.Series]，与 df 同索引、同长度；本函数不修改 df。

    均线上方占比因子
    ---------------------------------------------------
    含义：近 N 根 K 线中，典型价高于其 N 根均值的占比。
    原理：每根 K 线只记录位于均值哪一侧，舍弃距离；因子度量价格在均值上方停留多久，而非偏离多远。
         因子值大 ⇔ 多数时间在上方；因子值小 ⇔ 多数时间在下方。
    公式：mean(1{TP > MA_N}, N)，取值 [0, 1]
      TP = (high + low + close) / 3；MA_N = mean(TP, N)
    param: N（回看窗口，K 线根数，整数且 N ≥ 2，如 225）
    排序：False（降序：多头取最大值，空头取最小值）
    边界：相等或价格缺失计为下方。前 N 根两个窗口均不足（min_periods=1）：新标的自首根起即有值（首根为 0），
         与完整窗口同场排名。
    选币因子案例：('z_均线上方占比_zh', False, 225, 1)
    """
    tp = (df['high'] + df['low'] + df['close']) / 3
    result = {}
    for n in param_list:
        above = (tp > tp.rolling(n, min_periods=1).mean()).astype(float)
        result[n] = above.rolling(n, min_periods=1).mean()
    return result
