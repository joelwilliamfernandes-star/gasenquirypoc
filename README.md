# Gas enquiry SQLite database

Run:

```bash
python3 scripts/create_database.py
```

This creates `data/gas_enquiry.sqlite3` from the supplied CSV datasets.

## Tables

- `mprn` — MPRN, network and status
- `organizations` — network and supplier organization codes/names
- `smp_info` — meter-point information
- `supplier_history` — supplier periods for each MPRN
- `addresses` — MPRN addresses and postcodes
- `status_reference` — status indicator values
- `dpi_master` — domestic/industrial indicator values
- `frequency_master` — reading-frequency indicator values

MPRNs are stored as `TEXT` to preserve exact values and support exact-match searches.
