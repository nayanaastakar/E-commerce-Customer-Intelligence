-- Mirrors src/analytics/customers.py: score = CEIL(5 * row_number / n); recency inverted.
-- Ties broken by customer_id (binary collation) to match pandas rank(method='first') on sorted ids.
WITH ad AS (SELECT DATE_ADD(DATE(MAX(invoice_ts)), INTERVAL 1 DAY) d FROM fact_transaction_line),
base AS (
  SELECT c.customer_id,
         DATEDIFF((SELECT d FROM ad), DATE(MAX(f.invoice_ts))) AS recency_days,
         COUNT(DISTINCT f.invoice_no) AS frequency,
         SUM(f.line_value) AS monetary
  FROM fact_transaction_line f JOIN dim_customer c USING (customer_key)
  WHERE f.line_type='sale' GROUP BY c.customer_id),
sc AS (
  SELECT b.*, COUNT(*) OVER () n,
    ROW_NUMBER() OVER (ORDER BY recency_days, customer_id COLLATE utf8mb4_bin) rr,
    ROW_NUMBER() OVER (ORDER BY frequency,    customer_id COLLATE utf8mb4_bin) fr,
    ROW_NUMBER() OVER (ORDER BY monetary,     customer_id COLLATE utf8mb4_bin) mr
  FROM base b),
s2 AS (SELECT customer_id, recency_days, frequency, monetary,
              6 - CEIL(5*rr/n) AS r_score, CEIL(5*fr/n) AS f_score, CEIL(5*mr/n) AS m_score FROM sc)
SELECT *, CASE
  WHEN r_score>=4 AND f_score>=4 THEN 'Champions'
  WHEN r_score>=3 AND f_score>=4 THEN 'Loyal Customers'
  WHEN r_score>=4 AND f_score<=2 THEN 'Recent Customers'
  WHEN r_score>=3 AND f_score>=2 THEN 'Potential Loyalists'
  WHEN r_score<=2 AND f_score>=3 THEN 'At-Risk Customers'
  WHEN r_score<=2 AND f_score<=2 THEN 'Hibernating Customers'
  ELSE 'Other Customers' END AS segment
FROM s2;
