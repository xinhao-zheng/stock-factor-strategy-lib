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
    'Strategy Description': """
    The dividend analog of the FCFFEV strategy, on the value template "Factor A: X / Price; Factor B: verify X".
    - Factor A (z_DividendValue_en): Dividend / EV — is the dividend cheap against the whole-firm price?
    - Factor B (z_FCFDividendCoverage_en): FCF / Total Dividends — is the dividend covered by cash flow?
    Their ranks are summed with equal weight: one asks whether it is worth buying, the other whether it holds.

    factor_list rules:
        - z_DividendValue_en and 一级行业 are mandatory;
        - args of 一级行业 controls industry neutralization of the core factor: 'original' off, 'neutralized' on;
        - a list or tuple as the core factor's args enables the industry quota: industries are ranked by the mean
          core factor within each, the i-th industry keeps the top quota[i] stocks by intra-industry composite
          rank, and select_num is set to the quota sum; any other args disables it;
        - every other factor is an auxiliary ranking factor whose args is its weight (1 equal to the core, 0.5 half).
    Composite = Core Rank + Σ(Auxiliary Rank × Weight), smaller is better; each rank follows its own ascending flag.

    Recommended filter_list:
        ('z_ConsecutiveDividendYears_en', '', 'val:>=3', False)   at least 3 consecutive dividend years
        ('z_DividendQuality_en', 1, 'pct:<=0.5', False)           dividend high and stable, top half of the market
        ('一级行业过滤', ['银行', '非银金融', '房地产'], 'val:==0', False)
                                                                  exclude leveraged industries — bank and insurer
                                                                  statements carry none of the borrowing items EV needs

    Use Case-1: two-factor equal-weight ranking, weekly; Use Case-2: industry quota [3, 2, 1], 6 stocks in total.
    """,
    'Use Case-1':
        {
            'name': 'z_DividendValueStrategy_en',
            'hold_period': 'W',
            'offset_list': [0, 1, 2, 3, 4],
            'select_num': 5,
            'cap_weight': 1,
            'rebalance_time': 'open',
            'factor_list': [('z_DividendValue_en', False, '', 1),
                            ('一级行业', False, '', 'original'),
                            ('z_FCFDividendCoverage_en', False, '', 1),
                            ],
            'filter_list': [('z_ConsecutiveDividendYears_en', '', 'val:>=3', False),
                            ('z_DividendQuality_en', 1, 'pct:<=0.5', False),
                            ('一级行业过滤', ['银行', '非银金融', '房地产'], 'val:==0', False),
                            ],
        },
    'Use Case-2':
        {
            'name': 'z_DividendValueStrategy_en',
            'hold_period': 'W',
            'offset_list': [0, 1, 2, 3, 4],
            'select_num': 6,
            'cap_weight': 1,
            'rebalance_time': 'open',
            'factor_list': [('z_DividendValue_en', False, '', [3, 2, 1]),
                            ('一级行业', False, '', 'original'),
                            ('z_FCFDividendCoverage_en', False, '', 1),
                            ],
            'filter_list': [('z_ConsecutiveDividendYears_en', '', 'val:>=3', False),
                            ('z_DividendQuality_en', 1, 'pct:<=0.5', False),
                            ('一级行业过滤', ['银行', '非银金融', '房地产'], 'val:==0', False),
                            ],
        },
}


def calc_select_factor(df, strategy: StrategyConfig) -> pd.DataFrame:
    """
    Compute the composite selection factor and return df with the strategy.factor_name column.

    :param df: Daily panel after filter_before_select (stocks × trade dates); host base columns plus
        strategy.factor_columns.
    :param strategy: Strategy config; reads factor_list and factor_name, and rewrites select_num when the industry
        quota is on.
    :return: pd.DataFrame with the new strategy.factor_name column, smaller is better; with the quota on, only rows
        within the quota are kept.

    factor_list parsing: the entry named 一级行业 is the industry entry, its args 'original' or 'neutralized'; the
    first remaining entry is the core factor, its args an industry quota (list or tuple) or a placeholder; every
    later entry is an auxiliary factor, its args a numeric weight.
    """
    ind = next((f for f in strategy.factor_list if f.name == '一级行业'), None)
    others = [f for f in strategy.factor_list if f.name != '一级行业']
    if ind is None or not others:
        raise ValueError('factor_list must contain 一级行业 and at least one core factor')
    core, aux_factors = others[0], others[1:]

    neutralized = ind.args == 'neutralized'
    quota = core.args if isinstance(core.args, (list, tuple)) else None

    # Core factor: neutralize by industry on demand, then rank within each trade date by its ascending flag
    core_col = core.col_name
    if neutralized:
        df = factor_neutralization(df, factor=core_col, neutralize_list=[], industry=ind.col_name)
        core_col = f'{core_col}_中性'
    by_date = df.groupby('交易日期')
    df['核心排名'] = by_date[core_col].rank(ascending=core.is_sort_asc, method='min')

    # Composite = core rank + Σ(auxiliary rank × weight), smaller is better
    composite = df['核心排名'].copy()
    for af in aux_factors:
        composite = composite + by_date[af.col_name].rank(ascending=af.is_sort_asc, method='min') * af.weight
    df[strategy.factor_name] = composite

    # Industry quota: rank industries by mean core factor; the i-th industry keeps the top quota[i] by composite rank
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
