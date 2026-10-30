# E-Commerce Customer Intelligence & Retention Analytics Platform
Python ETL → MySQL 8.0 Star Schema → SQL Analytics → Interactive Dashboard & Power BI Data Marts. **Fully verified end-to-end: see `docs/PROJECT_STATUS.md`.**

## Dataset
Online Retail (UCI machine learning repository, id 352 / Kaggle `vijayuv/onlineretail`).
- **Date Range**: 2010-12-01 to 2011-12-09
- **Raw Rows**: 541,909 records
- **Clean Transactions**: 536,641 records (5,268 exact duplicates removed, 0 structural rejections)
- **Net Sales**: £9,748,131.07 across 19,960 sales invoices and 4,338 unique customers

## Quick Start (Windows, PowerShell)
```powershell
# 1. Environment & Dependencies
python -m pip install -r requirements.txt
copy .env.example .env     # Configure MySQL credentials if not already set

# 2. Acquire Dataset
python scripts\download_data.py   # Downloads and converts UCI dataset to data\raw\

# 3. Run Ingestion, Cleaning, KPIs, RFM & Cohort Pipeline
python -m src.pipeline

# 4. Initialize Database Schema & Load MySQL Star Schema
python -m src.database.load       # Atomic load of 536,641 fact rows

# 5. Run SQL Analytics & Cross-System Reconciliation
python scripts\reconcile_sql.py   # Confirms 100% exact match between SQL and Python

# 6. Generate Publication Figures & Visual Reports
python scripts\generate_eda.py    # Outputs charts to reports\figures\

# 7. Launch Interactive Analytics Dashboard
streamlit run dashboard.py        # Opens multi-page interactive dashboard

# 8. Run Automated Test Suite
python -m unittest discover -s tests -t .
```

## System Architecture & Layout
- `src/`
  - `ingestion/`: Dataset discovery, schema validation, encoding detection
  - `etl/`: Cleaning, deduplication, row-accounting, feature engineering
  - `analytics/`: Business KPIs, monthly trends, RFM segmentation, cohort retention
  - `validation/`: Independent pure-Python reconciliation cross-checks
  - `database/`: Automated schema management, MySQL staging and star schema loading
- `sql/`: DDL schema, dimension/fact transformations, sales analysis, retention, RFM, cohorts
- `exports/`: Power BI-ready CSV data marts (monthly sales, RFM, cohort matrix)
- `powerbi/`: DAX measures and 4-page dashboard specification
- `reports/`: Executive summary, figures (`monthly_sales_trend.png`, `rfm_segment_distribution.png`, `cohort_retention_heatmap.png`), reconciliation report
- `dashboard.py`: 5-page interactive Streamlit business dashboard
- `tests/`: 29 unit tests covering ingestion, cleaning, features, KPIs, cohorts, and SQL integrity

## Analytical Definitions
- **Net Sales**: Period Gross Sales (`line_type == 'sale'`) minus Returns (`line_type == 'cancellation'`).
- **Repeat Purchase Rate**: $65.58\%$ (customers with $\ge 2$ distinct purchase invoices).
- **RFM Segmentation**: Percentile-based scoring (1–5) across Recency, Frequency, and Monetary metrics.
- **Cohort Retention**: Activity measured by distinct customers with qualifying transactions in each calendar month relative to their acquisition cohort.
