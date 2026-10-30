"""Business KPIs. All customer analytics use line_type=='sale' AND has_customer."""
import pandas as pd


def kpis(df: pd.DataFrame) -> dict:
    sales = df[df.line_type == "sale"]
    canc = df[df.line_type == "cancellation"]
    gross = float(sales.line_value.sum())
    returns = float(canc.line_value.abs().sum())
    n_inv = int(sales.invoice_no.nunique())
    cust_sales = sales[sales.has_customer]
    per_cust = cust_sales.groupby("customer_id").invoice_no.nunique()
    repeat = int((per_cust >= 2).sum())
    return {
        "sales_invoices": n_inv,
        "customers": int(per_cust.size),
        "gross_sales": round(gross, 2),
        "returns": round(returns, 2),
        "net_sales": round(gross - returns, 2),
        "avg_invoice_value": round(gross / n_inv, 2) if n_inv else 0.0,
        "repeat_customers": repeat,
        "repeat_purchase_rate": round(repeat / per_cust.size, 4) if per_cust.size else 0.0,
    }


def monthly_sales(df: pd.DataFrame) -> pd.DataFrame:
    s = df[df.line_type == "sale"]
    c = df[df.line_type == "cancellation"]
    m = s.groupby("year_month").agg(gross_sales=("line_value", "sum"),
                                    invoices=("invoice_no", "nunique"),
                                    customers=("customer_id", "nunique"))
    m["returns"] = c.assign(v=c.line_value.abs()).groupby("year_month").v.sum()
    m = m.fillna({"returns": 0.0})
    m["net_sales"] = m.gross_sales - m.returns
    m["mom_growth_pct"] = m.net_sales.pct_change() * 100
    m["rolling_3m_net_sales"] = m.net_sales.rolling(3).mean()
    return m.reset_index()
