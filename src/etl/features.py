"""Feature engineering. line_value = quantity * unit_price (signed).

  gross_sales = sum(line_value)          where line_type == 'sale'
  returns     = sum(abs(line_value))     where line_type == 'cancellation'
  net_sales   = gross_sales - returns
Cancellations are NOT matched to original invoices (no link in the data), so
net sales is a period-level approximation.
"""
import pandas as pd


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["line_value"] = out["quantity"] * out["unit_price"]
    out["invoice_day"] = out["invoice_date"].dt.normalize()
    out["year"] = out["invoice_date"].dt.year
    out["month"] = out["invoice_date"].dt.month
    out["year_month"] = out["invoice_date"].dt.to_period("M").astype(str)
    return out
