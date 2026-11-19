# Gas enquiry SQLite database and MPRN search app

Build the database from the CSV files in `data/` with `python3 scripts/create_database.py`, then start the app using `python3 app.py`. Open <http://127.0.0.1:8000>.

## Meter Information page

The page uses `page_framework.py` for shared section behaviour. The **Details** and **Meter Point Information** sections appear first. **Supplier Information** shows the current supplier code and effective dates; hovering or keyboard-focusing the code reveals the supplier name. The expandable Supplier history contains the complete timeline, ordered by Effective From Date from latest to oldest, with dates formatted as `DD/MM/YYYY`. Current and future records receive corresponding status tags; historical records have no tag.

Sections load independently: absent data is omitted and an unavailable source is shown as **Failed to load data**. Layout adapts to narrow viewports down to 240 px. No last-updated timestamp or export control is included.

Run tests with `python3 -m unittest discover -s tests`.
