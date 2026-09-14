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
extra_data = {'dividend-delivery': ['近一年分红', '分红率_最近日']}


def add_factor(df: pd.DataFrame, param=None, **kwargs) -> pd.DataFrame:
    """
    计算因子，以单列 DataFrame 返回。

    :param df: 单只股票的日频 K 线，按交易日期升序；fin_cols / extra_data 声明的列已由框架合并入 df。
    :param param: 因子参数，含义见下。
    :param kwargs: col_name —— 输出列名。
    :return: pd.DataFrame，仅含 col_name 一列，与 df 同索引、同长度。本函数不修改 df。

    红利安全边际因子
    ---------------------------------------------------
    含义：当前股息率乘以截断后的 FCF覆盖度——只计入有自由现金流支撑的那部分股息。
    原理：股息是回报，自由现金流是股息的来源；靠举债或消耗存量维持的高股息不可持续。
         FCF覆盖度 = 自由现金流TTM / 近一年分红总额，截断到 [0, cap]：覆盖度 < 0（自由现金流为负）记 0，
         有效股息率归零；覆盖度 > cap 记 cap，抑制极端值。因子值大 ⇔ 股息率高且被真实现金流覆盖。
    公式：分红率_最近日 × clip(FCF覆盖度, 0, cap)
      FCF覆盖度 = (经营活动现金流净额TTM − 购建固定资产等支付的现金TTM) / 近一年分红总额
      近一年分红总额 = 近一年分红（每股）× 总股本，总股本 = 总市值 / 收盘价
    param: cap（覆盖度上限，正数，默认 3.0；1.0 表示分红恰被覆盖即满分）
    排序：False（值越大越优）
    边界：任一输入缺失、收盘价 ≤ 0 或近一年分红为 0 时为 NaN。
    选股因子案例：('z_红利安全边际_zh', False, 3, 1)
    过滤因子案例：('z_红利安全边际_zh', 3, 'pct:<=0.5', False)
    """
    col_name = kwargs['col_name']
    cap = float(param) if param not in (None, '') else 3.0
    if cap <= 0:
        raise ValueError(f'param 须为正的覆盖度上限，收到 {param!r}')

    fcf_ttm = df['C_ncf_from_oa@xbx_ttm'] - df['C_cash_paid_for_assets@xbx_ttm']
    close = df['收盘价'].where(df['收盘价'] > 0)
    total_dividend = df['近一年分红'] * df['总市值'] / close
    coverage = fcf_ttm / total_dividend.where(total_dividend > 0)

    return pd.DataFrame({col_name: df['分红率_最近日'] * coverage.clip(lower=0.0, upper=cap)}, index=df.index)
