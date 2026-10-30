import json, tempfile, unittest
from pathlib import Path
import numpy as np
import pandas as pd
from src.ingestion.loader import (SchemaError, find_dataset, load_raw, normalise_columns, validate_schema)
from src.etl.clean import clean
from src.etl.features import add_features
from src.analytics.metrics import kpis, monthly_sales
from src.analytics.customers import customer_summary, rfm, segment_label, cohort_retention
from src.validation.reconcile import independent_kpis, compare
from src import pipeline
from tests.fixtures import raw_df, EXPECTED, COLS, ROWS


def prepared():
    return add_features(clean(raw_df()).clean)


class TestIngestion(unittest.TestCase):
    def test_column_normalisation(self):
        self.assertEqual(normalise_columns(COLS),
            ["invoice_no", "stock_code", "description", "quantity", "invoice_date",
             "unit_price", "customer_id", "country"])

    def test_missing_column_raises(self):
        with self.assertRaises(SchemaError):
            validate_schema(raw_df().drop(columns=["unit_price"]))

    def test_no_file_raises(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(FileNotFoundError):
                find_dataset(Path(d))
        with self.assertRaises(FileNotFoundError):
            find_dataset(Path("/nonexistent_dir_xyz"))

    def test_empty_file_raises(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.csv"; p.write_text(",".join(COLS) + "\n")
            with self.assertRaises(ValueError):
                load_raw(p)

    def test_latin1_csv_loads(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.csv"
            pd.DataFrame(ROWS, columns=COLS).assign(Description="Caf\xe9").to_csv(p, index=False, encoding="latin-1")
            self.assertEqual(len(load_raw(p)), 12)


class TestCleaning(unittest.TestCase):
    def setUp(self):
        self.res = clean(raw_df())

    def test_row_accounting(self):
        s = self.res.stats
        self.assertEqual(s["raw_rows"], EXPECTED["raw_rows"])
        self.assertEqual(s["rejected_rows"], EXPECTED["rejected"])
        self.assertEqual(s["exact_duplicates_removed"], EXPECTED["duplicates"])
        self.assertEqual(s["clean_rows"], EXPECTED["clean_rows"])

    def test_reject_reasons(self):
        self.assertEqual(self.res.stats["rejected_by_reason"],
                         {"invalid_date": 1, "non_numeric_quantity": 1, "zero_quantity": 1})

    def test_line_types(self):
        self.assertEqual(self.res.stats["line_type_counts"], {"sale": 6, "cancellation": 1, "adjustment": 1})

    def test_missing_customer_retained_not_dropped(self):
        c = self.res.clean
        self.assertEqual(int((~c.has_customer).sum()), 2)
        self.assertIn("1004", set(c.invoice_no))

    def test_negative_quantity_preserved_on_cancellation(self):
        c = self.res.clean
        self.assertEqual(c.loc[c.invoice_no == "C1005", "quantity"].iloc[0], -1)

    def test_invalid_price_adjustment_excluded_from_sales(self):
        c = self.res.clean
        self.assertEqual(c.loc[c.invoice_no == "1006", "line_type"].iloc[0], "adjustment")

    def test_empty_frame_after_all_rejected(self):
        raw = raw_df().iloc[[6]]  # only invalid date row
        res = clean(raw)
        self.assertEqual(len(res.clean), 0)
        self.assertEqual(res.stats["rejected_rows"], 1)


class TestFeatures(unittest.TestCase):
    def test_line_value_and_dates(self):
        df = prepared()
        self.assertEqual(df.loc[df.invoice_no == "C1005", "line_value"].iloc[0], -5.0)
        self.assertEqual(df.loc[df.invoice_no == "1001", "year_month"].iloc[0], "2024-01")
        self.assertEqual(df.loc[df.invoice_no == "1001", "year"].iloc[0], 2024)


class TestKpis(unittest.TestCase):
    def test_expected_kpis(self):
        k = kpis(prepared())
        for key in ("sales_invoices", "customers", "gross_sales", "returns", "net_sales",
                    "avg_invoice_value", "repeat_customers", "repeat_purchase_rate"):
            self.assertAlmostEqual(k[key], EXPECTED[key], places=2, msg=key)

    def test_independent_reconciliation(self):
        df = prepared()
        self.assertEqual(compare(kpis(df), independent_kpis(df.to_dict("records"))), {})

    def test_monthly_sales_sums_match_totals(self):
        df = prepared(); m = monthly_sales(df)
        self.assertAlmostEqual(m.gross_sales.sum(), 170.0)
        self.assertAlmostEqual(m.net_sales.sum(), 165.0)


class TestCustomers(unittest.TestCase):
    def setUp(self):
        self.s = customer_summary(prepared())

    def test_frequency_single_vs_multi(self):
        f = self.s.set_index("customer_id").frequency
        self.assertEqual((f["1"], f["2"], f["3"]), (2, 2, 1))
        self.assertEqual(self.s.set_index("customer_id").is_repeat.to_dict(),
                         {"1": True, "2": True, "3": False})

    def test_recency_values(self):
        r = self.s.set_index("customer_id").recency_days
        self.assertEqual((r["1"], r["2"], r["3"]), (32, 1, 39))

    def test_recent_customer_gets_better_recency_score(self):
        r = rfm(self.s).set_index("customer_id").r_score
        self.assertGreater(r["2"], r["1"]); self.assertGreater(r["1"], r["3"])

    def test_segment_rules(self):
        self.assertEqual(segment_label(5, 5), "Champions")
        self.assertEqual(segment_label(1, 1), "Hibernating Customers")
        self.assertEqual(segment_label(2, 4), "At-Risk Customers")
        self.assertEqual(segment_label(5, 1), "Recent Customers")

    def test_customers_without_id_excluded(self):
        self.assertNotIn("1004", set(prepared().loc[prepared().has_customer, "invoice_no"]))
        self.assertEqual(len(self.s), 3)


class TestCohort(unittest.TestCase):
    def test_retention_matrix(self):
        counts, pct = cohort_retention(prepared())
        self.assertEqual(counts.loc["2024-01"].tolist(), [2, 1, 1])
        self.assertEqual(pct.loc["2024-01"].tolist(), [100.0, 50.0, 50.0])
        self.assertEqual(pct.loc["2024-02", 0], 100.0)

    def test_unobserved_cells_are_nan_not_zero(self):
        _, pct = cohort_retention(prepared())
        self.assertTrue(np.isnan(pct.loc["2024-02", 2]))

    def test_duplicate_rows_do_not_inflate_counts(self):
        df = prepared()
        dup = pd.concat([df, df[df.invoice_no == "1001"]], ignore_index=True)
        c1, _ = cohort_retention(df); c2, _ = cohort_retention(dup)
        self.assertTrue(c1.equals(c2))


class TestPipelineRun(unittest.TestCase):
    def _csv(self, d):
        p = Path(d) / "in.csv"
        pd.DataFrame(ROWS, columns=COLS).to_csv(p, index=False); return p

    def test_end_to_end_and_rerun_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            p = self._csv(d)
            out, exp = Path(d) / "out", Path(d) / "exp"
            r1 = pipeline.run(p, out, exp)
            first = (out / "transactions_clean.csv").read_text()
            r2 = pipeline.run(p, out, exp)
            self.assertEqual(first, (out / "transactions_clean.csv").read_text())
            self.assertEqual(r1["kpis"], r2["kpis"])
            self.assertEqual(r1["kpis"]["net_sales"], 165.0)
            self.assertEqual(r1["reconciliation"], "python-vs-independent PASSED")
            self.assertTrue((exp / "cohort_retention_pct.csv").exists())
            json.loads((out / "data_quality_report.json").read_text())

    def test_pipeline_fails_clearly_on_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            pipeline.run(Path("/nonexistent.csv"))


class TestSqlFiles(unittest.TestCase):
    """Structural checks only - SQL has NOT been executed against MySQL."""
    def test_statement_splitting(self):
        from src.database.load import _statements, SQL_DIR
        self.assertEqual(len(_statements(SQL_DIR / "staging.sql")), 2)
        self.assertEqual(len(_statements(SQL_DIR / "transformations.sql")), 5)

    def test_schema_has_no_destructive_statements(self):
        from src.database.load import SQL_DIR
        txt = (SQL_DIR / "schema.sql").read_text().upper()
        self.assertNotIn("DROP ", txt)

    def test_fact_has_no_invoice_level_measures(self):
        from src.database.load import SQL_DIR
        txt = (SQL_DIR / "schema.sql").read_text().lower()
        self.assertNotIn("invoice_total", txt)


if __name__ == "__main__":
    unittest.main()
