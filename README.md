# stock-factor-strategy-lib

Plug-in factors and strategies for a stock-selection framework: a factor measures a stock, a strategy composes those measurements into a portfolio. Each is a self-contained module the host loads by filename — add a file to extend the library, take any file to reuse it.
面向选股框架的即插即用因子与策略库：因子度量个股，策略把度量组合成持仓。每个都是宿主按文件名加载的自包含模块——加一个文件即扩展，取任一文件即复用。

---

## Layout | 目录

```text
.
├── factors/          # add_factor(df, param, **kwargs) → one factor column · 一列因子值
├── strategies/       # calc_select_factor(df, strategy) + STG_INTRO → holdings · 持仓
├── requirements.txt  # pandas
└── LICENSE
```

Every module ships in two editions of identical logic — English `z_EnglishName_en.py` and Chinese `z_中文名_zh.py`. The host resolves a module by filename: the file is the identifier.
每个模块提供逻辑相同的两个版本——英文版 `z_EnglishName_en.py` 与中文版 `z_中文名_zh.py`。宿主按文件名解析模块：文件名即标识。

---

## Encoding | 编码

UTF-8, no BOM, LF line endings. · UTF-8，无 BOM，LF 换行。

---

## License | 许可

MIT (see `LICENSE`). · MIT（见 `LICENSE`）。
