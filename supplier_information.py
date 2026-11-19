"""Supplier section mapping, date classification and rendering data."""

import sqlite3
from datetime import date
from typing import Callable

from page_framework import Section, _parse_date


def supplier_status(record: dict, today: date | None = None) -> str:
    """Classify a supplier record as current, future, or historical."""
    today = today or date.today()
    start = _parse_date(record.get("start_date"))
    end = _parse_date(record.get("end_date"))
    if start is not None and start > today:
        return "future"
    if start is not None and start <= today and (end is None or today <= end):
        return "current"
    return "historical"


def load_supplier_information(mprn: str, open_database: Callable[[], sqlite3.Connection]) -> Section:
    """Load supplier records for one MPRN; database failure stays section-local."""
    try:
        with open_database() as db:
            records = [dict(row) for row in db.execute("""
                SELECT sh.supplier_short_code AS supplier_code,
                       COALESCE(o.org_name, sh.supplier_short_code) AS supplier_name,
                       sh.efd AS start_date, sh.etd AS end_date
                FROM supplier_history AS sh
                LEFT JOIN organizations AS o ON o.short_code = sh.supplier_short_code
                WHERE sh.mprn = ?
            """, (mprn,)).fetchall()]
    except sqlite3.Error:
        return Section("Supplier Information", "failed", record_mode="supplier")

    if not records:
        return Section("Supplier Information", "no_data", record_mode="supplier")

    for record in records:
        record["status"] = supplier_status(record)
    records.sort(key=lambda item: _parse_date(item.get("start_date")) or date.min, reverse=True)
    current = next((record for record in records if record["status"] == "current"), None)
    return Section("Supplier Information", "data", records=records,
                   record_mode="supplier", current_record=current)
