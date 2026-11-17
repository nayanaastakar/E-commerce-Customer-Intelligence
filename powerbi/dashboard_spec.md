# Dashboard specification (4 pages) — NOT BUILT
No Power BI Desktop was available, so no `.pbix` exists. Build steps: import the tables from MySQL
(or the CSVs in `exports/`), create relationships as in `measures.dax`, add measures, then lay out pages:

1. **Executive Overview** – cards: Net Sales, Invoice Count, Customer Count, Average Invoice Value, Repeat Purchase Rate; line: monthly Net Sales; map/bar: Gross Sales by country; bar: top 10 products; slicers: date, country.
2. **Customer Retention** – matrix: cohort × cohort_age, value `Retention %`, colour-scale conditional formatting (blank = not yet observed); line: repeat-purchase trend; column: customers per cohort.
3. **Customer Segmentation** – donut/bar: customers by segment; bar: Revenue by Segment; scatter: recency vs frequency (size = monetary); table: top customers; slicer: segment.
4. **Sales & Product Performance** – monthly sales + MoM %; top products with cumulative %; Returns by month; country bar; Average Invoice Value trend.
Design: Apply the provided `frozen_mist_theme.json` theme palette (#DD700B cinnamon, #7C7D75 graphite, #ADACA7 stone gray, #FCF8D8 warm ivory, #D9DADF cool mist), WCAG-contrast text, titles on every visual, number formats (thousands separators, % with 1 dp).
