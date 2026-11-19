import sqlite3
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

import app
from page_framework import render_information_page
from supplier_information import load_supplier_information, supplier_status


class SupplierInformationTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "test.sqlite3"
        with sqlite3.connect(self.db_path) as db:
            db.executescript("""
                CREATE TABLE supplier_history (
                    id INTEGER PRIMARY KEY, mprn TEXT, supplier_short_code TEXT, efd TEXT, etd TEXT
                );
                CREATE TABLE organizations (short_code TEXT PRIMARY KEY, org_name TEXT);
                INSERT INTO organizations VALUES ('AAA', 'Alpha Gas Ltd');
                INSERT INTO organizations VALUES ('BBB', 'Beta Energy');
                INSERT INTO organizations VALUES ('CCC', 'Central Supply');
                INSERT INTO supplier_history VALUES (1, '12345', 'AAA', '20100101', '20191231');
                INSERT INTO supplier_history VALUES (2, '12345', 'BBB', '20200101', '20261231');
                INSERT INTO supplier_history VALUES (3, '12345', 'CCC', '20270101', NULL);
            """)
        self.patch = patch.object(app, "DB_PATH", self.db_path)
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self.tempdir.cleanup()

    def test_supplier_status_inclusive_boundaries_and_future(self):
        today = date(2026, 11, 19)
        self.assertEqual(supplier_status({"start_date": "20261119", "end_date": "20261119"}, today), "current")
        self.assertEqual(supplier_status({"start_date": "20261120", "end_date": None}, today), "future")
        self.assertEqual(supplier_status({"start_date": "20200101", "end_date": "20261118"}, today), "historical")
        self.assertEqual(supplier_status({"start_date": "20200101", "end_date": None}, today), "current")

    def test_current_supplier_and_history_are_presented_in_latest_start_order(self):
        section = load_supplier_information("12345", app.open_database)
        self.assertEqual(section.title, "Supplier Information")
        self.assertEqual(section.state, "data")
        self.assertEqual(section.current_record["supplier_code"], "BBB")
        html = render_information_page("12345", [section], date(2026, 11, 19))
        self.assertIn("Alpha Gas Ltd", html)
        self.assertIn("Beta Energy", html)
        self.assertIn("Current", html)
        self.assertIn("Future", html)
        self.assertIn("01/01/2027", html)
        self.assertLess(html.index("CCC"), html.index("BBB", html.index("Show Supplier history")))

    def test_failed_supplier_query_remains_visible(self):
        with sqlite3.connect(self.db_path) as db:
            db.execute("DROP TABLE supplier_history")
        section = load_supplier_information("12345", app.open_database)
        html = render_information_page("12345", [section])
        self.assertEqual(section.state, "failed")
        self.assertIn("Failed to load data", html)
        self.assertIn("Supplier Information", html)

    def test_supplier_name_interaction_is_keyboard_accessible(self):
        section = load_supplier_information("12345", app.open_database)
        html = render_information_page("12345", [section], date(2026, 11, 19))
        self.assertIn('class="supplier-code" aria-label="Supplier code BBB; supplier name Beta Energy"', html)
        self.assertIn("supplier-code:focus .supplier-name-value", html)


if __name__ == "__main__":
    unittest.main()
