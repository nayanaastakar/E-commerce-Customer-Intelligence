"""Fetch the Online Retail dataset. Tries Kaggle CLI (needs your own authenticated
~/.kaggle/kaggle.json or KAGGLE_* env vars - never paste tokens into code), then the
official UCI mirror. Fails clearly if neither works; manual steps are printed."""
import shutil, subprocess, sys, urllib.request, zipfile
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
UCI_URL = "https://archive.ics.uci.edu/static/public/352/online+retail.zip"
MANUAL = """Manual download:
  1. Kaggle: https://www.kaggle.com/datasets/vijayuv/onlineretail  (or UCI id 352)
  2. Put the .csv / .xlsx file in data/raw/
"""

def via_kaggle():
    if not shutil.which("kaggle"):
        return False
    r = subprocess.run(["kaggle", "datasets", "download", "-d", "vijayuv/onlineretail",
                        "-p", str(RAW), "--unzip"], capture_output=True, text=True)
    print(r.stdout, r.stderr)
    return r.returncode == 0

def _convert_xlsx_to_csv(xlsx_path: Path, csv_path: Path):
    import csv, openpyxl
    print(f"Converting {xlsx_path.name} to CSV for faster loading...")
    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    ws = wb.active
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for row in ws.iter_rows(values_only=True):
            writer.writerow(row)
    wb.close()
    print(f"Created {csv_path.name}")


def via_uci():
    z = RAW / "online_retail.zip"
    urllib.request.urlretrieve(UCI_URL, z)
    with zipfile.ZipFile(z) as f:
        f.extractall(RAW)
    z.unlink()
    xlsx = RAW / "Online Retail.xlsx"
    if xlsx.exists():
        _convert_xlsx_to_csv(xlsx, RAW / "Online Retail.csv")
    return True

if __name__ == "__main__":
    RAW.mkdir(parents=True, exist_ok=True)
    for name, fn in (("kaggle", via_kaggle), ("uci", via_uci)):
        try:
            if fn():
                print(f"Downloaded via {name} into {RAW}"); sys.exit(0)
        except Exception as e:
            print(f"[{name}] failed: {e}")
    print(MANUAL); sys.exit(1)
