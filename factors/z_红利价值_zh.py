"""
Stock Quant Strategy Framework
---------------------------------------------------
Author:    Xinhao Zheng
Contact:   Veritas428 (WeChat)
Copyright: (c) 2026 Xinhao Zheng. Licensed under the MIT License.
---------------------------------------------------
"""
import pandas as pd

# 企业价值的加项科目；货币资金为减项；总资产只用作资产负债表是否存在的锚点，不参与计算
_EV_ADDENDS = [
    'B_st_borrow@xbx', 'B_lt_loan@xbx', 'B_bond_payable@xbx',
    'B_lease_libilities@xbx', 'B_minority_equity@xbx', 'B_preferred_shares@xbx',
]
_EV_CASH = 'B_currency_fund@xbx'
_EV_ANCHOR = 'B_total_assets@xbx'

fin_cols = [*_EV_ADDENDS, _EV_CASH, _EV_ANCHOR]
extra_data = {'dividend-delivery': ['分红率_最近日']}


def add_factor(df: pd.DataFrame, param=None, **kwargs) -> pd.DataFrame:
    """
    计算因子，以单列 DataFrame 返回。

    :param df: 单只股票的日频 K 线，按交易日期升序；fin_cols / extra_data 声明的列已由框架合并入 df。
    :param param: 因子参数，含义见下。
    :param kwargs: col_name —— 输出列名。
    :return: pd.DataFrame，仅含 col_name 一列，与 df 同索引、同长度。本函数不修改 df。

    红利价值因子
    ---------------------------------------------------
    含义：红利口径的 FCFFEV——每单位企业价值对应的股息。
    原理：当前股息率 × (总市值 / EV)。总市值 / EV 是资本结构修正：高杠杆公司该比值 < 1，被折价；净现金公司
         该比值 > 1。因子值大 ⇔ 股息高且整家公司的标价低。分红的稳定性由过滤条件（z_连续分红年份_zh、
         z_分红质量_zh）保障，不在因子内折价。
    公式：分红率_最近日 × (总市值 / EV)
      分红率_最近日 = 近一年分红 / 当日收盘价（框架 data_bridge 逐日更新）
      EV = 总市值 + 短期借款 + 长期借款 + 应付债券 + 租赁负债 + 少数股东权益 + 优先股 − 货币资金
    param: 无（传 ''）
    排序：False（值越大越优）
    边界：报表未列示的科目记 0——未列示即为零，非缺失；总市值缺失、资产负债表缺失（总资产为空）或 EV ≤ 0 时
         为 NaN。银行、保险的报表格式不含借款与货币资金科目，其 EV 只含总市值与所列示科目，与一般企业口径不可比
         ——金融行业应由 filter_list 排除，或明知而接受。
    选股因子案例：('z_红利价值_zh', False, '', 1)
    过滤因子案例：('z_红利价值_zh', '', 'pct:<=0.5', False)
    """
    col_name = kwargs['col_name']

    # 未列示科目记 0；资产负债表缺失或 EV ≤ 0 记 NaN
    ev = df['总市值'] + df[_EV_ADDENDS].fillna(0).sum(axis=1) - df[_EV_CASH].fillna(0)
    ev = ev.where(df[_EV_ANCHOR].notna() & (ev > 0))

    return pd.DataFrame({col_name: df['分红率_最近日'] * df['总市值'] / ev}, index=df.index)
