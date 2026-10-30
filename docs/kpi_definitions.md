# KPI definitions
| KPI | Definition |
|---|---|
| Line value | signed `quantity × unit_price` |
| Sale line | not cancellation, quantity>0, unit_price>0 |
| Cancellation line | `invoice_no` starts with `C` (UCI convention; **verify on real data**) |
| Adjustment line | non-cancellation with quantity<0 or unit_price≤0 – kept for audit, excluded from all KPIs |
| Gross sales | Σ line value over sale lines |
| Returns | Σ |line value| over cancellation lines |
| Net sales | Gross sales − Returns (period-level; credits are not linked to original invoices) |
| Sales invoices | distinct `invoice_no` on sale lines |
| Customers | distinct `customer_id` on sale lines with a customer id (rows lacking an id are excluded from customer metrics only) |
| Average invoice value | Gross sales ÷ sales invoices |
| Repeat customer | customer with ≥2 distinct sale invoices; rate = repeat ÷ customers |
| Cohort | month of customer's first sale; retention = active customers in month k ÷ cohort size |
| RFM | recency days to (last data day + 1); frequency = distinct invoices; monetary = Σ sale line value; scores 1–5 from rank position (heuristic thresholds, not an industry standard) |
