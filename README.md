# Gas enquiry SQLite database and MPRN search app

Build the database from the CSV files in `data/`:

```bash
python3 scripts/create_database.py
```

Start the web app:

```bash
python3 app.py
```

Open <http://127.0.0.1:8000>. Enter a complete MPRN. A successful exact match redirects directly to Meter Information; unknown MPRNs show a no-match message, and database errors show a separate service-unavailable message. Set `GAS_ENQUIRY_DB` to use a database at another path. The app binds to localhost by default; set `HOST` and `PORT` to override.

Run tests with:

```bash
python3 -m unittest discover -s tests
```

## Database tables

- `mprn` — MPRN, network and status
- `organizations` — network and supplier organization codes/names
- `smp_info` — meter-point information
- `supplier_history` — supplier periods for each MPRN
- `addresses` — MPRN addresses and postcodes
- `status_reference` — status indicator values
- `dpi_master` — domestic/industrial indicator values
- `frequency_master` — reading-frequency indicator values

MPRNs are stored as text and compared with SQL equality to ensure exact-match behavior.
