-- Populate dimensions then fact from staging. Safe to rerun after staging.sql.
INSERT IGNORE INTO dim_country (country_name)
  SELECT DISTINCT COALESCE(country,'Unspecified') FROM stg_transactions;

INSERT IGNORE INTO dim_customer (customer_id)
  SELECT DISTINCT customer_id FROM stg_transactions WHERE customer_id IS NOT NULL;

INSERT INTO dim_product (stock_code, description)
  SELECT stock_code, description FROM (
    SELECT stock_code, description,
           ROW_NUMBER() OVER (PARTITION BY stock_code ORDER BY invoice_date DESC, source_row_id DESC) rn
    FROM stg_transactions) t WHERE rn = 1
  ON DUPLICATE KEY UPDATE description = VALUES(description);

INSERT IGNORE INTO dim_date (date_key, full_date, `year`, `quarter`, `month`, `year_month`, month_name, day_of_week)
  SELECT DISTINCT CAST(DATE_FORMAT(invoice_date,'%Y%m%d') AS UNSIGNED), DATE(invoice_date),
         YEAR(invoice_date), QUARTER(invoice_date), MONTH(invoice_date),
         DATE_FORMAT(invoice_date,'%Y-%m'), MONTHNAME(invoice_date), WEEKDAY(invoice_date)
  FROM stg_transactions;

INSERT INTO fact_transaction_line
  (source_row_id, invoice_no, date_key, customer_key, product_key, country_key,
   invoice_ts, quantity, unit_price, line_value, line_type)
SELECT s.source_row_id, s.invoice_no,
       CAST(DATE_FORMAT(s.invoice_date,'%Y%m%d') AS UNSIGNED),
       c.customer_key, p.product_key, k.country_key,
       s.invoice_date, s.quantity, s.unit_price, s.quantity * s.unit_price, s.line_type
FROM stg_transactions s
LEFT JOIN dim_customer c ON c.customer_id = s.customer_id
JOIN dim_product p ON p.stock_code = s.stock_code
JOIN dim_country k ON k.country_name = COALESCE(s.country,'Unspecified');
