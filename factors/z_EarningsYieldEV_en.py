"""
Stock Quant Strategy Framework
---------------------------------------------------
Author:    Xinhao Zheng
Contact:   Veritas428 (WeChat)
Copyright: (c) 2026 Xinhao Zheng. Licensed under the MIT License.
---------------------------------------------------
"""
import pandas as pd

# param → net profit column
_PROFIT_COLS = {'全年': 'R_np@xbx_ttm', '单季': 'R_np@xbx_单季'}

# EV addends; cash is the subtrahend; total assets only anchors whether a balance sheet exists
_EV_ADDENDS = [
    'B_st_borrow@xbx', 'B_lt_loan@xbx', 'B_bond_payable@xbx',
    'B_lease_libilities@xbx', 'B_minority_equity@xbx', 'B_preferred_shares@xbx',
]
_EV_CASH = 'B_currency_fund@xbx'
_EV_ANCHOR = 'B_total_assets@xbx'

fin_cols = [*_PROFIT_COLS.values(), *_EV_ADDENDS, _EV_CASH, _EV_ANCHOR]
extra_data = {}


def add_factor(df: pd.DataFrame, param=None, **kwargs) -> pd.DataFrame:
    """
    Compute the factor and return it as a single-column DataFrame.

    :param df: Daily K-line of one stock, ascending by trade date; columns declared in fin_cols / extra_data
        are merged in by the host.
    :param param: Factor parameter; see below.
    :param kwargs: col_name — the output column name.
    :return: pd.DataFrame with the single column col_name, on the index and length of df. The function does
        not modify df.

    Earnings Yield EV Factor
    ---------------------------------------------------
    Meaning: EP on an enterprise-value basis — net profit divided by EV rather than market cap.
    Principle: EP = Net Profit / Market Cap takes the equity holder's view only; with EV as the denominator, a
         leveraged firm no longer looks cheap because its market cap is small, and a net-cash firm becomes
         correspondingly cheaper. A large value ⇔ a high earnings return at the whole-firm price, i.e. a low
         valuation.
    Formula: Net Profit / EV
      EV = Market Cap + Short-Term Borrowings + Long-Term Loans + Bonds Payable + Lease Liabilities
           + Minority Interest + Preferred Stock − Cash
    param: '全年' (TTM net profit) or '单季' (latest single-quarter net profit)
    Sorting: False (larger is better)
    Boundary: A line item unlisted in the statement is 0 — unlisted means zero, not missing. NaN when Net
         Profit or Market Cap is missing, the balance sheet is missing (Total Assets empty), or EV ≤ 0. Bank
         and insurer statement formats carry no borrowing or cash items, so their EV holds only market cap and
         the items they do list, and is not comparable with non-financials — exclude financials via
         filter_list, or accept that knowingly.
    Selection Case: ('z_EarningsYieldEV_en', False, '全年', 1)
    Filter Case:    ('z_EarningsYieldEV_en', '全年', 'pct:<=0.8', False)
    """
    col_name = kwargs['col_name']
    if param not in _PROFIT_COLS:
        raise ValueError(f"param accepts '全年' or '单季', got {param!r}")

    # Unlisted items are 0; a missing balance sheet or EV ≤ 0 is NaN
    ev = df['总市值'] + df[_EV_ADDENDS].fillna(0).sum(axis=1) - df[_EV_CASH].fillna(0)
    ev = ev.where(df[_EV_ANCHOR].notna() & (ev > 0))

    return pd.DataFrame({col_name: df[_PROFIT_COLS[param]] / ev}, index=df.index)
