# Gas enquiry SQLite database and MPRN search app

Build the database from the CSV files in `data/`:

```bash
python3 scripts/create_database.py
```

Start the web app with `python3 app.py`, then open <http://127.0.0.1:8000>. A successful exact MPRN lookup redirects directly to Meter Information.

## Meter Information page framework

`page_framework.py` provides reusable `Section` and `Field` models and common rendering behaviour. Populated sections are expanded by default; sections with no data are omitted; failed sections remain visible with **Failed to load data**. The meter route retrieves Details, Meter Point Information, Address and Supplier independently, so a failed section does not hide the rest of the page.

Date-bounded records use inclusive Start Date/End Date checks. Current records appear first; historical records are in a collapsed, expandable disclosure ordered newest to oldest, with no pagination. Tooltip text can be attached to a field and is exposed to keyboard and pointer users. Layout adapts to narrow viewports down to 240 px. No last-updated timestamp or export control is included.

Run tests with:

```bash
python3 -m unittest discover -s tests
```

## Database tables

- `mprn` — MPRN, network and status
- `organizations` — organization codes and names
- `smp_info` — meter-point information
- `supplier_history` — supplier periods for each MPRN
- `addresses` — MPRN addresses and postcodes
- `status_reference`, `dpi_master`, `frequency_master` — reference data

MPRNs are stored as text and compared with SQL equality for exact-match behaviour.
