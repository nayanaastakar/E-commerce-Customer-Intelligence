-- Headline KPIs (definitions: docs/kpi_definitions.md)
SELECT COUNT(DISTINCT CASE WHEN line_type='sale' THEN invoice_no END)                 AS sales_invoices,
       COUNT(DISTINCT CASE WHEN line_type='sale' THEN customer_key END)               AS customers,
       ROUND(SUM(CASE WHEN line_type='sale' THEN line_value END),2)                   AS gross_sales,
       ROUND(SUM(CASE WHEN line_type='cancellation' THEN -line_value END),2)          AS returns,
       ROUND(SUM(CASE WHEN line_type='sale' THEN line_value
                      WHEN line_type='cancellation' THEN line_value END),2)           AS net_sales
FROM fact_transaction_line;

-- Monthly sales with MoM growth and 3-month rolling average
WITH m AS (
  SELECT d.`year_month`,
         SUM(CASE WHEN f.line_type='sale' THEN f.line_value ELSE 0 END)           AS gross_sales,
         SUM(CASE WHEN f.line_type='cancellation' THEN -f.line_value ELSE 0 END)  AS returns,
         COUNT(DISTINCT CASE WHEN f.line_type='sale' THEN f.invoice_no END)       AS invoices,
         COUNT(DISTINCT CASE WHEN f.line_type='sale' THEN f.customer_key END)     AS customers
  FROM fact_transaction_line f JOIN dim_date d USING (date_key)
  GROUP BY d.`year_month`)
SELECT `year_month`, gross_sales, returns, gross_sales-returns AS net_sales, invoices, customers,
       ROUND(100*((gross_sales-returns) / NULLIF(LAG(gross_sales-returns) OVER w,0) - 1),2) AS mom_growth_pct,
       ROUND(AVG(gross_sales-returns) OVER (ORDER BY `year_month` ROWS BETWEEN 2 PRECEDING AND CURRENT ROW),2) AS rolling_3m_net
FROM m WINDOW w AS (ORDER BY `year_month`) ORDER BY `year_month`;

-- Year-over-year (only meaningful where the same month exists in the prior year)
WITH m AS (SELECT d.`year`, d.`month`, SUM(f.line_value) AS gross
           FROM fact_transaction_line f JOIN dim_date d USING (date_key)
           WHERE f.line_type='sale' GROUP BY d.`year`, d.`month`)
SELECT `year`, `month`, gross, ROUND(100*(gross/NULLIF(LAG(gross,1) OVER (PARTITION BY `month` ORDER BY `year`),0)-1),2) AS yoy_pct
FROM m ORDER BY `year`, `month`;

-- Sales by country
SELECT k.country_name, ROUND(SUM(f.line_value),2) AS gross_sales,
       COUNT(DISTINCT f.invoice_no) AS invoices
FROM fact_transaction_line f JOIN dim_country k USING (country_key)
WHERE f.line_type='sale' GROUP BY k.country_name ORDER BY gross_sales DESC;

-- Top 20 products + cumulative contribution
WITH p AS (SELECT p.stock_code, p.description, SUM(f.line_value) AS gross, SUM(f.quantity) AS units
           FROM fact_transaction_line f JOIN dim_product p USING (product_key)
           WHERE f.line_type='sale' GROUP BY p.stock_code, p.description)
SELECT stock_code, description, ROUND(gross,2) gross_sales, units,
       ROUND(100*gross/SUM(gross) OVER (),2) AS pct_of_sales,
       ROUND(100*SUM(gross) OVER (ORDER BY gross DESC)/SUM(gross) OVER (),2) AS cumulative_pct
FROM p ORDER BY gross DESC LIMIT 20;

-- Returns / cancellations by month
SELECT d.`year_month`, COUNT(DISTINCT f.invoice_no) AS cancel_invoices, ROUND(SUM(-f.line_value),2) AS credit_value
FROM fact_transaction_line f JOIN dim_date d USING (date_key)
WHERE f.line_type='cancellation' GROUP BY d.`year_month` ORDER BY d.`year_month`;

-- Customer revenue concentration: share of sales from the top 10% of customers
WITH c AS (SELECT customer_key, SUM(line_value) rev FROM fact_transaction_line
           WHERE line_type='sale' AND customer_key IS NOT NULL GROUP BY customer_key),
r AS (SELECT rev, NTILE(10) OVER (ORDER BY rev DESC) AS decile FROM c)
SELECT decile, ROUND(SUM(rev),2) AS revenue, ROUND(100*SUM(rev)/SUM(SUM(rev)) OVER (),2) AS pct_of_customer_revenue
FROM r GROUP BY decile ORDER BY decile;
