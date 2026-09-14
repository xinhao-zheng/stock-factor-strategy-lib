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
    计算因子，以单列 DataFrame 返回。

    :param df: 单只股票的日频 K 线，按交易日期升序；fin_cols / extra_data 声明的列已由框架合并入 df。
    :param param: 因子参数，含义见下。
    :param kwargs: col_name —— 输出列名。
    :return: pd.DataFrame，仅含 col_name 一列，与 df 同索引、同长度。本函数不修改 df。

    分红质量因子
    ---------------------------------------------------
    含义：近三年分红率的均值，按其波动折价。
    原理：折价系数 = 均值 / (均值 + k × 标准差)，取值在 (0, 1]。均值高且波动小者得分高；均值高而波动大者被折价；
         均值低者无论多稳都排不上去。k 越大对波动越敏感，k = 0 退化为纯均值排序。
    公式：均值 × 均值 / (均值 + k × 标准差)
      均值 = 分红率_登记日_近年均值，标准差 = 分红率_登记日_近年标准差
      （框架 data_bridge 以报告期回溯三年内的登记日记录计算）
    param: k（波动惩罚系数，非负，默认 1；0.5 宽松，2 严格）
    排序：False（值越大越优）
    边界：均值或标准差缺失时为 NaN——三年内仅一条分红记录时标准差缺失，稳定性不可判定，不以 0 代之；
         分母为 0 时为 NaN。框架 data_bridge 按报告期开窗，不按登记日截断：特别分红、中期分红使报告期与登记日
         排序冲突时，相邻两个登记日之间会提前吸收尚未登记的记录，属框架侧限制。
    选股因子案例：('z_分红质量_zh', False, 1, 1)
    过滤因子案例：('z_分红质量_zh', 1, 'pct:<=0.5', False)
    """
    col_name = kwargs['col_name']
    k = float(param) if param not in (None, '') else 1.0
    if k < 0:
        raise ValueError(f'param 须为非负的波动惩罚系数，收到 {param!r}')

    mean = df['分红率_登记日_近年均值']
    std = df['分红率_登记日_近年标准差']
    denominator = mean + k * std

    return pd.DataFrame({col_name: mean * mean / denominator.where(denominator > 0)}, index=df.index)
