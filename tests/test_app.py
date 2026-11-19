import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import app
from page_framework import render_information_page


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
                INSERT INTO addresses VALUES ('68723345', '171 Manor Way', '', 'Lincolnshire', '', '', 'Scotland', 'Industrial Estate', 'PJ2 6KR');
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

    def test_details_section_shows_source_values_address_and_network_tooltip(self):
        sections = app.load_meter_sections("68723345")
        self.assertEqual(sections[0].title, "Details")
        self.assertEqual(sections[0].state, "data")
        fields = {field.label: field for field in sections[0].fields}
        self.assertEqual(fields["MPRN"].value, "68723345")
        self.assertEqual(fields["Status"].value, "L")
        self.assertEqual(fields["Network"].value, "PRA")
        self.assertEqual(fields["Network"].tooltip, "Vertex Gas Services")
        self.assertEqual(fields["Address"].value,
                         "171 Manor Way, Lincolnshire, Scotland, Industrial Estate, PJ2 6KR")
        html = render_information_page("68723345", sections)
        self.assertIn("Vertex Gas Services", html)
        self.assertIn("171 Manor Way, Lincolnshire, Scotland, Industrial Estate, PJ2 6KR", html)
        self.assertIn("<summary>Details", html)

    def test_details_omits_blank_address_lines_without_empty_commas(self):
        with sqlite3.connect(self.db_path) as db:
            db.execute("UPDATE addresses SET address_line_3 = '', address_line_6 = '' WHERE mprn = '68723345'")
        fields = {field.label: field for field in app.load_meter_sections("68723345")[0].fields}
        self.assertEqual(fields["Address"].value, "171 Manor Way, Industrial Estate, PJ2 6KR")

    def test_details_failure_is_visible_and_distinct_from_no_data(self):
        with sqlite3.connect(self.db_path) as db:
            db.execute("DROP TABLE organizations")
        sections = app.load_meter_sections("68723345")
        self.assertEqual(sections[0].title, "Details")
        self.assertEqual(sections[0].state, "failed")
        html = render_information_page("68723345", sections)
        self.assertIn("Failed to load data", html)
        self.assertIn("Details", html)

    def test_search_page_escapes_entered_value(self):
        _, html = app.search_page(value='"<script>')
        self.assertNotIn('<script>', html)


if __name__ == "__main__":
    unittest.main()
