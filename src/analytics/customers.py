"""Customer summary, RFM scoring and cohort retention.

RFM (heuristic, NOT an industry standard):
  Recency  = days from last qualifying purchase to analysis_date (lower = better)
  Frequency= distinct qualifying invoices
  Monetary = sum of line_value on qualifying sale lines
Scores 1-5 from percentile rank (rank 'first' breaks ties deterministically).
Recency score is inverted so the most recent customers score 5.
"""
import numpy as np
import pandas as pd


def qualifying(df: pd.DataFrame) -> pd.DataFrame:
    return df[(df.line_type == "sale") & df.has_customer]


def customer_summary(df: pd.DataFrame, analysis_date=None) -> pd.DataFrame:
    q = qualifying(df)
    if analysis_date is None:
        analysis_date = df.invoice_day.max() + pd.Timedelta(days=1)
    analysis_date = pd.Timestamp(analysis_date)
    g = q.groupby("customer_id")
    s = g.agg(first_purchase=("invoice_date", "min"), last_purchase=("invoice_date", "max"),
              frequency=("invoice_no", "nunique"), monetary=("line_value", "sum")).reset_index()
    s["recency_days"] = (analysis_date - s.last_purchase.dt.normalize()).dt.days
    s["is_repeat"] = s.frequency >= 2
    s["cohort_month"] = s.first_purchase.dt.to_period("M").astype(str)
    return s


def _score(series: pd.Series, higher_is_better: bool) -> pd.Series:
    pct = series.rank(method="first", pct=True)
    sc = np.ceil(pct * 5).clip(1, 5).astype(int)
    return sc if higher_is_better else 6 - sc


def segment_label(r: int, f: int) -> str:
    if r >= 4 and f >= 4: return "Champions"
    if r >= 3 and f >= 4: return "Loyal Customers"
    if r >= 4 and f <= 2: return "Recent Customers"
    if r >= 3 and f >= 2: return "Potential Loyalists"
    if r <= 2 and f >= 3: return "At-Risk Customers"
    if r <= 2 and f <= 2: return "Hibernating Customers"
    return "Other Customers"


def rfm(summary: pd.DataFrame) -> pd.DataFrame:
    out = summary.copy()
    out["r_score"] = _score(out.recency_days, higher_is_better=False)
    out["f_score"] = _score(out.frequency, higher_is_better=True)
    out["m_score"] = _score(out.monetary, higher_is_better=True)
    out["segment"] = [segment_label(r, f) for r, f in zip(out.r_score, out.f_score)]
    return out


def cohort_retention(df: pd.DataFrame):
    """Returns (counts, pct). Denominator = customers whose first purchase is in the
    cohort month (month 0 = 100%). A customer is 'active' in month k if they have >=1
    qualifying sale invoice in that calendar month. Duplicated rows cannot inflate
    counts because activity is measured as distinct customers per cohort/month."""
    q = qualifying(df)
    first = q.groupby("customer_id").invoice_date.min().dt.to_period("M")
    act = q.assign(m=q.invoice_date.dt.to_period("M"))[["customer_id", "m"]].drop_duplicates()
    act["cohort"] = act.customer_id.map(first)
    act["age"] = (act.m.dt.year - act.cohort.dt.year) * 12 + (act.m.dt.month - act.cohort.dt.month)
    counts = act.pivot_table(index="cohort", columns="age", values="customer_id",
                             aggfunc="nunique", fill_value=0)
    counts.index = counts.index.astype(str)
    pct = counts.div(counts[0], axis=0) * 100
    # Cells beyond the observed data window are unknown, not 0% -> NaN
    last = act.m.max()
    for cohort in pct.index:
        max_age = (last.year - pd.Period(cohort).year) * 12 + (last.month - pd.Period(cohort).month)
        pct.loc[cohort, [a for a in pct.columns if a > max_age]] = np.nan
    return counts, pct.round(2)
