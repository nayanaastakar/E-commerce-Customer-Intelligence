-- Cohort = month of first qualifying purchase. Denominator = customers in the cohort (month 0).
-- Active in month k = >=1 sale invoice in that calendar month (distinct customers, so duplicate rows cannot inflate).
WITH first_m AS (SELECT customer_key, DATE_FORMAT(MIN(invoice_ts),'%Y-%m-01') AS cohort_start
                 FROM fact_transaction_line WHERE line_type='sale' AND customer_key IS NOT NULL GROUP BY customer_key),
act AS (SELECT DISTINCT customer_key, DATE_FORMAT(invoice_ts,'%Y-%m-01') AS m FROM fact_transaction_line
        WHERE line_type='sale' AND customer_key IS NOT NULL),
ages AS (SELECT DATE_FORMAT(f.cohort_start,'%Y-%m') AS cohort,
                TIMESTAMPDIFF(MONTH, f.cohort_start, a.m) AS age, a.customer_key
         FROM act a JOIN first_m f USING (customer_key)),
cnt AS (SELECT cohort, age, COUNT(DISTINCT customer_key) active FROM ages GROUP BY cohort, age)
SELECT c.cohort, c.age AS month_index, c.active,
       ROUND(100*c.active/ s.active, 2) AS retention_pct
FROM cnt c JOIN cnt s ON s.cohort=c.cohort AND s.age=0
ORDER BY c.cohort, c.age;
-- Note: cells beyond the last month in the data are absent (unknown), not zero.
