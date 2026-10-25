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
        raise ValueError('BMAC exchange info must be a nonempty DataFrame')
    labels = snapshot[['symbol', 'contract_type']].copy()
    labels['symbol'] = labels['symbol'].str.replace('-', '', regex=False)
    if labels['symbol'].isna().any() or labels['symbol'].eq('').any():
        raise ValueError('BMAC exchange info contains missing symbols')
    return labels.set_index('symbol', verify_integrity=True)['contract_type']


def signal_multi_params(df: pd.DataFrame, param_list) -> dict:
    """
    Compute the factor and return one Series per param.

    :param df: K-line of one symbol; requires the symbol column.
    :param param_list: Sequence of 'crypto' or 'tradfi'; no default.
    :return: dict[param, pd.Series], preserving df's index and length without modifying df.

    Asset Universe Factor
    ---------------------------------------------------
    Meaning: Asset-class membership before cross-sectional ranking.
    Principle: Other classes are NaN, not 0; the host drops NaN first, then ranks within the class.
    Formula: 1 if contract_type(symbol) matches param; NaN otherwise.
    param: 'crypto' → PERPETUAL; 'tradfi' → TRADIFI_PERPETUAL.
    Sorting: Not applicable; use a value filter.
    Boundary: Reads the host's BMAC snapshot, falling back to config.bmac_exginfo_path on read failure.
         Modification time and size refresh the memory cache. No network access or file writes.
         New symbols follow their type; unknown symbols/types remain NaN. Missing columns or invalid metadata
         raise. Current classifications label every row, including a reused symbol's earlier lifecycles.
    Filter Case: ('z_AssetUniverse_en', 'crypto', 'val:==1', True)
    """
    for param in param_list:
        if not isinstance(param, str) or param not in _CONTRACT_TYPES:
            raise ValueError(f"param must be 'crypto' or 'tradfi', got {param!r}")
    types = df['symbol'].str.replace('-', '', regex=False).map(_contract_types())
    return {param: pd.Series(1.0, index=df.index).where(types.eq(_CONTRACT_TYPES[param]))
            for param in param_list}


def signal(*args):
    """Legacy single-parameter interface: assign df[factor_name] and return df."""
    df, param, factor_name = args[:3]
    df[factor_name] = signal_multi_params(df, [param])[param]
    return df
