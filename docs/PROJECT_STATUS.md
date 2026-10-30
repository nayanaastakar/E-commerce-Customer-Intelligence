# Project Status (Updated 2026-10-31)

## Environment & Infrastructure (Verified)
- **Host**: Windows 11 with Python 3.11.9.
- **Database**: MySQL 8.0 server active and connected on `localhost:3306`.
- **Dataset**: Real Online Retail dataset (541,909 rows) downloaded and verified.
- **Test Suite**: 29 unit tests passing (100% pass rate).

---

## Status by Item

| Item | Status | Evidence |
|---|---|---|
| **Real dataset acquired** | **Verified** | `data/raw/Online Retail.csv` (541,909 rows) via `scripts/download_data.py` |
| **Loader / schema validation** | **Verified** | 5 unit tests pass; loaded real dataset without schema error |
| **Cleaning & deduplication** | **Verified** | 5,268 exact duplicates removed; 536,641 clean rows; 0 rejected |
| **Features & KPIs** | **Verified** | Gross: £10.64M, Returns: £893.98K, Net: £9.75M, 19,960 invoices |
| **RFM & Cohort Retention** | **Verified** | 4,338 customers scored into 7 RFM segments; 13-month cohort retention matrix |
| **Python vs Independent KPI Reconciliation** | **Verified** | Reconciled with 0 tolerance (`reconciliation: python-vs-independent PASSED`) |
| **Pipeline End-to-End & Idempotency** | **Verified** | Run end-to-end; verified idempotent overwrites; all exports generated |
| **MySQL Star Schema & Transformations** | **Verified** | Created 6 tables; loaded 536,641 rows into `stg_transactions` and transformed to `fact_transaction_line` |
| **MySQL Loader (`src/database/load.py`)** | **Verified** | Full transactional load executed; verified exact 536,641 fact rows |
| **SQL Analytics & Python Reconciliation** | **Verified** | `scripts/reconcile_sql.py` executed: 100% KPI match between SQL views and Python |
| **EDA Visualizations** | **Verified** | `reports/figures/` generated: `monthly_sales_trend.png`, `rfm_segment_distribution.png`, `cohort_retention_heatmap.png` |
| **Reports & Audit Documentation** | **Verified** | Generated `reports/executive_summary.md`, `reports/sql_reconciliation_report.json`, `data/processed/data_quality_report.json` |

---

## Issues Resolved During Execution
1. **UCI Dataset Download & Fast CSV Conversion**: Integrated streaming Excel to CSV conversion into `scripts/download_data.py` to avoid memory bloat and speed up subsequent loads by 50x.
2. **MemoryError in Pure-Python Reconciliation**: Fixed `src/validation/reconcile.py` and `src/pipeline.py` by replacing `df.to_dict("records")` (which allocated 536k dicts) with streaming `itertuples(index=False)`.
3. **Database URL Credentials Parser**: Fixed `src/config.py` to URL-encode credentials using `urllib.parse.quote_plus`, preventing connection failures when passwords contain special characters like `@`.
4. **MySQL Reserved Word Syntax Error**: Backticked the reserved word `` `year_month` `` across `sql/schema.sql`, `sql/transformations.sql`, and `sql/sales_analysis.sql`.
5. **Schema Initialization Automation**: Added `ensure_schema()` in `src/database/load.py` and created `scripts/init_schema.py` for turnkey setup.
6. **SQL Analytical Script Validation**: Fixed unquoted column reference in `sql/sales_analysis.sql` query 2; all SQL analytics now execute cleanly on MySQL 8.0.
