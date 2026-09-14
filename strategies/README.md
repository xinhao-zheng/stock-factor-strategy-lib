# strategies/

A strategy is a configurable template that turns factor scores into a portfolio: it weights several factors into one composite ranking, then narrows the result with hard filters. The logic is fixed — factors, weights, holding period, and filters are configuration.
策略是可配置模板，把因子分值转成持仓：它将若干因子加权合成一个复合排名，再用硬过滤收窄结果。逻辑固定——因子、权重、持仓周期与过滤皆为配置。

Each ships in two editions of identical logic — `z_EnglishNameStrategy_en.py` and `z_中文名策略_zh.py`.
每个策略提供逻辑相同的两个版本——`z_EnglishNameStrategy_en.py` 与 `z_中文名策略_zh.py`。

---

## Interface | 接口

```python
import pandas as pd

STG_INTRO = {
    '策略说明': '...',                        # what it does and how to configure
    '使用案例-1': {
        'name': '...',
        'hold_period': 'W',                   # rebalance cadence
        'select_num': 5,                      # names held
        'factor_list': [(factor, ascending, param, weight), ...],
        'filter_list': [(factor, param, rule, ascending), ...],
    },
}

def calc_select_factor(df: pd.DataFrame, strategy) -> pd.DataFrame:
    # rank → weight into a composite → filter → return kept rows
    ...
```

- **`factor_list`** — `(name, ascending, param, weight)`. The first non-industry entry is the core factor; the rest are auxiliaries.
- **`filter_list`** — `(name, param, rule, ascending)`, where `rule` is a threshold such as `val:>=1` or `pct:<=0.5`.
- **Composite** — `composite = core_rank + Σ(aux_rank × weight)`, smaller is better. Ranks carry no unit, so factors on different scales combine without normalization.
- **Industry control** — a list weight on the core factor (e.g. `[3,2,1]`) imposes a per-industry quota; `neutralized` on the industry entry regresses the core factor on industry dummies and ranks the residual — the industry mean is removed, the ranking stays market-wide.
- **Ties** — ranks use `method='min'`; stocks tied on the composite share a rank and enter the quota and `select_num` together, so the holding count can exceed the configured value — the host's own selection rule.
- **`factor_list`** —— `(名称, 升序, 参数, 权重)`。第一个非行业项为核心因子，其余为辅助因子。
- **`filter_list`** —— `(名称, 参数, 规则, 升序)`，`规则` 为阈值，如 `val:>=1` 或 `pct:<=0.5`。
- **复合** —— `复合 = 核心排名 + Σ(辅助排名 × 权重)`，越小越优。排名无量纲，故不同量纲的因子无需标准化即可合成。
- **行业控制** —— 核心因子权重设为列表（如 `[3,2,1]`）即施加分行业配额；行业项设为 `neutralized` 则将核心因子对行业哑变量回归、以残差排名——剔除的是行业均值，排名仍在全市场进行。
- **并列** —— 排名取 `method='min'`；复合因子同分的股票共享名次，一同进入配额与 `select_num`，持仓数可能多于配置值——与宿主自身的选股规则一致。

A strategy composes scores the framework has already computed; it does not recompute raw signals. Each file's `STG_INTRO` is its specification.
策略组合的是框架已算好的分值，不重新计算原始信号。每个文件的 `STG_INTRO` 即其规格。
