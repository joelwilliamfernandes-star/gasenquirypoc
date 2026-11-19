import unittest
from datetime import date

from page_framework import Field, Section, is_current_record, order_current_and_historical, render_information_page


class InformationFrameworkTests(unittest.TestCase):
    def test_inclusive_dates_and_missing_end_date(self):
        today = date(2026, 11, 19)
        self.assertTrue(is_current_record({"start_date": "20261119", "end_date": "20261119"}, today))
        self.assertTrue(is_current_record({"start_date": "2020-01-01", "end_date": None}, today))
        self.assertFalse(is_current_record({"start_date": "20261120", "end_date": None}, today))
        self.assertFalse(is_current_record({"start_date": "20200101", "end_date": "20261118"}, today))

    def test_historical_records_sorted_newest_first_after_current(self):
        records = [
            {"supplier": "old", "start_date": "20100101", "end_date": "20121231"},
            {"supplier": "current", "start_date": "20200101", "end_date": None},
            {"supplier": "newer-history", "start_date": "20150101", "end_date": "20191231"},
        ]
        current, history = order_current_and_historical(records, date(2026, 1, 1))
        self.assertEqual([x["supplier"] for x in current], ["current"])
        self.assertEqual([x["supplier"] for x in history], ["newer-history", "old"])

    def test_framework_hides_empty_and_shows_failed_section(self):
        html = render_information_page("123", [
            Section("Empty", "no_data"),
            Section("Unavailable", "failed"),
            Section("Details", "data", fields=[Field("MPRN", "123")]),
        ])
        self.assertNotIn("Empty", html)
        self.assertIn("Failed to load data", html)
        self.assertIn("Details", html)
        self.assertIn("<details open>", html)

    def test_history_is_collapsed_and_tooltip_is_accessible(self):
        html = render_information_page("123", [Section(
            "Suppliers", "data", records=[
                {"supplier": "historic", "start_date": "20100101", "end_date": "20121231"},
                {"supplier": "current", "start_date": "20200101", "end_date": None},
            ], record_fields=[("supplier", "Supplier", "Source context")],
        )], today=date(2026, 1, 1))
        self.assertIn("<details class=\"history\">", html)
        self.assertIn('role="tooltip"', html)
        self.assertLess(html.index("current"), html.index("Show historical records"))


if __name__ == "__main__":
    unittest.main()
