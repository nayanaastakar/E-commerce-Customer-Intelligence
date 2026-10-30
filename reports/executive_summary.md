# Executive Summary: E-Commerce Customer Intelligence & Retention Analytics

## 1. Overview
This analytics platform processes UK-based online retail transactions, transforming transactional event streams through an automated ETL pipeline into a verified MySQL 8.0 star schema data warehouse, reproducible SQL analytical views, and Power BI-ready data marts.

---

## 2. Headline Performance Metrics

| Metric | Value | Description |
|---|---|---|
| **Gross Sales** | £10,642,110.80 | Total value of qualifying sale transactions |
| **Returns & Cancellations** | £893,979.73 | Credit value of cancellations (8.40% return rate) |
| **Net Sales** | £9,748,131.07 | Period net sales (Gross Sales - Returns) |
| **Sales Invoices** | 19,960 | Total qualifying sales invoices |
| **Unique Customers** | 4,338 | Identified purchasing customers |
| **Average Invoice Value** | £533.17 | Average gross revenue per sale invoice |
| **Repeat Customers** | 2,845 | Customers with $\ge 2$ distinct purchase orders |
| **Repeat Purchase Rate** | **65.58%** | Share of customer base with repeat transactions |

---

## 3. Data Cleaning & Integrity Summary

From the raw dataset of **541,909 records**:
- **0 records structurally rejected** (all records contained valid dates, prices, quantities, and stock codes).
- **5,268 exact duplicate records removed** (accounting for identical multi-item resubmissions).
- **536,641 clean transactional records loaded**:
  - `sale`: 524,878 rows (97.8%)
  - `cancellation`: 9,251 rows (1.7%)
  - `adjustment`: 2,512 rows (0.5%) – internal corrections/postage/discounts excluded from customer KPIs.
- **Customer ID Coverage**: 74.84% (135,037 anonymous guest transactions retained as real sales in general revenue metrics, excluded only from customer-level RFM and cohort metrics).

---

## 4. RFM Customer Segmentation Findings

Customers were scored from 1 to 5 across Recency (inverted), Frequency, and Monetary dimensions using percentile rankings:

- **Champions (R $\ge$ 4, F $\ge$ 4)**: High-value, frequent, and recently active customers generating disproportionate revenue.
- **Loyal Customers (R $\ge$ 3, F $\ge$ 4)**: Consistent purchasers with steady order cadences.
- **Potential Loyalists (R $\ge$ 3, F $\ge$ 2)**: Recent buyers with multiple purchases ripe for loyalty rewards.
- **Recent Customers (R $\ge$ 4, F $\le$ 2)**: Newly acquired customers requiring onboarding nurturing.
- **At-Risk Customers (R $\le$ 2, F $\ge$ 3)**: High historical frequency who have not purchased recently; prime target for win-back campaigns.
- **Hibernating Customers (R $\le$ 2, F $\le$ 2)**: Low frequency, long elapsed time since last purchase.

---

## 5. Cohort Retention Dynamics

- Initial customer cohorts (e.g. December 2010 cohort) demonstrate a 12-month retention trajectory stabilizing around 35–50% repeat activity in subsequent quarters.
- Mid-period cohorts show sustained 20–30% month-over-month engagement.
- High repeat purchase rate (65.58%) indicates strong underlying product-market fit in wholesale and gift categories.

---

## 6. Generated Artifacts & Visualizations
- `reports/figures/monthly_sales_trend.png`: Monthly sales volume and MoM growth percentage.
- `reports/figures/rfm_segment_distribution.png`: Customer count and share across RFM segments.
- `reports/figures/cohort_retention_heatmap.png`: Retention matrix heatmap across customer tenure.
- `data/processed/data_quality_report.json`: Full data profiling and audit trial.
- `exports/*.csv`: Power BI-ready CSV data marts.
