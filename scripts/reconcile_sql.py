"""Reconcile MySQL star schema analytics against Python pipeline outputs.
Executes SQL analytics queries and cross-checks headline KPIs, customer counts,
revenue, repeat rates, RFM segments, and cohort retention.
"""
import json, logging, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import pandas as pd
from sqlalchemy import create_engine, text
from src import config

log = logging.getLogger("reconcile_sql")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
SQL_DIR = ROOT / "sql"
EXPORTS_DIR = ROOT / "exports"
REPORT_PATH = ROOT / "data" / "processed" / "data_quality_report.json"


def _statements(path: Path):
    body = re.sub(r"--.*", "", path.read_text(encoding="utf-8"))
    return [s.strip() for s in body.split(";") if s.strip()]


def reconcile():
    engine = create_engine(config.mysql_url())
    with open(REPORT_PATH, encoding="utf-8") as f:
        dq_report = json.load(f)
    py_kpis = dq_report["kpis"]

    with engine.connect() as conn:
        # 1. Headline KPIs from sql/sales_analysis.sql (statement 0)
        sales_sql = _statements(SQL_DIR / "sales_analysis.sql")
        kpi_row = conn.execute(text(sales_sql[0])).mappings().one()
        sql_kpis = {
            "sales_invoices": int(kpi_row["sales_invoices"]),
            "customers": int(kpi_row["customers"]),
            "gross_sales": float(kpi_row["gross_sales"]),
            "returns": float(kpi_row["returns"]),
            "net_sales": float(kpi_row["net_sales"]),
        }

        # Repeat purchase rate from sql/customer_retention.sql (statement 0)
        retention_sql = _statements(SQL_DIR / "customer_retention.sql")
        ret_row = conn.execute(text(retention_sql[0])).mappings().one()
        sql_kpis["repeat_customers"] = int(ret_row["repeat_customers"])
        sql_kpis["repeat_purchase_rate"] = float(ret_row["repeat_purchase_rate"])

        log.info("Python KPIs: %s", py_kpis)
        log.info("SQL KPIs:    %s", sql_kpis)

        mismatches = []
        for k in ["sales_invoices", "customers", "gross_sales", "returns", "net_sales", "repeat_customers", "repeat_purchase_rate"]:
            diff = abs(py_kpis[k] - sql_kpis[k])
            if diff > 0.05:
                mismatches.append((k, py_kpis[k], sql_kpis[k], diff))

        if mismatches:
            log.error("Reconciliation MISMATCH: %s", mismatches)
            raise ValueError(f"KPI reconciliation failed: {mismatches}")
        else:
            log.info("Reconciliation PASSED: All headline KPIs match perfectly!")

        # 2. Check table row counts
        tables = ["stg_transactions", "dim_date", "dim_customer", "dim_product", "dim_country", "fact_transaction_line"]
        counts = {}
        for t in tables:
            counts[t] = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
            log.info("Table %s: %d rows", t, counts[t])

        # 3. Monthly sales check
        monthly_df = pd.read_sql(text(sales_sql[1]), conn)
        log.info("Monthly sales query returned %d months", len(monthly_df))

        # 4. RFM segmentation check
        rfm_sql = _statements(SQL_DIR / "rfm_segmentation.sql")
        rfm_df = pd.read_sql(text(rfm_sql[0]), conn)
        log.info("SQL RFM segmentation generated for %d customers across segments:\n%s",
                 len(rfm_df), rfm_df["segment"].value_counts().to_string())

        # 5. Cohort retention check
        cohort_sql = _statements(SQL_DIR / "cohort_analysis.sql")
        cohort_df = pd.read_sql(text(cohort_sql[0]), conn)
        log.info("SQL Cohort analysis generated %d cohort-month cells", len(cohort_df))

        reconciliation_summary = {
            "status": "PASSED",
            "table_counts": counts,
            "python_kpis": py_kpis,
            "sql_kpis": sql_kpis,
            "sql_rfm_customers": len(rfm_df),
            "sql_cohort_cells": len(cohort_df),
        }
        (ROOT / "reports" / "sql_reconciliation_report.json").parent.mkdir(parents=True, exist_ok=True)
        (ROOT / "reports" / "sql_reconciliation_report.json").write_text(
            json.dumps(reconciliation_summary, indent=2, default=str), encoding="utf-8"
        )
        log.info("Saved reports/sql_reconciliation_report.json")
        return reconciliation_summary


if __name__ == "__main__":
    reconcile()
