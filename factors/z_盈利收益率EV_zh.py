"""
Stock Quant Strategy Framework
---------------------------------------------------
Author:    Xinhao Zheng
Contact:   Veritas428 (WeChat)
Copyright: (c) 2026 Xinhao Zheng. Licensed under the MIT License.
---------------------------------------------------
"""
import pandas as pd

# param → 净利润列
_PROFIT_COLS = {'全年': 'R_np@xbx_ttm', '单季': 'R_np@xbx_单季'}

# 企业价值的加项科目；货币资金为减项；总资产只用作资产负债表是否存在的锚点，不参与计算
_EV_ADDENDS = [
    'B_st_borrow@xbx', 'B_lt_loan@xbx', 'B_bond_payable@xbx',
    'B_lease_libilities@xbx', 'B_minority_equity@xbx', 'B_preferred_shares@xbx',
]
_EV_CASH = 'B_currency_fund@xbx'
_EV_ANCHOR = 'B_total_assets@xbx'

fin_cols = [*_PROFIT_COLS.values(), *_EV_ADDENDS, _EV_CASH, _EV_ANCHOR]
extra_data = {}


def add_factor(df: pd.DataFrame, param=None, **kwargs) -> pd.DataFrame:
    """
    计算因子，以单列 DataFrame 返回。

    :param df: 单只股票的日频 K 线，按交易日期升序；fin_cols / extra_data 声明的列已由框架合并入 df。
    :param param: 因子参数，含义见下。
    :param kwargs: col_name —— 输出列名。
    :return: pd.DataFrame，仅含 col_name 一列，与 df 同索引、同长度。本函数不修改 df。

    盈利收益率EV因子
    ---------------------------------------------------
    含义：企业价值口径的 EP——净利润除以 EV 而非总市值。
    原理：EP = 净利润 / 总市值 只站在股东视角；以 EV 为分母后，高杠杆公司不再因市值小而显得便宜，净现金公司
         则相应更便宜。因子值大 ⇔ 整家公司标价下的盈利回报率高，即估值低。
    公式：净利润 / EV
      EV = 总市值 + 短期借款 + 长期借款 + 应付债券 + 租赁负债 + 少数股东权益 + 优先股 − 货币资金
    param: '全年'（净利润TTM）或 '单季'（最近单季净利润）
    排序：False（值越大越优）
    边界：报表未列示的科目记 0——未列示即为零，非缺失；净利润缺失、总市值缺失、资产负债表缺失（总资产为空）
         或 EV ≤ 0 时为 NaN。银行、保险的报表格式不含借款与货币资金科目，其 EV 只含总市值与所列示科目，与一般
         企业口径不可比——金融行业应由 filter_list 排除，或明知而接受。
    选股因子案例：('z_盈利收益率EV_zh', False, '全年', 1)
    过滤因子案例：('z_盈利收益率EV_zh', '全年', 'pct:<=0.8', False)
    """
    col_name = kwargs['col_name']
    if param not in _PROFIT_COLS:
        raise ValueError(f"param 仅接受 '全年' 或 '单季'，收到 {param!r}")

    # 未列示科目记 0；资产负债表缺失或 EV ≤ 0 记 NaN
    ev = df['总市值'] + df[_EV_ADDENDS].fillna(0).sum(axis=1) - df[_EV_CASH].fillna(0)
    ev = ev.where(df[_EV_ANCHOR].notna() & (ev > 0))

    return pd.DataFrame({col_name: df[_PROFIT_COLS[param]] / ev}, index=df.index)
