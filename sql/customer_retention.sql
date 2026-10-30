-- Repeat purchase: customers with >=2 distinct sale invoices
WITH ci AS (SELECT customer_key, COUNT(DISTINCT invoice_no) n FROM fact_transaction_line
            WHERE line_type='sale' AND customer_key IS NOT NULL GROUP BY customer_key)
SELECT COUNT(*) customers, SUM(n>=2) repeat_customers, ROUND(SUM(n>=2)/COUNT(*),4) repeat_purchase_rate FROM ci;

-- Purchase-frequency distribution
WITH ci AS (SELECT customer_key, COUNT(DISTINCT invoice_no) n FROM fact_transaction_line
            WHERE line_type='sale' AND customer_key IS NOT NULL GROUP BY customer_key)
SELECT LEAST(n,10) AS invoices_bucket_10plus, COUNT(*) customers FROM ci GROUP BY 1 ORDER BY 1;

-- Monthly active vs returning customers
WITH first_m AS (SELECT customer_key, MIN(DATE_FORMAT(invoice_ts,'%Y-%m')) fm FROM fact_transaction_line
                 WHERE line_type='sale' AND customer_key IS NOT NULL GROUP BY customer_key),
act AS (SELECT DISTINCT customer_key, DATE_FORMAT(invoice_ts,'%Y-%m') ym FROM fact_transaction_line
        WHERE line_type='sale' AND customer_key IS NOT NULL)
SELECT a.ym, COUNT(*) active_customers, SUM(a.ym = f.fm) new_customers, SUM(a.ym > f.fm) returning_customers
FROM act a JOIN first_m f USING (customer_key) GROUP BY a.ym ORDER BY a.ym;

-- Inactivity: days since last purchase (analysis date = day after last transaction in data)
WITH ad AS (SELECT DATE_ADD(DATE(MAX(invoice_ts)), INTERVAL 1 DAY) d FROM fact_transaction_line)
SELECT CASE WHEN rd<=90 THEN '0-90' WHEN rd<=180 THEN '91-180' WHEN rd<=365 THEN '181-365' ELSE '365+' END AS recency_band,
       COUNT(*) customers
FROM (SELECT DATEDIFF((SELECT d FROM ad), DATE(MAX(invoice_ts))) rd FROM fact_transaction_line
      WHERE line_type='sale' AND customer_key IS NOT NULL GROUP BY customer_key) x
GROUP BY recency_band ORDER BY MIN(rd);
