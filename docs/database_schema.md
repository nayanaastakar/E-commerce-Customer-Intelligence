# Database schema (MySQL 8) — DDL written, NOT executed
```mermaid
erDiagram
  dim_date ||--o{ fact_transaction_line : date_key
  dim_customer ||--o{ fact_transaction_line : customer_key
  dim_product ||--o{ fact_transaction_line : product_key
  dim_country ||--o{ fact_transaction_line : country_key
```
Grain: one source invoice line. No invoice-level totals are stored, preventing fan-out double counting.
`customer_key` is NULL when the source has no customer id. `stg_transactions` is the staging layer.
