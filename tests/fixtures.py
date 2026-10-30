"""SYNTHETIC unit-test fixture (12 hand-built rows). NOT the real dataset and never
used for reported business results. Expected values below were computed by hand."""
import pandas as pd

COLS = ["InvoiceNo", "StockCode", "Description", "Quantity", "InvoiceDate",
        "UnitPrice", "CustomerID", "Country"]
ROWS = [
    ["1001", "A", "Widget", "2", "2024-01-05 10:00:00", "5.00", "1", "UK"],
    ["1002", "B", "Gadget", "1", "2024-02-10 11:00:00", "20.00", "1", "UK"],
    ["1003", "A", "Widget", "3", "2024-01-20 09:00:00", "5.00", "2", "FR"],
    ["1004", "C", "Thing", "1", "2024-03-01 12:00:00", "100.00", "", "UK"],       # no customer
    ["C1005", "A", "Widget", "-1", "2024-02-15 13:00:00", "5.00", "1", "UK"],     # cancellation
    ["1006", "D", "Adj", "-5", "2024-02-16 14:00:00", "0", "", "UK"],             # adjustment
    ["1007", "E", "Bad", "1", "notadate", "1.00", "9", "UK"],                      # invalid date
    ["1008", "E", "Bad", "abc", "2024-02-01 10:00:00", "1.00", "9", "UK"],         # bad qty
    ["1001", "A", "Widget", "2", "2024-01-05 10:00:00", "5.00", "1", "UK"],        # exact duplicate
    ["1009", "E", "Zero", "0", "2024-02-02 10:00:00", "1.00", "9", "UK"],          # zero qty
    ["1010", "A", "Widget", "4", "2024-02-03 10:00:00", "5.00", "3", "UK"],
    ["1011", "A", "Widget", "1", "2024-03-12 10:00:00", "5.00", "2", "FR"],
]

def raw_df():
    from src.ingestion.loader import normalise_columns
    df = pd.DataFrame(ROWS, columns=COLS, dtype=str)
    df.columns = normalise_columns(df.columns)
    return df

EXPECTED = dict(raw_rows=12, rejected=3, duplicates=1, clean_rows=8,
                sales_invoices=6, customers=3, gross_sales=170.0, returns=5.0,
                net_sales=165.0, avg_invoice_value=28.33, repeat_customers=2,
                repeat_purchase_rate=0.6667)
