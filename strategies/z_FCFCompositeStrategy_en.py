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
    Multi-factor extension of the Cash Flow Stock Selection Strategy: it keeps every behavior of FCFFEV + 一级行业
    + industry quota and adds rank-weighted auxiliary factors.
    With only FCFFEV and 一级行业 in factor_list it behaves as the official 现金流选股策略; the quota rules are the
    same, the one difference being that the intra-industry rank uses the composite rather than FCFFEV itself.

    factor_list rules:
        - FCFFEV and 一级行业 are mandatory;
        - args of 一级行业 controls industry neutralization of the core factor: 'original' off, 'neutralized' on;
        - a list or tuple as the args of FCFFEV enables the industry quota: industries are ranked by mean FCFFEV
          within each, the i-th industry keeps the top quota[i] stocks by intra-industry composite rank, and
          select_num is set to the quota sum; any other args disables it;
        - every other factor is an auxiliary ranking factor whose args is its weight (1 equal to FCFFEV, 0.5 half).
    Composite = FCFFEV Rank + Σ(Auxiliary Rank × Weight), smaller is better; each rank follows its own ascending flag.

    Known limits: ranks use method='min', so stocks tied on the composite enter the quota and select_num together
    and the holding count can exceed the configured value — the same rule as the host's select_by_factor. Industry
    neutralization takes '综合' as the base industry and raises when the panel lacks it, which can occur in short
    backtests or under tight filters.

    Use Case-1: pure FCFFEV, weekly; Use Case-2: FCFFEV industry quota [3, 2, 1] with z_MomentumVolatility_en and
    z_TrendPurity_en, 3-day holding, intraday 09:50 rebalance (requires minute-level close data), 6 stocks in total.
    """,
    'Use Case-1':
        {
            'name': 'z_FCFCompositeStrategy_en',
            'hold_period': 'W',
            'offset_list': [0, 1, 2, 3, 4],
            'select_num': 5,
            'cap_weight': 1,
            'rebalance_time': 'open',
            'factor_list': [('FCFFEV', False, 'ttm', 1),
                            ('一级行业', False, '', 'original'),
                            ],
            'filter_list': [('FCFF_TTM大于0', 3 * 250, 'val:==1', False),
                            ('一级行业过滤', ['银行', '非银金融', '房地产'], 'val:==0', False),
                            ],
        },
    'Use Case-2':
        {
            'name': 'z_FCFCompositeStrategy_en',
            'hold_period': '3D',
            'offset_list': [0, 1, 2],
            'select_num': 6,
            'cap_weight': 1,
            'rebalance_time': '0950-0950',
            'factor_list': [('FCFFEV', False, 'ttm', [3, 2, 1]),
                            ('一级行业', False, '', 'original'),
                            ('z_MomentumVolatility_en', False, 20, 1),
                            ('z_TrendPurity_en', False, 20, 1),
                            ],
            'filter_list': [('FCFF_TTM大于0', 3 * 250, 'val:==1', False),
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
        # factor_neutralization drops the '综合' dummy as the base industry and raises KeyError when the panel
        # lacks it; fail first with a readable message
        if not ((df[ind.col_name] == '综合') & df[core_col].notna()).any():
            raise ValueError(
                "neutralization uses '综合' as the base industry; the panel has no valid core value for it"
            )
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
