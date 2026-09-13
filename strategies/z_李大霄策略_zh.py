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
    依据李大霄公开表述归纳的选股约束——非其本人参与，不构成投资建议。在 z_红利价值策略_zh 的模板上收紧为
    「经现金流验证的高股息 + 低估值 + 大市值」的多因子价值策略，沿用「核心因子 A：X / 价格；验证因子 B：验证 X」骨架。

    表述 → 因子 / 过滤 的映射：
        - 好股给股东真实的现金回报，且高分红只有好公司撑得住
          → 核心因子 z_红利安全边际_zh（当前股息率 × FCF覆盖度）：自由现金流为负的高股息自动归零；
        - 物超所值、最低估的优质蓝筹
          → 辅助因子 z_盈利收益率EV_zh（净利润 / EV，以 EV 而非市值为分母）；
        - 大蓝筹、核心资产，不排除银行
          → 辅助因子 市值（越大越优，半权）；不加 一级行业过滤；
        - 远离小、新、差、题材、伪成长五类
          → 全部进入 filter_list 作硬边界；
        - 少交易
          → hold_period 取月频 'M'。
        股债性价比属择时维度，对横截面选股无区分度，不设该因子。

    factor_list 解析规则：
        - 核心因子（第一个非 一级行业 的项）与 一级行业 必选；推荐核心因子 z_红利安全边际_zh，可换回 z_红利价值_zh；
        - 一级行业 的 args 控制核心因子是否行业中性化：'original' 不做，'neutralized' 做——避免红利股集中于单一行业；
        - 核心因子的 args 为列表或元组时启用行业配额：先按行业内核心因子均值给行业排名，第 i 名行业保留
          复合因子行业内排名前 quota[i] 的股票，select_num 置为配额之和；不为列表或元组时不启用；
        - 其余因子为辅助排名因子，args 为权重（1 与核心因子等权，0.5 半权）。
    复合因子 = 核心因子排名 + Σ(辅助因子排名 × 权重)，越小越优；排名方向取各因子的 ascending 位。

    建议的 filter_list（小 → 新 → 差 → 伪成长 → 题材 → 质量门槛）：
        ('市值', '', 'pct:>=0.3', True)                ① 小：剔除市值最小的 30%
        ('上市至今交易天数', '', 'val:>=750', False)    ② 新：上市不足约 3 年者出局
        ('z_连续分红年份_zh', '', 'val:>=3', False)     ③ 差：连续分红不足 3 年者出局
        ('EP', '全年', 'val:>0', False)                ④ 伪成长：TTM 净利润为负者出局
        ('换手率', 20, 'pct:<=0.8', True)              ⑤ 题材：剔除 20 日换手率最高的 20%
        ('z_分红质量_zh', 1, 'pct:<=0.5', False)       ⑥ 分红高且稳，位于全市场前一半
        ('一级行业过滤', ['银行', '非银金融', '房地产'], 'val:==0', False)   可选，默认关闭

    已知限制：银行、保险的报表格式不含借款与货币资金科目，z_盈利收益率EV_zh 对其只含总市值与所列示科目，与一般
    企业口径不可比——保留银行即接受该口径；要严格 EV 口径，启用上述 一级行业过滤。

    用例-1：经现金流验证的高股息，月频；用例-2：行业配额 [3, 3, 2, 2] 叠加行业中性化；用例-3：核心因子换回
    z_红利价值_zh，验证因子 z_FCF覆盖度_zh。
    """,
    '使用案例-1':
        {
            'name': 'z_李大霄策略_zh',
            'hold_period': 'M',
            'offset_list': [0],
            'select_num': 10,
            'cap_weight': 1,
            'rebalance_time': 'open',
            'factor_list': [('z_红利安全边际_zh', False, 3, 1),
                            ('一级行业', False, '', 'original'),
                            ('z_盈利收益率EV_zh', False, '全年', 1),
                            ('市值', False, '', 0.5),
                            ],
            'filter_list': [('市值', '', 'pct:>=0.3', True),
                            ('上市至今交易天数', '', 'val:>=750', False),
                            ('z_连续分红年份_zh', '', 'val:>=3', False),
                            ('EP', '全年', 'val:>0', False),
                            ('换手率', 20, 'pct:<=0.8', True),
                            ('z_分红质量_zh', 1, 'pct:<=0.5', False),
                            ],
        },
    '使用案例-2':
        {
            'name': 'z_李大霄策略_zh',
            'hold_period': 'M',
            'offset_list': [0],
            'select_num': 10,
            'cap_weight': 1,
            'rebalance_time': 'open',
            'factor_list': [('z_红利安全边际_zh', False, 3, [3, 3, 2, 2]),
                            ('一级行业', False, '', 'neutralized'),
                            ('z_盈利收益率EV_zh', False, '全年', 1),
                            ('市值', False, '', 0.5),
                            ],
            'filter_list': [('市值', '', 'pct:>=0.3', True),
                            ('上市至今交易天数', '', 'val:>=750', False),
                            ('z_连续分红年份_zh', '', 'val:>=3', False),
                            ('EP', '全年', 'val:>0', False),
                            ('换手率', 20, 'pct:<=0.8', True),
                            ('z_分红质量_zh', 1, 'pct:<=0.5', False),
                            ],
        },
    '使用案例-3':
        {
            'name': 'z_李大霄策略_zh',
            'hold_period': 'M',
            'offset_list': [0],
            'select_num': 10,
            'cap_weight': 1,
            'rebalance_time': 'open',
            'factor_list': [('z_红利价值_zh', False, '', 1),
                            ('一级行业', False, '', 'original'),
                            ('z_FCF覆盖度_zh', False, '', 1),
                            ('市值', False, '', 0.5),
                            ],
            'filter_list': [('市值', '', 'pct:>=0.3', True),
                            ('上市至今交易天数', '', 'val:>=750', False),
                            ('z_连续分红年份_zh', '', 'val:>=3', False),
                            ('EP', '全年', 'val:>0', False),
                            ('换手率', 20, 'pct:<=0.8', True),
                            ('z_分红质量_zh', 1, 'pct:<=0.5', False),
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
