"""
Stock Quant Strategy Framework
---------------------------------------------------
Author:    Xinhao Zheng
Contact:   Veritas428 (WeChat)
Copyright: (c) 2026 Xinhao Zheng. Licensed under the MIT License.
---------------------------------------------------
"""
import pandas as pd

# EV addends; cash is the subtrahend; total assets only anchors whether a balance sheet exists
_EV_ADDENDS = [
    'B_st_borrow@xbx', 'B_lt_loan@xbx', 'B_bond_payable@xbx',
    'B_lease_libilities@xbx', 'B_minority_equity@xbx', 'B_preferred_shares@xbx',
]
_EV_CASH = 'B_currency_fund@xbx'
_EV_ANCHOR = 'B_total_assets@xbx'

fin_cols = [*_EV_ADDENDS, _EV_CASH, _EV_ANCHOR]
extra_data = {'dividend-delivery': ['分红率_最近日']}


def add_factor(df: pd.DataFrame, param=None, **kwargs) -> pd.DataFrame:
    """
    Compute the factor and return it as a single-column DataFrame.

    :param df: Daily K-line of one stock, ascending by trade date; columns declared in fin_cols / extra_data
        are merged in by the host.
    :param param: Factor parameter; see below.
    :param kwargs: col_name — the output column name.
    :return: pd.DataFrame with the single column col_name, on the index and length of df. The function does
        not modify df.

    Dividend Value Factor
    ---------------------------------------------------
    Meaning: The dividend analog of FCFFEV — dividend per unit of enterprise value.
    Principle: Current Dividend Yield × (Market Cap / EV). Market Cap / EV is the capital-structure
         correction: below 1 for a leveraged firm, which is discounted; above 1 for a net-cash firm. A large
         value ⇔ a high dividend at a low whole-firm price. Dividend stability is enforced by filters
         (z_ConsecutiveDividendYears_en, z_DividendQuality_en), not discounted inside the factor.
    Formula: 分红率_最近日 × (Market Cap / EV)
      分红率_最近日 = TTM Dividend per Share / Daily Close (refreshed daily by the host's data_bridge)
      EV = Market Cap + Short-Term Borrowings + Long-Term Loans + Bonds Payable + Lease Liabilities
           + Minority Interest + Preferred Stock − Cash
    param: None (pass '')
    Sorting: False (larger is better)
    Boundary: A line item unlisted in the statement is 0 — unlisted means zero, not missing. NaN when Market
         Cap is missing, the balance sheet is missing (Total Assets empty), or EV ≤ 0. Bank and insurer
         statement formats carry no borrowing or cash items, so their EV holds only market cap and the items
         they do list, and is not comparable with non-financials — exclude financials via filter_list, or
         accept that knowingly.
    Selection Case: ('z_DividendValue_en', False, '', 1)
    Filter Case:    ('z_DividendValue_en', '', 'pct:<=0.5', False)
    """
    col_name = kwargs['col_name']

    # Unlisted items are 0; a missing balance sheet or EV ≤ 0 is NaN
    ev = df['总市值'] + df[_EV_ADDENDS].fillna(0).sum(axis=1) - df[_EV_CASH].fillna(0)
    ev = ev.where(df[_EV_ANCHOR].notna() & (ev > 0))

    return pd.DataFrame({col_name: df['分红率_最近日'] * df['总市值'] / ev}, index=df.index)
