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
extra_data = {'dividend-delivery': ['连续分红年份']}


def add_factor(df: pd.DataFrame, param=None, **kwargs) -> pd.DataFrame:
    """
    计算因子，以单列 DataFrame 返回。

    :param df: 单只股票的日频 K 线，按交易日期升序；fin_cols / extra_data 声明的列已由框架合并入 df。
    :param param: 因子参数，含义见下。
    :param kwargs: col_name —— 输出列名。
    :return: pd.DataFrame，仅含 col_name 一列，与 df 同索引、同长度。本函数不修改 df。

    连续分红年份因子
    ---------------------------------------------------
    含义：透传框架 data_bridge 计算的连续分红年份。
    原理：自最近一次分红的报告期起向前回溯，分红记录不间断的年数，取整数（1, 2, 3 …）。计数只反映有无，
         不反映金额——用作过滤门槛，不用于排序。
    公式：连续分红年份（直接透传）
    param: 无（传 ''）
    排序：不适用（过滤因子）
    边界：无分红记录时为 NaN；最近登记日之后 270 个交易日无新记录，框架将分红数据整体置为 NaN。框架 data_bridge
         按文件行序累计，不按登记日截断：特别分红、中期分红使报告期与登记日排序冲突时，相邻两个登记日之间会提前
         吸收尚未登记的记录，属框架侧限制。
    选股因子案例：无
    过滤因子案例：('z_连续分红年份_zh', '', 'val:>=3', False)
    """
    col_name = kwargs['col_name']

    return pd.DataFrame({col_name: df['连续分红年份']}, index=df.index)
