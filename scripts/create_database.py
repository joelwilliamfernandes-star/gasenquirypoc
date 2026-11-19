#!/usr/bin/env python3
"""Build the gas-enquiry SQLite database from the supplied CSV."""

import argparse
import csv
import sqlite3
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV = REPO_ROOT / "data" / "dummy_data.csv"
DEFAULT_DB = REPO_ROOT / "data" / "gas_enquiry.sqlite3"
EXPECTED_COLUMNS = ("short code", "org name")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="Input CSV path")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="Output SQLite database path")
    args = parser.parse_args()

    args.db.parent.mkdir(parents=True, exist_ok=True)
    with args.csv.open("r", newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames is None or any(column not in reader.fieldnames for column in EXPECTED_COLUMNS):
            raise SystemExit("Input CSV must contain 'short code' and 'org name' columns.")

        rows = []
        for line_number, row in enumerate(reader, start=2):
            short_code = (row.get("short code") or "").strip()
            org_name = (row.get("org name") or "").strip()
            if not short_code or not org_name:
                raise SystemExit(f"Missing short code or org name on CSV line {line_number}.")
            rows.append((short_code, org_name))

    with sqlite3.connect(args.db) as connection:
        connection.execute("DROP TABLE IF EXISTS organizations")
        connection.execute(
            """CREATE TABLE organizations (
                id INTEGER PRIMARY KEY,
                short_code TEXT NOT NULL,
                org_name TEXT NOT NULL
            )"""
        )
        connection.execute(
            "CREATE INDEX idx_organizations_short_code ON organizations(short_code)"
        )
        connection.executemany(
            "INSERT INTO organizations (short_code, org_name) VALUES (?, ?)", rows
        )

    print(f"Created {args.db} with {len(rows)} organization records.")


if __name__ == "__main__":
    main()
