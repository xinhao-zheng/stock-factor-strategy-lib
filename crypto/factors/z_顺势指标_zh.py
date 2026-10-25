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

    顺势指标因子
    ---------------------------------------------------
    含义：典型价相对 N 根均值的偏离，以平均偏差标准化——顺势指标（Commodity Channel Index, CCI）。
    原理：除以平均偏差，消去价格单位与各标的自身波动，各标的在同一尺度上排名。因子值大 ⇔ 价格远高于近期均值；
         因子值小 ⇔ 远低于近期均值。
    公式：(TP − MA_N) / (0.015 × MD_N)
      TP = (high + low + close) / 3；MA_N = mean(TP, N)；MD_N = mean(|TP − MA_N|, N)
      MD_N 取每根 K 线相对其当时 MA_N 的偏差均值；Lambert 原定义（TA-Lib 采用）以当前 MA_N 度量整个窗口，
      数值因此不同
    param: N（回看窗口，K 线根数，整数且 N ≥ 2，如 150）
    排序：False（降序：多头取最大值，空头取最小值）
    边界：MD_N = 0 时为 NaN，含首根 K 线。前 N 根窗口不足（min_periods=1）：新标的自第二根起即有值，与完整窗口
         同场排名。
    选币因子案例：('z_顺势指标_zh', False, 150, 1)
    """
    tp = (df['high'] + df['low'] + df['close']) / 3
    result = {}
    for n in param_list:
        deviation = tp - tp.rolling(n, min_periods=1).mean()
        mean_deviation = deviation.abs().rolling(n, min_periods=1).mean()
        result[n] = deviation / (0.015 * mean_deviation)
    return result
