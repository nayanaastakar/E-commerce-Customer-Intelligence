"""Independent pure-Python recomputation (no pandas groupby) of key KPIs, used to
cross-check the pandas implementation. Same function can be compared against
MySQL results once a database is available."""
from collections import defaultdict


def independent_kpis(rows):
    """rows: iterable of dicts or DataFrame with line_type, has_customer, customer_id, invoice_no,
    quantity, unit_price."""
    gross = returns = 0.0
    invoices = set()
    cust_invoices = defaultdict(set)
    if hasattr(rows, "itertuples"):
        for r in rows.itertuples(index=False):
            val = r.quantity * r.unit_price
            if r.line_type == "sale":
                gross += val
                invoices.add(r.invoice_no)
                if r.has_customer:
                    cust_invoices[r.customer_id].add(r.invoice_no)
            elif r.line_type == "cancellation":
                returns += abs(val)
    else:
        for r in rows:
            val = r["quantity"] * r["unit_price"]
            if r["line_type"] == "sale":
                gross += val
                invoices.add(r["invoice_no"])
                if r["has_customer"]:
                    cust_invoices[r["customer_id"]].add(r["invoice_no"])
            elif r["line_type"] == "cancellation":
                returns += abs(val)
    n_c = len(cust_invoices)
    rep = sum(1 for v in cust_invoices.values() if len(v) >= 2)
    return {"sales_invoices": len(invoices), "customers": n_c,
            "gross_sales": round(gross, 2), "returns": round(returns, 2),
            "net_sales": round(gross - returns, 2),
            "avg_invoice_value": round(gross / len(invoices), 2) if invoices else 0.0,
            "repeat_customers": rep,
            "repeat_purchase_rate": round(rep / n_c, 4) if n_c else 0.0}


def compare(a: dict, b: dict, tol=0.01):
    diffs = {k: (a[k], b[k]) for k in a if abs(a[k] - b[k]) > tol}
    return diffs
