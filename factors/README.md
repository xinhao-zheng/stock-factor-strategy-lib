# factors/

A factor maps one stock's history to a single column — the score downstream ranking and filtering consume. Factors are independent: add a file and the host discovers it by filename, with no registry to update and no base class to inherit.
因子把单只股票的历史映射为一列——供下游排序与过滤使用的分值。因子彼此独立：新增一个文件，宿主即按文件名发现它，无需更新注册表，也无需继承基类。

Each ships in two editions of identical computation — `z_EnglishName_en.py` and `z_中文名_zh.py`: the same logic documented twice, not two implementations.
每个因子提供计算完全相同的两个版本——`z_EnglishName_en.py` 与 `z_中文名_zh.py`：同一逻辑的双语文档，而非两套实现。

---

## Interface | 接口

```python
import pandas as pd

fin_cols = []        # financial columns the factor needs
extra_data = {}      # other declared inputs, e.g. dividend fields

def add_factor(df: pd.DataFrame, param=None, **kwargs) -> pd.DataFrame:
    col_name = kwargs['col_name']
    factor = df['收盘价'].pct_change(param)
    return pd.DataFrame({col_name: factor}, index=df.index)
```

- **Input** — `df`: one stock's K-line plus any columns named in `fin_cols` / `extra_data`. `param`: the factor's single setting — a window, a tuple, or a mode string. `col_name`: the output name, passed through `kwargs`.
- **Output** — a one-column DataFrame on `df`'s index; the module writes nothing else and keeps no state.
- **Missing data** — read only what is declared; when an input is absent, return `NaN`, never a substitute. A line item unlisted in a filed statement is zero, not missing; the statement itself absent is missing.
- **输入** —— `df`：单只股票的 K 线，加上 `fin_cols` / `extra_data` 声明的列。`param`：因子唯一参数——窗口、元组或模式字符串。`col_name`：输出列名，经 `kwargs` 传入。
- **输出** —— 与 `df` 同索引的单列 DataFrame；模块不写其他内容、不保留状态。
- **缺失数据** —— 只读声明的列；输入缺失时返回 `NaN`，绝不填充替代值。已披露报表中未列示的科目为零，不是缺失；报表本身不存在才是缺失。

---

## Conventions | 约定

- One parameter per factor; pack compound settings into a tuple, e.g. `(short, long)`.
- Vectorize over `df` — no per-row loops, so the factor applies across the universe at scale.
- Sort direction, and whether a factor ranks or filters, is the calling strategy's decision, not the factor's.
- 每个因子一个参数；复合设置打包成元组，如 `(short, long)`。
- 对 `df` 向量化——不写逐行循环，使因子可在全市场规模应用。
- 排序方向、以及作排序还是过滤，由调用的策略决定，而非因子自身。

A file's docstring is its specification: meaning, formula, parameter, direction.
文件的 docstring 即其规格：含义、公式、参数、方向。
