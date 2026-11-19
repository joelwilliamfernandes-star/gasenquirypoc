#!/usr/bin/env python3
"""Small standard-library web app for exact MPRN lookup."""

from html import escape
import os
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from page_framework import Field, Section, render_information_page

ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("GAS_ENQUIRY_DB", ROOT / "data" / "gas_enquiry.sqlite3"))


class DatabaseError(Exception):
    """Raised when the database cannot be queried as expected."""


def open_database():
    try:
        connection = sqlite3.connect(DB_PATH, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only = ON")
        return connection
    except sqlite3.Error as error:
        raise DatabaseError from error


def find_mprn(mprn):
    """Return the matched MPRN or None; equality is intentionally exact."""
    try:
        with open_database() as db:
            row = db.execute("SELECT mprn FROM mprn WHERE mprn = ?", (mprn,)).fetchone()
            return row["mprn"] if row else None
    except (sqlite3.Error, DatabaseError) as error:
        raise DatabaseError from error


def meter_information(mprn):
    """Return the legacy flat meter-information mapping used by callers/tests."""
    query = """
        SELECT m.mprn, m.network, network_org.org_name AS network_name,
               m.status, status_ref.value AS status_name,
               si.confirmation_reference, si.confirmation_efd,
               si.market_sector_code, si.meter_link_code, si.meter_class,
               si.interruption_contract, si.network_project, si.network_indicator,
               si.network_efd, si.network_etd, si.ldz_id, si.exit_zone,
               si.network_owner_efd, si.priority_consumer, si.reading_frequency,
               si.meter_read_batch_frequency, si.bypass_fitted,
               si.twinstream_indicator, si.csep_id, si.shared_smp_indicator,
               si.asp_name, si.registration_active_date,
               a.address_line_1, a.address_line_2, a.address_line_3,
               a.address_line_4, a.address_line_5, a.address_line_6,
               a.address_line_7, a.postcode,
               supplier.supplier_short_code AS current_supplier_code,
               supplier_org.org_name AS current_supplier_name
        FROM mprn AS m
        LEFT JOIN organizations AS network_org ON network_org.short_code = m.network
        LEFT JOIN status_reference AS status_ref ON status_ref.indicator = m.status
        LEFT JOIN smp_info AS si ON si.mprn = m.mprn
        LEFT JOIN addresses AS a ON a.mprn = m.mprn
        LEFT JOIN supplier_history AS supplier
          ON supplier.mprn = m.mprn AND (supplier.etd IS NULL OR supplier.etd = '')
        LEFT JOIN organizations AS supplier_org
          ON supplier_org.short_code = supplier.supplier_short_code
        WHERE m.mprn = ? LIMIT 1
    """
    try:
        with open_database() as db:
            row = db.execute(query, (mprn,)).fetchone()
            return dict(row) if row else None
    except (sqlite3.Error, DatabaseError) as error:
        raise DatabaseError from error


def load_meter_sections(mprn):
    """Load common information sections independently so one failure is isolated."""
    try:
        with open_database() as db:
            meter = db.execute(
                "SELECT mprn, network, status FROM mprn WHERE mprn = ?", (mprn,)
            ).fetchone()
    except sqlite3.Error as error:
        raise DatabaseError from error
    if meter is None:
        return None

    sections = [Section("Details", "data", fields=[
        Field("MPRN", meter["mprn"]),
        Field("Network code", meter["network"]),
        Field("Status code", meter["status"]),
    ])]

    def load_section(title, query, parameters, field_specs=None, record_specs=None):
        try:
            with open_database() as db:
                rows = [dict(row) for row in db.execute(query, parameters).fetchall()]
        except sqlite3.Error:
            sections.append(Section(title, "failed"))
            return
        if not rows:
            sections.append(Section(title, "no_data"))
        elif record_specs:
            sections.append(Section(title, "data", records=rows,
                                    record_fields=record_specs,
                                    start_key="start_date", end_key="end_date"))
        else:
            row = rows[0]
            sections.append(Section(title, "data", fields=[
                Field(label, row.get(key), tooltip) for key, label, tooltip in field_specs
            ]))

    load_section("Meter Point Information", """
        SELECT confirmation_reference, confirmation_efd, market_sector_code,
               meter_link_code, meter_class, interruption_contract, network_project,
               network_indicator, network_efd, network_etd, ldz_id, exit_zone,
               network_owner_efd, priority_consumer, reading_frequency,
               meter_read_batch_frequency, bypass_fitted, twinstream_indicator,
               csep_id, shared_smp_indicator, asp_name, registration_active_date
        FROM smp_info WHERE mprn = ?
    """, (mprn,), field_specs=[
        ("confirmation_reference", "Confirmation reference", None),
        ("confirmation_efd", "Confirmation EFD", None),
        ("market_sector_code", "Market sector code", None),
        ("meter_link_code", "Meter link code", None), ("meter_class", "Class", None),
        ("interruption_contract", "Interruption contract", None),
        ("network_project", "Network project", None), ("network_indicator", "Network indicator", None),
        ("network_efd", "Network EFD", None), ("network_etd", "Network ETD", None),
        ("ldz_id", "LDZ ID", None), ("exit_zone", "Exit zone", None),
        ("network_owner_efd", "Network owner EFD", None),
        ("priority_consumer", "Priority consumer", None),
        ("reading_frequency", "Reading frequency", None),
        ("meter_read_batch_frequency", "Meter read batch frequency", None),
        ("bypass_fitted", "Bypass fitted", None),
        ("twinstream_indicator", "Twinstream indicator", None),
        ("csep_id", "CSEP ID", None), ("shared_smp_indicator", "Shared SMP indicator", None),
        ("asp_name", "ASP name", None),
        ("registration_active_date", "Registration active date", None),
    ])
    load_section("Address", """
        SELECT address_line_1, address_line_2, address_line_3, address_line_4,
               address_line_5, address_line_6, address_line_7, postcode
        FROM addresses WHERE mprn = ?
    """, (mprn,), field_specs=[
        ("address_line_1", "Address line 1", None), ("address_line_2", "Address line 2", None),
        ("address_line_3", "Address line 3", None), ("address_line_4", "Address line 4", None),
        ("address_line_5", "Address line 5", None), ("address_line_6", "Address line 6", None),
        ("address_line_7", "Address line 7", None), ("postcode", "Postcode", None),
    ])
    load_section("Supplier", """
        SELECT sh.supplier_short_code, o.org_name AS supplier_name,
               sh.efd AS start_date, sh.etd AS end_date
        FROM supplier_history AS sh
        LEFT JOIN organizations AS o ON o.short_code = sh.supplier_short_code
        WHERE sh.mprn = ?
    """, (mprn,), record_specs=[
        ("supplier_name", "Supplier", None),
        ("supplier_short_code", "Supplier code", None),
        ("start_date", "Start date", None), ("end_date", "End date", None),
    ])
    return sections


# Kept for compatibility with callers using the original single-section renderer.
LABELS = {
    "mprn": "MPRN", "network": "Network code", "network_name": "Network",
    "status_name": "Status", "confirmation_reference": "Confirmation reference",
    "confirmation_efd": "Confirmation EFD", "market_sector_code": "Market sector code",
    "meter_link_code": "Meter link code", "meter_class": "Class",
    "interruption_contract": "Interruption contract", "network_project": "Network project",
    "network_indicator": "Network indicator", "network_efd": "Network EFD",
    "network_etd": "Network ETD", "ldz_id": "LDZ ID", "exit_zone": "Exit zone",
    "network_owner_efd": "Network owner EFD", "priority_consumer": "Priority consumer",
    "reading_frequency": "Reading frequency", "meter_read_batch_frequency": "Meter read batch frequency",
    "bypass_fitted": "Bypass fitted", "twinstream_indicator": "Twinstream indicator",
    "csep_id": "CSEP ID", "shared_smp_indicator": "Shared SMP indicator",
    "asp_name": "ASP name", "registration_active_date": "Registration active date",
    "address_line_1": "Address line 1", "address_line_2": "Address line 2",
    "address_line_3": "Address line 3", "address_line_4": "Address line 4",
    "address_line_5": "Address line 5", "address_line_6": "Address line 6",
    "address_line_7": "Address line 7", "postcode": "Postcode",
    "current_supplier_code": "Current supplier code", "current_supplier_name": "Current supplier",
}


def page(title, body):
    return """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{}</title><style>
body{{font:1rem/1.5 system-ui,sans-serif;max-width:54rem;margin:2rem auto;padding:0 1rem;color:#172b4d}}
label{{display:block;font-weight:700;margin-bottom:.4rem}}input{{font:inherit;padding:.6rem;width:min(100%,24rem);box-sizing:border-box}}
button{{font:inherit;padding:.6rem 1rem;margin-top:1rem;cursor:pointer}}.message{{padding:.8rem;border-left:4px solid #b42318;background:#fff2f0;margin:1rem 0}}
dl{{display:grid;grid-template-columns:minmax(12rem,1fr) 2fr;gap:.45rem 1rem}}dt{{font-weight:700}}dd{{margin:0;overflow-wrap:anywhere}}
</style></head><body>{}</body></html>""".format(title, body)


def search_page(message="", value="", status=200):
    notice = f'<p class="message" role="alert">{escape(message)}</p>' if message else ""
    body = f"""<h1>Search by MPRN</h1>{notice}<form action="/search" method="post">
<label for="mprn">Complete MPRN</label><input id="mprn" name="mprn" inputmode="numeric" autocomplete="off" required value="{escape(value, quote=True)}">
<button type="submit">Search</button></form>"""
    return status, page("Search by MPRN", body)


def meter_page(info):
    fields = [Field(label, info.get(key)) for key, label in LABELS.items()]
    return render_information_page(info["mprn"], [Section("Meter Point Information", "data", fields=fields)])


class Handler(BaseHTTPRequestHandler):
    def respond(self, status, content, location=None):
        encoded = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'")
        if location:
            self.send_header("Location", location)
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            status, content = search_page()
            self.respond(status, content)
            return
        if path.startswith("/meter/"):
            mprn = path.removeprefix("/meter/")
            try:
                sections = load_meter_sections(mprn)
            except DatabaseError:
                status, content = search_page("The search service is temporarily unavailable. Please try again.", status=503)
                self.respond(status, content)
                return
            if sections is None:
                status, content = search_page("That MPRN was not found. Check the number and try again.", status=404)
                self.respond(status, content)
                return
            self.respond(200, render_information_page(mprn, sections))
            return
        self.respond(404, page("Not found", '<h1>Page not found</h1><p><a href="/">Return to MPRN search</a></p>'))

    def do_POST(self):
        if urlparse(self.path).path != "/search":
            self.respond(404, page("Not found", "<h1>Page not found</h1>"))
            return
        try:
            length = min(int(self.headers.get("Content-Length", "0")), 4096)
            form = parse_qs(self.rfile.read(length).decode("utf-8"), keep_blank_values=True)
            mprn = form.get("mprn", [""])[0].strip()
        except (ValueError, UnicodeDecodeError):
            status, content = search_page("Enter a valid MPRN.", status=400)
            self.respond(status, content)
            return
        if not mprn or not mprn.isascii() or not mprn.isdigit():
            status, content = search_page("Enter a complete MPRN using digits only.", mprn, 400)
            self.respond(status, content)
            return
        try:
            matched = find_mprn(mprn)
        except DatabaseError:
            status, content = search_page("The search service is temporarily unavailable. Please try again.", mprn, 503)
            self.respond(status, content)
            return
        if matched is None:
            status, content = search_page("That MPRN was not found. Check the number and try again.", mprn, 404)
            self.respond(status, content)
            return
        self.respond(303, "", f"/meter/{matched}")

    def log_message(self, fmt, *args):
        super().log_message(fmt, *args)


def main():
    address = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    print(f"Gas enquiry app listening at http://{address}:{port} (database: {DB_PATH})")
    ThreadingHTTPServer((address, port), Handler).serve_forever()


if __name__ == "__main__":
    main()
