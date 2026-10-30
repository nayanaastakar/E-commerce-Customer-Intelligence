"""Load processed CSV into MySQL (staging -> star schema) in ONE transaction.
Rerunnable: staging.sql clears fact/staging first; dims use INSERT IGNORE / upsert.
STATUS: implemented, NOT executed (no MySQL available when written)."""
import logging, re
from pathlib import Path
import pandas as pd
from src import config

log = logging.getLogger(__name__)
SQL_DIR = Path(__file__).resolve().parents[2] / "sql"
COLS = ["source_row_id", "invoice_no", "stock_code", "description", "quantity", "invoice_date",
        "unit_price", "customer_id", "country", "line_type", "has_customer"]


def _statements(path: Path):
    body = re.sub(r"--.*", "", path.read_text(encoding="utf-8"))
    return [s.strip() for s in body.split(";") if s.strip()]


def ensure_schema(engine):
    from sqlalchemy import text
    with engine.begin() as conn:
        for st in _statements(SQL_DIR / "schema.sql"):
            conn.execute(text(st))


def load(csv_path=None):
    from sqlalchemy import create_engine, text  # lazy: not needed for tests
    csv_path = Path(csv_path or config.PROCESSED_DIR / "transactions_clean.csv")
    df = pd.read_csv(csv_path, dtype={"customer_id": "string"}, parse_dates=["invoice_date"])[COLS]
    df["has_customer"] = df["has_customer"].astype(int)
    engine = create_engine(config.mysql_url())
    ensure_schema(engine)
    with engine.begin() as conn:   # rolls back on any error
        for st in _statements(SQL_DIR / "staging.sql"):
            conn.execute(text(st))
        log.info("Loading %d rows into stg_transactions...", len(df))
        df.to_sql("stg_transactions", conn, if_exists="append", index=False, chunksize=10000, method="multi")
        log.info("Running dimension and fact transformations...")
        for st in _statements(SQL_DIR / "transformations.sql"):
            conn.execute(text(st))
        n_f = conn.execute(text("SELECT COUNT(*) FROM fact_transaction_line")).scalar()
    if n_f != len(df):
        raise RuntimeError(f"Row-count mismatch: csv={len(df)} fact={n_f}")
    log.info("Loaded %d fact rows", n_f)
    return n_f

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO); load()
