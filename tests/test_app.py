import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import app


class MprnLookupTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "test.sqlite3"
        with sqlite3.connect(self.db_path) as db:
            db.executescript("""
                CREATE TABLE mprn (mprn TEXT PRIMARY KEY, network TEXT, status TEXT);
                CREATE TABLE organizations (short_code TEXT PRIMARY KEY, org_name TEXT);
                CREATE TABLE status_reference (indicator TEXT PRIMARY KEY, value TEXT);
                CREATE TABLE smp_info (
                    mprn TEXT PRIMARY KEY, confirmation_reference TEXT, confirmation_efd TEXT,
                    market_sector_code TEXT, meter_link_code TEXT, meter_class TEXT,
                    interruption_contract TEXT, network_project TEXT, network_indicator TEXT,
                    network_efd TEXT, network_etd TEXT, ldz_id TEXT, exit_zone TEXT,
                    network_owner_efd TEXT, priority_consumer TEXT, reading_frequency TEXT,
                    meter_read_batch_frequency TEXT, bypass_fitted TEXT, twinstream_indicator TEXT,
                    csep_id TEXT, shared_smp_indicator TEXT, asp_name TEXT, registration_active_date TEXT
                );
                CREATE TABLE addresses (
                    mprn TEXT PRIMARY KEY, address_line_1 TEXT, address_line_2 TEXT,
                    address_line_3 TEXT, address_line_4 TEXT, address_line_5 TEXT,
                    address_line_6 TEXT, address_line_7 TEXT, postcode TEXT
                );
                CREATE TABLE supplier_history (
                    id INTEGER PRIMARY KEY, mprn TEXT, supplier_short_code TEXT, efd TEXT, etd TEXT
                );
                INSERT INTO mprn VALUES ('68723345', 'PRA', 'L');
                INSERT INTO organizations VALUES ('PRA', 'Vertex Gas Services');
                INSERT INTO status_reference VALUES ('L', 'Live');
                INSERT INTO addresses VALUES ('68723345', '171 Manor Way', '', '', '', '', '', '', 'PJ2 6KR');
                INSERT INTO supplier_history VALUES (1, '68723345', 'PRA', '20200101', NULL);
            """)
        self.patch = patch.object(app, "DB_PATH", self.db_path)
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self.tempdir.cleanup()

    def test_exact_lookup_matches_only_full_mprn(self):
        self.assertEqual(app.find_mprn("68723345"), "68723345")
        self.assertIsNone(app.find_mprn("6872334"))
        self.assertIsNone(app.find_mprn("687233450"))

    def test_meter_details_are_loaded_for_exact_mprn(self):
        result = app.meter_information("68723345")
        self.assertEqual(result["mprn"], "68723345")
        self.assertEqual(result["network_name"], "Vertex Gas Services")
        self.assertEqual(result["postcode"], "PJ2 6KR")
        self.assertEqual(result["current_supplier_name"], "Vertex Gas Services")
        self.assertIsNone(app.meter_information("6872334"))

    def test_search_page_escapes_entered_value(self):
        _, html = app.search_page(value='"<script>')
        self.assertNotIn('<script>', html)


if __name__ == "__main__":
    unittest.main()
