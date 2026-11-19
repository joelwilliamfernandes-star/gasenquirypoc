# Gas enquiry sample database

This repository includes `data/dummy_data.csv` and a Python standard-library script that builds a SQLite database from it.

## Build the database

From the repository root, run:

```bash
python3 scripts/create_database.py
```

This creates `data/gas_enquiry.sqlite3` with an `organizations` table:

- `id` — generated integer primary key
- `short_code` — source `short code`
- `org_name` — source `org name`

The source contains repeated rows; they are preserved as supplied. To choose another input or output path, pass `--csv` and/or `--db`.

**MPRN search is not supported by this dataset yet:** the CSV contains organization short codes and names, but no MPRNs or meter-point information. Those data fields will be needed to implement and populate the exact-match MPRN search database.
