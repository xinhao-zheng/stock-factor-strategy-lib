"""
Stock Quant Strategy Framework
---------------------------------------------------
Author:    Xinhao Zheng
Contact:   Veritas428 (WeChat)
Copyright: (c) 2026 Xinhao Zheng. Licensed under the MIT License.
---------------------------------------------------
"""
import pandas as pd

fin_cols = ['C_ncf_from_oa@xbx_ttm', 'C_cash_paid_for_assets@xbx_ttm']
extra_data = {'dividend-delivery': ['近一年分红']}


def add_factor(df: pd.DataFrame, param=None, **kwargs) -> pd.DataFrame:
    """
    计算因子，以单列 DataFrame 返回。

    :param df: 单只股票的日频 K 线，按交易日期升序；fin_cols / extra_data 声明的列已由框架合并入 df。
    :param param: 因子参数，含义见下。
    :param kwargs: col_name —— 输出列名。
    :return: pd.DataFrame，仅含 col_name 一列，与 df 同索引、同长度。本函数不修改 df。

    FCF覆盖度因子
    ---------------------------------------------------
    含义：自由现金流TTM 对近一年分红总额的覆盖倍数。
    原理：> 1，自由现金流足以覆盖分红；< 1，分红多于自由现金流，差额来自存量或举债；≤ 0，自由现金流为负，
         分红全部依赖存量或举债。倍数只回答“撑不撑得住”，不回答“分得多不多”——用作过滤门槛。
    公式：FCF_TTM / 近一年分红总额
      FCF_TTM = 经营活动现金流净额TTM − 购建固定资产等支付的现金TTM
      近一年分红总额 = 近一年分红（每股）× 总股本，总股本 = 总市值 / 收盘价
    param: 无（传 ''）
    排序：不适用（过滤因子）
    边界：任一输入缺失、收盘价 ≤ 0 或近一年分红为 0 时为 NaN。
    选股因子案例：无
    过滤因子案例：('z_FCF覆盖度_zh', '', 'val:>=1', False)
    """
    col_name = kwargs['col_name']

    fcf_ttm = df['C_ncf_from_oa@xbx_ttm'] - df['C_cash_paid_for_assets@xbx_ttm']
    close = df['收盘价'].where(df['收盘价'] > 0)
    total_dividend = df['近一年分红'] * df['总市值'] / close

    return pd.DataFrame({col_name: fcf_ttm / total_dividend.where(total_dividend > 0)}, index=df.index)
