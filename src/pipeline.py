"""Run: python -m src.pipeline [--file PATH]
Writes processed data, rejected rows, analytical exports (CSV for Power BI) and
a machine-readable data quality report. Re-running overwrites outputs (idempotent)."""
import argparse, json, logging, sys
from pathlib import Path
import pandas as pd
from src import config
from src.ingestion.loader import find_dataset, load_raw
from src.analytics.profiling import profile_raw
from src.analytics.metrics import kpis, monthly_sales
from src.analytics.customers import customer_summary, rfm, cohort_retention
from src.etl.clean import clean
from src.etl.features import add_features
from src.validation.reconcile import independent_kpis, compare

log = logging.getLogger("pipeline")


def run(file=None, out_dir=None, export_dir=None):
    out_dir = Path(out_dir or config.PROCESSED_DIR); out_dir.mkdir(parents=True, exist_ok=True)
    export_dir = Path(export_dir or config.EXPORT_DIR); export_dir.mkdir(parents=True, exist_ok=True)
    path = Path(file) if file else find_dataset(config.RAW_DIR)
    raw = load_raw(path)
    profile = profile_raw(raw)
    res = clean(raw)
    del raw
    df = add_features(res.clean)

    k = kpis(df)
    diffs = compare(k, independent_kpis(df))
    if diffs:
        raise RuntimeError(f"KPI reconciliation failed: {diffs}")

    summ = customer_summary(df)
    seg = rfm(summ)
    counts, pct = cohort_retention(df)

    df.to_csv(out_dir / "transactions_clean.csv", index=False)
    res.rejected.to_csv(out_dir / "transactions_rejected.csv", index=False)
    monthly_sales(df).to_csv(export_dir / "monthly_sales.csv", index=False)
    seg.to_csv(export_dir / "customer_rfm.csv", index=False)
    pct.reset_index().to_csv(export_dir / "cohort_retention_pct.csv", index=False)
    counts.reset_index().to_csv(export_dir / "cohort_retention_counts.csv", index=False)
    report = {"source_file": path.name, "profile": profile, "cleaning": res.stats, "kpis": k,
              "reconciliation": "python-vs-independent PASSED"}
    (out_dir / "data_quality_report.json").write_text(json.dumps(report, indent=2, default=str))
    log.info("Pipeline complete: %s", k)
    return report


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    ap = argparse.ArgumentParser(); ap.add_argument("--file")
    try:
        run(ap.parse_args().file)
    except Exception as e:
        log.error("Pipeline failed: %s", e); sys.exit(1)
