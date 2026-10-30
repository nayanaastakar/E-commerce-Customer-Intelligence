"""Cleaning with explicit outcomes per record.

* REJECTED  - structurally unusable (bad date, non-numeric qty/price, no invoice id,
              zero quantity, no stock code). Kept in a rejected table with a reason.
* DUPLICATE - exact full-row duplicates (first occurrence kept). Counted separately.
* RETAINED with line_type:
    sale          - normal line
    cancellation  - invoice_no starts with 'C' (UCI convention; VERIFY on real file)
    adjustment    - non-cancellation row with qty<0 or price<=0; kept for audit,
                    EXCLUDED from sales and customer metrics
* Rows without customer_id are retained (real sales) with has_customer=False and
  excluded from customer-level analytics only.
"""
import logging
from dataclasses import dataclass, field
import pandas as pd

log = logging.getLogger(__name__)


@dataclass
class CleanResult:
    clean: pd.DataFrame
    rejected: pd.DataFrame
    stats: dict = field(default_factory=dict)


def clean(raw: pd.DataFrame) -> CleanResult:
    df = raw.copy()
    n_raw = len(df)
    df["source_row_id"] = range(1, n_raw + 1)

    for c in ("invoice_no", "stock_code", "description", "country", "customer_id"):
        df[c] = df[c].astype("string").str.strip()
    df["description"] = df["description"].str.upper().replace("", pd.NA)
    df["stock_code"] = df["stock_code"].str.upper().replace("", pd.NA)
    df["invoice_no"] = df["invoice_no"].replace("", pd.NA)
    df["customer_id"] = df["customer_id"].str.replace(r"\.0$", "", regex=True).replace("", pd.NA)

    df["invoice_date"] = pd.to_datetime(df["invoice_date"], errors="coerce")
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")

    reason = pd.Series(pd.NA, index=df.index, dtype="string")
    def mark(mask, label):
        reason[reason.isna() & mask] = label
    mark(df["invoice_no"].isna(), "missing_invoice_no")
    mark(df["invoice_date"].isna(), "invalid_date")
    mark(df["quantity"].isna(), "non_numeric_quantity")
    mark(df["unit_price"].isna(), "non_numeric_price")
    mark(df["quantity"] == 0, "zero_quantity")
    mark(df["stock_code"].isna(), "missing_stock_code")

    rejected = df[reason.notna()].assign(reject_reason=reason[reason.notna()])
    ok = df[reason.isna()].copy()

    key = ["invoice_no", "stock_code", "description", "quantity",
           "invoice_date", "unit_price", "customer_id", "country"]
    dup_mask = ok.duplicated(subset=key, keep="first")
    n_dups = int(dup_mask.sum())
    ok = ok[~dup_mask].copy()

    ok["is_cancellation"] = ok["invoice_no"].str.upper().str.startswith("C")
    ok["line_type"] = "sale"
    ok.loc[ok["is_cancellation"], "line_type"] = "cancellation"
    adj = (~ok["is_cancellation"]) & ((ok["quantity"] < 0) | (ok["unit_price"] <= 0))
    ok.loc[adj, "line_type"] = "adjustment"
    ok["has_customer"] = ok["customer_id"].notna()
    ok = ok.reset_index(drop=True)

    stats = {
        "raw_rows": n_raw,
        "rejected_rows": len(rejected),
        "rejected_by_reason": rejected["reject_reason"].value_counts().to_dict(),
        "exact_duplicates_removed": n_dups,
        "clean_rows": len(ok),
        "line_type_counts": ok["line_type"].value_counts().to_dict(),
        "rows_missing_customer_id": int((~ok["has_customer"]).sum()),
        "customer_id_coverage_pct": round(100 * float(ok["has_customer"].mean()), 2) if len(ok) else 0.0,
    }
    assert n_raw == len(rejected) + n_dups + len(ok), "row accounting mismatch"
    log.info("Clean stats: %s", stats)
    return CleanResult(ok, rejected, stats)
