#!/usr/bin/env python3
"""Build the complete gas-enquiry SQLite database from the supplied CSV files."""

import csv
import sqlite3
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
DB_PATH = DATA_DIR / "gas_enquiry.sqlite3"

DATASETS = {
    "dummy_data_mprn.csv": "mprn",
    "dummy_data_org.csv": "organizations",
    "dummy_data_smp_info.csv": "smp_info",
    "dummy_data_supplier.csv": "supplier_history",
    "dummy_data_address.csv": "addresses",
    "dummy_data_status_reference.csv": "status_reference",
    "dummy_data_dpi_master.csv": "dpi_master",
    "dummy_data_frequency_master.csv": "frequency_master",
}


def rows_from_csv(filename: str):
    path = DATA_DIR / filename
    if not path.exists():
        raise SystemExit(f"Missing required CSV: {path}")
    with path.open("r", newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames is None:
            raise SystemExit(f"CSV has no header: {path}")
        rows = []
        for line_number, row in enumerate(reader, start=2):
            rows.append({key: (value or "").strip() for key, value in row.items()})
            if line_number and not any(rows[-1].values()):
                raise SystemExit(f"Blank row at {path}:{line_number}")
        return reader.fieldnames, rows


def table(connection: sqlite3.Connection, name: str, sql: str, filename: str,
          insert_sql: str, value_mapper=lambda row: tuple(row.values())):
    connection.execute(f"DROP TABLE IF EXISTS {name}")
    connection.execute(sql)
    headers, rows = rows_from_csv(filename)
    connection.executemany(insert_sql, [value_mapper(row) for row in rows])
    print(f"  {name}: {len(rows)} rows")


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as db:
        db.execute("PRAGMA foreign_keys = ON")

        table(db, "organizations", """
            CREATE TABLE organizations (
                short_code TEXT PRIMARY KEY,
                org_name TEXT NOT NULL
            )
        """, "dummy_data_org.csv",
            "INSERT INTO organizations (short_code, org_name) VALUES (?, ?)",
            lambda r: (r["short code"], r["org name"]))

        table(db, "mprn", """
            CREATE TABLE mprn (
                mprn TEXT PRIMARY KEY,
                network TEXT NOT NULL REFERENCES organizations(short_code),
                status TEXT NOT NULL REFERENCES status_reference(indicator)
            )
        """, "dummy_data_mprn.csv",
            "INSERT INTO mprn (mprn, network, status) VALUES (?, ?, ?)",
            lambda r: (r["MPRN"], r["Network"], r["Status"]))

        table(db, "status_reference", """
            CREATE TABLE status_reference (
                indicator TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """, "dummy_data_status_reference.csv",
            "INSERT INTO status_reference (indicator, value) VALUES (?, ?)",
            lambda r: (r["indicator"], r["value"]))

        table(db, "dpi_master", """
            CREATE TABLE dpi_master (
                indicator TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """, "dummy_data_dpi_master.csv",
            "INSERT INTO dpi_master (indicator, value) VALUES (?, ?)",
            lambda r: (r["indicator"], r["value"]))

        table(db, "frequency_master", """
            CREATE TABLE frequency_master (
                indicator TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """, "dummy_data_frequency_master.csv",
            "INSERT INTO frequency_master (indicator, value) VALUES (?, ?)",
            lambda r: (r["indicator"], r["value"]))

        table(db, "addresses", """
            CREATE TABLE addresses (
                mprn TEXT PRIMARY KEY REFERENCES mprn(mprn),
                address_line_1 TEXT,
                address_line_2 TEXT,
                address_line_3 TEXT,
                address_line_4 TEXT,
                address_line_5 TEXT,
                address_line_6 TEXT,
                address_line_7 TEXT,
                postcode TEXT
            )
        """, "dummy_data_address.csv",
            "INSERT INTO addresses VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            lambda r: (r["MPRN"], r["Address Line 1"], r["Address Line 2"],
                       r["Address Line 3"], r["Address Line 4"], r["Address Line 5"],
                       r["Address Line 6"], r["Address Line 7"], r["postcode"]))

        table(db, "supplier_history", """
            CREATE TABLE supplier_history (
                id INTEGER PRIMARY KEY,
                mprn TEXT NOT NULL REFERENCES mprn(mprn),
                supplier_short_code TEXT NOT NULL REFERENCES organizations(short_code),
                ef d TEXT,
                etd TEXT
            )
        """.replace("ef d", "efd"), "dummy_data_supplier.csv",
            "INSERT INTO supplier_history (mprn, supplier_short_code, efd, etd) VALUES (?, ?, ?, ?)",
            lambda r: (r["MPRN"], r["supplier short code"], r["EFD"], r["ETD"] or None))

        table(db, "smp_info", """
            CREATE TABLE smp_info (
                mprn TEXT PRIMARY KEY REFERENCES mprn(mprn),
                confirmation_reference TEXT,
                confirmation_efd TEXT,
                market_sector_code TEXT,
                meter_link_code TEXT,
                meter_class TEXT,
                interruption_contract TEXT,
                network_project TEXT,
                network_indicator TEXT,
                network_efd TEXT,
                network_etd TEXT,
                ldz_id TEXT,
                exit_zone TEXT,
                network_owner_efd TEXT,
                priority_consumer TEXT,
                reading_frequency TEXT,
                meter_read_batch_frequency TEXT,
                bypass_fitted TEXT,
                twinstream_indicator TEXT,
                csep_id TEXT,
                shared_smp_indicator TEXT,
                asp_name TEXT,
                registration_active_date TEXT
            )
        """, "dummy_data_smp_info.csv",
            "INSERT INTO smp_info VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            lambda r: (r["MPRN"], r["Confirmation Reference"], r["Confimration EFD"],
                       r["Market Sector Code"], r["Meter Link Code"], r["class"],
                       r["interruption contract"], r["network project"], r["network indicator"],
                       r["network EFD"], r["network ETD"], r["LDZ ID"], r["Exit zone"],
                       r["Network owner EFD"], r["Priority consumer"], r["reading frequency"],
                       r["meter read batch frequency"], r["bypass fitted"],
                       r["twinstream indicator"], r["CSEP ID"], r["shared SMP indicator"],
                       r["ASP name"], r["registration active date"]))

        db.execute("CREATE INDEX idx_mprn_network ON mprn(network)")
        db.execute("CREATE INDEX idx_supplier_history_mprn ON supplier_history(mprn)")
        db.execute("CREATE INDEX idx_addresses_postcode ON addresses(postcode)")

    print(f"Created database: {DB_PATH}")


if __name__ == "__main__":
    main()
