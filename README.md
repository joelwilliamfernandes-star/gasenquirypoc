# Gas enquiry SQLite database and MPRN search app

Build the database from the CSV files in `data/` with `python3 scripts/create_database.py`, then start the app using `python3 app.py`. Open <http://127.0.0.1:8000>.

## Meter Information page

The page uses `page_framework.py` for shared section behaviour. The **Details** section appears first. **Meter Point Information** follows it and displays all 22 defined source fields as read-only values. The four specified date values are formatted as `DD/MM/YYYY`; source date strings in `YYYYMMDD`, `YYYYDDMM`, and ISO date formats are supported. Other values are shown as supplied. Market Sector Code has an accessible tooltip; its current generic wording should be replaced when the approved business explanation is confirmed.

Sections load independently: absent data is omitted and an unavailable source is shown as **Failed to load data**. Supplier history is ordered with current records first and historical records behind an expandable control. Layout adapts to narrow viewports down to 240 px. No last-updated timestamp or export control is included.

Run tests with `python3 -m unittest discover -s tests`.
