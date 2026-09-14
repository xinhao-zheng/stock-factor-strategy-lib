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
    Selection constraints distilled from Li Daxiao's public statements — without his involvement, and not
    investment advice. Tightened from the z_DividendValueStrategy_en template into a multi-factor value strategy of
    "FCF-verified high dividend + low valuation + large cap", on the skeleton "Core Factor A: X / Price;
    Verification Factor B: verify X".

    Statement → factor / filter mapping:
        - A good stock pays shareholders real cash, and only a good company can sustain a high dividend
          → core factor z_DividendSafetyMargin_en (Current Dividend Yield × FCF Coverage): a high yield on
            negative free cash flow collapses to zero by construction;
        - Exceptional value, the cheapest quality blue chips
          → auxiliary z_EarningsYieldEV_en (Net Profit / EV, with EV rather than market cap as denominator);
        - Large blue chips and core assets, banks not excluded
          → auxiliary 市值 (larger is better, half weight); no 一级行业过滤;
        - Stay away from the small, the new, the bad, the thematic, and pseudo-growth
          → all enforced as hard boundaries in filter_list;
        - Trade seldom
          → hold_period monthly 'M'.
        Bond-equity relative value is a timing dimension with no cross-sectional discrimination; no such factor.

    factor_list rules:
        - the core factor (first entry not named 一级行业) and 一级行业 are mandatory; the recommended core is
          z_DividendSafetyMargin_en, z_DividendValue_en may be substituted;
        - args of 一级行业 controls industry neutralization of the core factor: 'original' off, 'neutralized' on —
          against dividend stocks concentrating in a single industry;
        - a list or tuple as the core factor's args enables the industry quota: industries are ranked by the mean
          core factor within each, the i-th industry keeps the top quota[i] stocks by intra-industry composite
          rank, and select_num is set to the quota sum; any other args disables it;
        - every other factor is an auxiliary ranking factor whose args is its weight (1 equal to the core, 0.5 half).
    Composite = Core Rank + Σ(Auxiliary Rank × Weight), smaller is better; each rank follows its own ascending flag.

    Recommended filter_list (small → new → bad → pseudo-growth → thematic → quality threshold):
        ('市值', '', 'pct:>=0.3', True)                          ① small: drop the smallest 30% by market cap
        ('上市至今交易天数', '', 'val:>=750', False)              ② new: listed less than ~3 years is out
        ('z_ConsecutiveDividendYears_en', '', 'val:>=3', False)  ③ bad: fewer than 3 consecutive dividend years is out
        ('EP', '全年', 'val:>0', False)                          ④ pseudo-growth: negative TTM net profit is out
        ('换手率', 20, 'pct:<=0.8', True)                        ⑤ thematic: drop the top 20% by 20-day turnover
        ('z_DividendQuality_en', 1, 'pct:<=0.5', False)          ⑥ dividend high and stable, top half of the market
        ('一级行业过滤', ['银行', '非银金融', '房地产'], 'val:==0', False)   optional, off by default

    Known limits: bank and insurer statement formats carry no borrowing or cash items, so for them
    z_EarningsYieldEV_en holds only market cap and the items they do list, not comparable with non-financials —
    keeping banks means accepting that basis; for a strict EV basis, enable the 一级行业过滤 above. Ranks use
    method='min', so stocks tied on the composite enter the quota and select_num together and the holding count
    can exceed the configured value — the same rule as the host's select_by_factor. Industry neutralization takes
    '综合' as the base industry and raises when the panel lacks it, which can occur in short backtests or under
    tight filters. z_ConsecutiveDividendYears_en and z_DividendQuality_en pass through the host's dividend bridge,
    which windows by report period rather than record date — when a special or interim dividend puts the two
    orders at odds, a record not yet registered is absorbed early (see both factors' boundary sections).

    Use Case-1: FCF-verified high dividend, monthly; Use Case-2: industry quota [3, 3, 2, 2] with industry
    neutralization; Use Case-3: core factor back to z_DividendValue_en, verification factor z_FCFDividendCoverage_en.
    """,
    'Use Case-1':
        {
            'name': 'z_DAXIAOLIStrategy_en',
            'hold_period': 'M',
            'offset_list': [0],
            'select_num': 10,
            'cap_weight': 1,
            'rebalance_time': 'open',
            'factor_list': [('z_DividendSafetyMargin_en', False, 3, 1),
                            ('一级行业', False, '', 'original'),
                            ('z_EarningsYieldEV_en', False, '全年', 1),
                            ('市值', False, '', 0.5),
                            ],
            'filter_list': [('市值', '', 'pct:>=0.3', True),
                            ('上市至今交易天数', '', 'val:>=750', False),
                            ('z_ConsecutiveDividendYears_en', '', 'val:>=3', False),
                            ('EP', '全年', 'val:>0', False),
                            ('换手率', 20, 'pct:<=0.8', True),
                            ('z_DividendQuality_en', 1, 'pct:<=0.5', False),
                            ],
        },
    'Use Case-2':
        {
            'name': 'z_DAXIAOLIStrategy_en',
            'hold_period': 'M',
            'offset_list': [0],
            'select_num': 10,
            'cap_weight': 1,
            'rebalance_time': 'open',
            'factor_list': [('z_DividendSafetyMargin_en', False, 3, [3, 3, 2, 2]),
                            ('一级行业', False, '', 'neutralized'),
                            ('z_EarningsYieldEV_en', False, '全年', 1),
                            ('市值', False, '', 0.5),
                            ],
            'filter_list': [('市值', '', 'pct:>=0.3', True),
                            ('上市至今交易天数', '', 'val:>=750', False),
                            ('z_ConsecutiveDividendYears_en', '', 'val:>=3', False),
                            ('EP', '全年', 'val:>0', False),
                            ('换手率', 20, 'pct:<=0.8', True),
                            ('z_DividendQuality_en', 1, 'pct:<=0.5', False),
                            ],
        },
    'Use Case-3':
        {
            'name': 'z_DAXIAOLIStrategy_en',
            'hold_period': 'M',
            'offset_list': [0],
            'select_num': 10,
            'cap_weight': 1,
            'rebalance_time': 'open',
            'factor_list': [('z_DividendValue_en', False, '', 1),
                            ('一级行业', False, '', 'original'),
                            ('z_FCFDividendCoverage_en', False, '', 1),
                            ('市值', False, '', 0.5),
                            ],
            'filter_list': [('市值', '', 'pct:>=0.3', True),
                            ('上市至今交易天数', '', 'val:>=750', False),
                            ('z_ConsecutiveDividendYears_en', '', 'val:>=3', False),
                            ('EP', '全年', 'val:>0', False),
                            ('换手率', 20, 'pct:<=0.8', True),
                            ('z_DividendQuality_en', 1, 'pct:<=0.5', False),
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
