# Gas enquiry SQLite database and MPRN search app

Build the database from the CSV files in `data/` with `python3 scripts/create_database.py`, then start the app using `python3 app.py`. Open <http://127.0.0.1:8000>.

## Meter Information page framework

`page_framework.py` provides reusable `Section` and `Field` models and common rendering behaviour. Populated sections are expanded by default; sections with no data are omitted; failed sections remain visible with **Failed to load data**. The meter route retrieves sections independently so a failure does not hide other information.

The **Details** section appears first and contains the exact searched MPRN, source Status, Network code and Address. Network Name is available as the Network field tooltip only. Address lines 1–7 are joined in source order with comma separators, omitting blank lines. Status is not translated or otherwise transformed.

Date-bounded records use inclusive Start Date/End Date checks. Current records appear first; historical records are in a collapsed, expandable disclosure ordered newest to oldest, with no pagination. Tooltip text can be attached to a field. Layout adapts to narrow viewports down to 240 px. No last-updated timestamp or export control is included.

Run tests with `python3 -m unittest discover -s tests`.
