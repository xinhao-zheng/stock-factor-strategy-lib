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
extra_data = {'dividend-delivery': ['分红率_最近日']}


def add_factor(df: pd.DataFrame, param=None, **kwargs) -> pd.DataFrame:
    """
    计算因子，以单列 DataFrame 返回。

    :param df: 单只股票的日频 K 线，按交易日期升序；fin_cols / extra_data 声明的列已由框架合并入 df。
    :param param: 因子参数，含义见下。
    :param kwargs: col_name —— 输出列名。
    :return: pd.DataFrame，仅含 col_name 一列，与 df 同索引、同长度。本函数不修改 df。

    当前股息率因子
    ---------------------------------------------------
    含义：以当日收盘价计量的股息率。
    原理：分红率_最近日 = 近一年分红 / 当日收盘价，由框架 data_bridge 逐日更新；分红率_登记日 只在登记日取值、
         其后前向填充，分母不随价格变动。本因子透传前者：分母随价格变动，给出的是以当前价格买入所锁定的股息率。
    公式：近一年分红 / 当日收盘价（= 分红率_最近日，直接透传）
    param: 无（传 ''）
    排序：False（值越大越优）
    边界：无分红记录时为 NaN；最近登记日之后 270 个交易日无新记录，框架将分红数据整体置为 NaN。
    选股因子案例：('z_当前股息率_zh', False, '', 1)
    过滤因子案例：('z_当前股息率_zh', '', 'pct:<=0.5', False)
    """
    col_name = kwargs['col_name']

    return pd.DataFrame({col_name: df['分红率_最近日']}, index=df.index)
