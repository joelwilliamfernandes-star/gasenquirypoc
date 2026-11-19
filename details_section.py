"""Data mapping for the Meter Information page Details section."""

import sqlite3
from typing import Callable

from page_framework import Field, Section


def load_details_section(meter, open_database: Callable[[], sqlite3.Connection]) -> Section:
    """Fetch MPRN, source Status, Network and ordered address for one MPRN.

    This is deliberately separate from other section reads so a failure in the
    Details source is represented in the Details section, not as missing data.
    """
    try:
        with open_database() as db:
            row = db.execute("""
                SELECT m.mprn, m.status, m.network,
                       network_org.org_name AS network_name,
                       a.address_line_1, a.address_line_2, a.address_line_3,
                       a.address_line_4, a.address_line_5, a.address_line_6,
                       a.address_line_7
                FROM mprn AS m
                LEFT JOIN organizations AS network_org
                  ON network_org.short_code = m.network
                LEFT JOIN addresses AS a ON a.mprn = m.mprn
                WHERE m.mprn = ?
            """, (meter["mprn"],)).fetchone()
    except sqlite3.Error:
        return Section("Details", "failed")

    if row is None:
        return Section("Details", "failed")

    address = ", ".join(
        str(row[f"address_line_{line}"]).strip()
        for line in range(1, 8)
        if row[f"address_line_{line}"] is not None
        and str(row[f"address_line_{line}"]).strip()
    )
    fields = [
        Field("MPRN", row["mprn"]),
        # Status is intentionally displayed exactly as supplied, not looked up.
        Field("Status", row["status"]),
        Field("Network", row["network"], tooltip=row["network_name"]),
        Field("Address", address or None),
    ]
    return Section("Details", "data", fields=fields)
