"""Data profiling computed from the actual loaded data."""
import pandas as pd


def profile_raw(raw: pd.DataFrame) -> dict:
    qty = pd.to_numeric(raw["quantity"], errors="coerce")
    price = pd.to_numeric(raw["unit_price"], errors="coerce")
    dates = pd.to_datetime(raw["invoice_date"], errors="coerce")
    return {
        "rows": len(raw), "columns": list(raw.columns),
        "missing_by_column": raw.isna().sum().to_dict(),
        "exact_duplicate_rows": int(raw.duplicated().sum()),
        "unique_customers": int(raw["customer_id"].dropna().nunique()),
        "unique_products": int(raw["stock_code"].dropna().nunique()),
        "unique_invoices": int(raw["invoice_no"].dropna().nunique()),
        "date_min": str(dates.min()), "date_max": str(dates.max()),
        "date_parse_failures": int(dates.isna().sum()),
        "quantity_describe": qty.describe().round(3).to_dict(),
        "price_describe": price.describe().round(3).to_dict(),
        "negative_quantity_rows": int((qty < 0).sum()),
        "zero_or_negative_price_rows": int((price <= 0).sum()),
        "c_prefixed_invoices": int(raw["invoice_no"].astype("string").str.upper().str.startswith("C").sum()),
    }
