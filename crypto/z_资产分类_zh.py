"""
Crypto Quant Strategy Framework
---------------------------------------------------
Author:    Xinhao Zheng
Contact:   Veritas428 (WeChat)
Copyright: (c) 2026 Xinhao Zheng. Licensed under the MIT License.
---------------------------------------------------
"""
from functools import lru_cache
from pathlib import Path

import pandas as pd

_CONTRACT_TYPES = {'crypto': 'PERPETUAL', 'tradfi': 'TRADIFI_PERPETUAL'}
_LOCAL_PATH = Path(__file__).resolve().parents[1] / 'data' / 'cache' / 'exginfo_swap.pkl'


@lru_cache(maxsize=2)
def _read_snapshot(path, mtime_ns, size):
    return pd.read_pickle(path)


def _contract_types():
    try:
        stat = _LOCAL_PATH.stat()
        snapshot = _read_snapshot(str(_LOCAL_PATH), stat.st_mtime_ns, stat.st_size)
    except Exception:
        from config import bmac_exginfo_path

        path = Path(bmac_exginfo_path) / 'exginfo_swap.pkl'
        stat = path.stat()
        snapshot = _read_snapshot(str(path), stat.st_mtime_ns, stat.st_size)

    if not isinstance(snapshot, pd.DataFrame) or snapshot.empty:
        raise ValueError('BMAC 交易所信息须为非空 DataFrame')
    labels = snapshot[['symbol', 'contract_type']].copy()
    labels['symbol'] = labels['symbol'].str.replace('-', '', regex=False)
    if labels['symbol'].isna().any() or labels['symbol'].eq('').any():
        raise ValueError('BMAC 交易所信息含缺失的 symbol')
    return labels.set_index('symbol', verify_integrity=True)['contract_type']


def signal_multi_params(df: pd.DataFrame, param_list) -> dict:
    """
    计算因子，每个参数返回一列 Series。

    :param df: 单个标的的 K 线，须包含 symbol 列。
    :param param_list: 'crypto' 或 'tradfi' 的序列，无默认值。
    :return: dict[param, pd.Series]，与 df 同索引、同长度；本函数不修改 df。

    资产分类因子
    ---------------------------------------------------
    含义：截面排名前的资产类别归属。
    原理：其他类别取 NaN 而非 0；框架先剔除 NaN，再在本类内排名。
    公式：contract_type(symbol) 与 param 匹配时为 1，否则为 NaN。
    param: 'crypto' → PERPETUAL；'tradfi' → TRADIFI_PERPETUAL。
    排序：不适用，使用数值过滤。
    边界：读取框架已有的 BMAC 快照；读取失败时回退至 config.bmac_exginfo_path。
         文件修改时间与大小更新内存缓存；不联网、不写文件。
         新标的按其类型归类；未知标的或类型保持 NaN。缺列或元数据无效时报错。
         当前分类作用于全部行，包括同名标的的早期生命周期。
    过滤因子案例：('z_资产分类_zh', 'crypto', 'val:==1', True)
    """
    for param in param_list:
        if not isinstance(param, str) or param not in _CONTRACT_TYPES:
            raise ValueError(f"param 仅接受 'crypto' 或 'tradfi'，收到 {param!r}")
    types = df['symbol'].str.replace('-', '', regex=False).map(_contract_types())
    return {param: pd.Series(1.0, index=df.index).where(types.eq(_CONTRACT_TYPES[param]))
            for param in param_list}


def signal(*args):
    """旧版单参数接口：写入 df[factor_name] 并返回原 df。"""
    df, param, factor_name = args[:3]
    df[factor_name] = signal_multi_params(df, [param])[param]
    return df
