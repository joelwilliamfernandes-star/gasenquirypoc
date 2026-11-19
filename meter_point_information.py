"""Mapping and display formatting for Meter Point Information."""

import sqlite3
from datetime import date, datetime
from typing import Callable

from page_framework import Field, Section


# Source column, display label, tooltip text. Tooltip wording is intentionally
# generic until the business-approved Market Sector Code explanation is supplied.
FIELD_SPECS = (
    ("confirmation_reference", "Confirmation Reference", None),
    ("confirmation_efd", "UNC Confirmation Effective Date", None),
    ("market_sector_code", "Market Sector Code", "Market sector code supplied by source."),
    ("meter_link_code", "Meter Link Code", None),
    ("meter_class", "Supply Meter Point Class", None),
    ("interruption_contract", "Interruption Contract Exists", None),
    ("network_project", "Network Project Name", None),
    ("network_indicator", "Network Indicator", None),
    ("network_efd", "Network Project State Date", None),
    ("network_etd", "Network Project End Date", None),
    ("ldz_id", "LDZ ID", None),
    ("exit_zone", "Exit Zone", None),
    ("network_owner_efd", "Network Owner EFD", None),
    ("priority_consumer", "Priority Consumer Indicator", None),
    ("reading_frequency", "Reading Frequency", None),
    ("meter_read_batch_frequency", "Meter Read Batch Frequency", None),
    ("bypass_fitted", "Bypass Fitted", None),
    ("twinstream_indicator", "Twin Stream Site Indicator", None),
    ("csep_id", "CSEP ID", None),
    ("shared_smp_indicator", "Shared SMP Indicator", None),
    ("asp_name", "ASP Name", None),
    ("registration_active_date", "Registration Active Date", None),
)

DATE_FIELDS = {
    "confirmation_efd",
    "network_efd",
    "network_etd",
    "registration_active_date",
}


def format_date(value):
    """Format known source date representations as DD/MM/YYYY.

    Source data includes both YYYYMMDD and YYYYDDMM strings. Accept ISO dates
    too, and leave unrecognized source values untouched rather than inventing
    a date interpretation.
    """
    if value is None or not str(value).strip():
        return value
    text = str(value).strip()
    for fmt in ("%Y%m%d", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).strftime("%d/%m/%Y")
        except ValueError:
            pass
    if len(text) == 8 and text.isdigit():
        try:
            return datetime.strptime(text, "%Y%d%m").strftime("%d/%m/%Y")
        except ValueError:
            pass
    return text


def load_meter_point_information(mprn: str, open_database: Callable[[], sqlite3.Connection]) -> Section:
    """Load a meter's 22 read-only fields, isolated from other page sections."""
    columns = ", ".join(FIELD[0] for FIELD in FIELD_SPECS)
    try:
        with open_database() as db:
            row = db.execute(
                f"SELECT {columns} FROM smp_info WHERE mprn = ?", (mprn,)
            ).fetchone()
    except sqlite3.Error:
        return Section("Meter Point Information", "failed")

    if row is None:
        return Section("Meter Point Information", "no_data")

    fields = []
    for key, label, tooltip in FIELD_SPECS:
        value = row[key]
        if key in DATE_FIELDS:
            value = format_date(value)
        fields.append(Field(label, value, tooltip=tooltip))
    return Section("Meter Point Information", "data", fields=fields)
