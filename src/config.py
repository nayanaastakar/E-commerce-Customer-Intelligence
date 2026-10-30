"""Environment-driven configuration. No secrets in source."""
import os, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def _load_dotenv():
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
    except ImportError:
        pass

_load_dotenv()

RAW_DIR = ROOT / os.getenv("RAW_DATA_DIR", "data/raw")
PROCESSED_DIR = ROOT / os.getenv("PROCESSED_DATA_DIR", "data/processed")
EXPORT_DIR = ROOT / os.getenv("EXPORT_DIR", "exports")

def mysql_url() -> str:
    missing = [k for k in ("MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_DATABASE") if not os.getenv(k)]
    if missing:
        raise RuntimeError(f"Missing environment variables: {missing}. See .env.example")
    user = urllib.parse.quote_plus(os.getenv("MYSQL_USER", ""))
    pwd = urllib.parse.quote_plus(os.getenv("MYSQL_PASSWORD", ""))
    host = os.getenv("MYSQL_HOST", "localhost")
    port = os.getenv("MYSQL_PORT", "3306")
    db = os.getenv("MYSQL_DATABASE", "")
    return f"mysql+pymysql://{user}:{pwd}@{host}:{port}/{db}"
