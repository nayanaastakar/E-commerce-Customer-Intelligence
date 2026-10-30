"""Dataset discovery, schema validation and loading.

Column names are normalised to snake_case and mapped through ALIASES so the
UCI/Kaggle variants load identically. If required columns are missing the
loader raises SchemaError instead of guessing.
"""
import logging
import re
from pathlib import Path
import pandas as pd

log = logging.getLogger(__name__)

REQUIRED = ["invoice_no", "stock_code", "description", "quantity",
            "invoice_date", "unit_price", "customer_id", "country"]
ALIASES = {"invoiceno": "invoice_no", "invoice": "invoice_no", "stockcode": "stock_code",
           "invoicedate": "invoice_date", "unitprice": "unit_price", "price": "unit_price",
           "customerid": "customer_id"}
SUPPORTED = (".csv", ".xlsx", ".xls")


class SchemaError(ValueError):
    pass


def normalise_columns(cols):
    out = []
    for c in cols:
        key = re.sub(r"[^0-9a-z]+", "_", str(c).strip().lower()).strip("_")
        out.append(ALIASES.get(key.replace("_", ""), key))
    return out


def find_dataset(raw_dir: Path) -> Path:
    raw_dir = Path(raw_dir)
    if not raw_dir.is_dir():
        raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")
    files = sorted(p for p in raw_dir.iterdir() if p.suffix.lower() in SUPPORTED)
    if not files:
        raise FileNotFoundError(
            f"No {SUPPORTED} file in {raw_dir}. Run scripts/download_data.py or place the file manually.")
    if len(files) > 1:
        log.warning("Multiple data files found; using %s", files[0].name)
    return files[0]


def validate_schema(df: pd.DataFrame) -> None:
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise SchemaError(f"Missing required columns: {missing}. Found: {list(df.columns)}")


def load_raw(path: Path) -> pd.DataFrame:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)
    if path.suffix.lower() == ".csv":
        try:
            df = pd.read_csv(path, dtype=str, encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(path, dtype=str, encoding="latin-1")
    else:
        df = pd.read_excel(path, dtype=str)
    df.columns = normalise_columns(df.columns)
    if len(df) == 0:
        raise ValueError(f"Input file is empty: {path}")
    validate_schema(df)
    log.info("Loaded %d rows x %d cols from %s", len(df), df.shape[1], path.name)
    return df
