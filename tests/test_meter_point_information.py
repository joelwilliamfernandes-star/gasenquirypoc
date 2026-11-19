import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import app
from meter_point_information import FIELD_SPECS, format_date


class MeterPointInformationTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.path = Path(self.tempdir.name) / "test.sqlite3"
        with sqlite3.connect(self.path) as db:
            db.execute("""CREATE TABLE smp_info (
                mprn TEXT PRIMARY KEY, confirmation_reference TEXT, confirmation_efd TEXT,
                market_sector_code TEXT, meter_link_code TEXT, meter_class TEXT,
                interruption_contract TEXT, network_project TEXT, network_indicator TEXT,
                network_efd TEXT, network_etd TEXT, ldz_id TEXT, exit_zone TEXT,
                network_owner_efd TEXT, priority_consumer TEXT, reading_frequency TEXT,
                meter_read_batch_frequency TEXT, bypass_fitted TEXT, twinstream_indicator TEXT,
                csep_id TEXT, shared_smp_indicator TEXT, asp_name TEXT, registration_active_date TEXT
            )""")
            db.execute("""INSERT INTO smp_info VALUES (
                '68723345','REF-1','20220131','I','Invalid','2','Y','Pipeline Renewal','Y',
                '20200315','20210430','KD','NT2','20010301','N','D','M','Y','N',
                'CSEP-1','N','ASP Ltd','20221205')""")
        self.patch = patch.object(app, "DB_PATH", self.path)
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self.tempdir.cleanup()

    def test_all_22_fields_are_mapped_and_dates_formatted(self):
        sections = app.load_meter_sections("68723345")
        section = sections[1]
        self.assertEqual(section.title, "Meter Point Information")
        self.assertEqual(section.state, "data")
        self.assertEqual(len(section.fields), 22)
        fields = {field.label: field for field in section.fields}
        self.assertEqual(fields["UNC Confirmation Effective Date"].value, "31/01/2022")
        self.assertEqual(fields["Network Project State Date"].value, "15/03/2020")
        self.assertEqual(fields["Network Project End Date"].value, "30/04/2021")
        self.assertEqual(fields["Registration Active Date"].value, "05/12/2022")
        self.assertEqual(fields["Market Sector Code"].value, "I")
        self.assertTrue(fields["Market Sector Code"].tooltip)
        self.assertEqual(fields["Supply Meter Point Class"].value, "2")
        self.assertEqual(fields["Twin Stream Site Indicator"].value, "N")

    def test_source_values_not_in_date_fields_are_unchanged(self):
        fields = {field.label: field for field in app.load_meter_sections("68723345")[1].fields}
        self.assertEqual(fields["Interruption Contract Exists"].value, "Y")
        self.assertEqual(fields["Network Project Name"].value, "Pipeline Renewal")
        self.assertEqual(fields["Reading Frequency"].value, "D")

    def test_date_formatter_handles_source_yyyymmdd_and_yyyyddmm(self):
        self.assertEqual(format_date("20220131"), "31/01/2022")
        self.assertEqual(format_date("20222107"), "21/07/2022")
        self.assertEqual(format_date("2022-07-21"), "21/07/2022")
        self.assertEqual(format_date("not-a-date"), "not-a-date")

    def test_failed_query_remains_a_failed_section(self):
        with sqlite3.connect(self.path) as db:
            db.execute("DROP TABLE smp_info")
        section = app.load_meter_sections("68723345")[1]
        self.assertEqual(section.state, "failed")


if __name__ == "__main__":
    unittest.main()
