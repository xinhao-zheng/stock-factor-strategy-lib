"""
Stock Quant Strategy Framework
---------------------------------------------------
Author:    Xinhao Zheng
Contact:   Veritas428 (WeChat)
Copyright: (c) 2026 Xinhao Zheng. Licensed under the MIT License.
---------------------------------------------------
"""
import pandas as pd

from core.market_essentials import factor_neutralization
from core.model.strategy_config import StrategyConfig

STG_INTRO = {
    '策略说明': """
    红利口径的 FCFFEV 策略，沿用价值模板「因子 A：X / 价格；因子 B：验证 X」。
    - 因子 A（z_红利价值_zh）：股息 / 企业价值，回答“分红相对整家公司的标价是否便宜”；
    - 因子 B（z_FCF覆盖度_zh）：自由现金流 / 分红总额，回答“分红是否被现金流覆盖”。
    两者等权排名相加：一个管值不值得买，一个管撑不撑得住。

    factor_list 解析规则：
        - z_红利价值_zh 与 一级行业 必选；
        - 一级行业 的 args 控制核心因子是否行业中性化：'original' 不做，'neutralized' 做；
        - 核心因子的 args 为列表或元组时启用行业配额：先按行业内核心因子均值给行业排名，第 i 名行业保留
          复合因子行业内排名前 quota[i] 的股票，select_num 置为配额之和；不为列表或元组时不启用；
        - 其余因子为辅助排名因子，args 为权重（1 与核心因子等权，0.5 半权）。
    复合因子 = 核心因子排名 + Σ(辅助因子排名 × 权重)，越小越优；排名方向取各因子的 ascending 位。

    建议的 filter_list：
        ('z_连续分红年份_zh', '', 'val:>=3', False)    连续分红不少于 3 年
        ('z_分红质量_zh', 1, 'pct:<=0.5', False)       分红高且稳，位于全市场前一半
        ('一级行业过滤', ['银行', '非银金融', '房地产'], 'val:==0', False)
                                                       排除高杠杆行业——银行、保险的报表格式不含 EV 所需的借款科目

    已知限制：排名取 method='min'，复合因子同分者并列进入配额与 select_num，实际持仓数可能多于配置值，与框架
    select_by_factor 的规则一致。行业中性化以 '综合' 为基准行业，面板不含该行业时报错，短区间回测或强过滤下可能
    出现。z_连续分红年份_zh 与 z_分红质量_zh 透传框架分红桥的列，该桥按报告期开窗、不按登记日截断，特别分红与
    中期分红使排序冲突时会提前吸收尚未登记的记录（见两因子的边界段）。

    用例-1：双因子等权排名，周频；用例-2：行业配额 [3, 2, 1]，共选 6 只。
    """,
    '使用案例-1':
        {
            'name': 'z_红利价值策略_zh',
            'hold_period': 'W',
            'offset_list': [0, 1, 2, 3, 4],
            'select_num': 5,
            'cap_weight': 1,
            'rebalance_time': 'open',
            'factor_list': [('z_红利价值_zh', False, '', 1),
                            ('一级行业', False, '', 'original'),
                            ('z_FCF覆盖度_zh', False, '', 1),
                            ],
            'filter_list': [('z_连续分红年份_zh', '', 'val:>=3', False),
                            ('z_分红质量_zh', 1, 'pct:<=0.5', False),
                            ('一级行业过滤', ['银行', '非银金融', '房地产'], 'val:==0', False),
                            ],
        },
    '使用案例-2':
        {
            'name': 'z_红利价值策略_zh',
            'hold_period': 'W',
            'offset_list': [0, 1, 2, 3, 4],
            'select_num': 6,
            'cap_weight': 1,
            'rebalance_time': 'open',
            'factor_list': [('z_红利价值_zh', False, '', [3, 2, 1]),
                            ('一级行业', False, '', 'original'),
                            ('z_FCF覆盖度_zh', False, '', 1),
                            ],
            'filter_list': [('z_连续分红年份_zh', '', 'val:>=3', False),
                            ('z_分红质量_zh', 1, 'pct:<=0.5', False),
                            ('一级行业过滤', ['银行', '非银金融', '房地产'], 'val:==0', False),
                            ],
        },
}


def calc_select_factor(df, strategy: StrategyConfig) -> pd.DataFrame:
    """
    计算复合选股因子，返回带 strategy.factor_name 列的 df。

    :param df: filter_before_select 之后的日频面板（多股票 × 多交易日），列为框架基础列与 strategy.factor_columns。
    :param strategy: 策略配置；读取 factor_list 与 factor_name，启用行业配额时改写 select_num。
    :return: pd.DataFrame，新增 strategy.factor_name 列，越小越优；启用行业配额时只保留配额内的行。

    factor_list 解析：名为 一级行业 的项为行业项，其 args 为 'original' 或 'neutralized'；其余第一项为核心因子，
    其 args 为行业配额（列表或元组）或占位；其后各项为辅助因子，其 args 为数值权重。
    """
    ind = next((f for f in strategy.factor_list if f.name == '一级行业'), None)
    others = [f for f in strategy.factor_list if f.name != '一级行业']
    if ind is None or not others:
        raise ValueError('factor_list 须包含 一级行业 与至少一个核心因子')
    core, aux_factors = others[0], others[1:]

    neutralized = ind.args == 'neutralized'
    quota = core.args if isinstance(core.args, (list, tuple)) else None

    # 核心因子：按需行业中性化，再按其 ascending 位在每个交易日内排名
    core_col = core.col_name
    if neutralized:
        # factor_neutralization 以 '综合' 为基准行业删除其哑变量，面板不含该行业时它抛 KeyError；先给出可读的报错
        if not ((df[ind.col_name] == '综合') & df[core_col].notna()).any():
            raise ValueError("行业中性化以 '综合' 为基准行业，当前面板无该行业的有效核心因子值")
        df = factor_neutralization(df, factor=core_col, neutralize_list=[], industry=ind.col_name)
        core_col = f'{core_col}_中性'
    by_date = df.groupby('交易日期')
    df['核心排名'] = by_date[core_col].rank(ascending=core.is_sort_asc, method='min')

    # 复合因子 = 核心排名 + Σ(辅助排名 × 权重)，越小越优
    composite = df['核心排名'].copy()
    for af in aux_factors:
        composite = composite + by_date[af.col_name].rank(ascending=af.is_sort_asc, method='min') * af.weight
    df[strategy.factor_name] = composite

    # 行业配额：按行业内核心因子均值给行业排名，第 i 名行业保留复合因子行业内排名前 quota[i] 的股票
    if quota is not None:
        strategy.select_num = sum(quota)
        industry_keys = ['交易日期', ind.col_name]
        industry_rank = (
            df.groupby(industry_keys)[core_col].mean()
            .groupby(level='交易日期').rank(ascending=core.is_sort_asc, method='min')
            .rename('行业平均排名')
        )
        df = df.join(industry_rank, on=industry_keys)
        df['行业内排名'] = df.groupby(industry_keys)[strategy.factor_name].rank(ascending=True, method='min')
        quota_by_rank = pd.Series(quota, index=range(1, len(quota) + 1), dtype='float64')
        df = df[df['行业内排名'] <= df['行业平均排名'].map(quota_by_rank)]

    return df
