# Gas enquiry SQLite database and MPRN search app

Build the database from the CSV files in `data/` with `python3 scripts/create_database.py`, then start locally using `python3 app.py`. Open <http://127.0.0.1:8000>.

## Deploy on PythonAnywhere

The project includes `wsgi.py`, a WSGI entry point for PythonAnywhere. PythonAnywhere does not run the app's local `http.server`; the hosted web app must use its WSGI configuration.

1. Clone this repository into your PythonAnywhere home directory, for example `/home/YOUR_USERNAME/gasenquirypoc`.
2. In a PythonAnywhere Bash console, build the SQLite database from the CSV files:

   ```bash
   cd ~/gasenquirypoc
   python3 scripts/create_database.py
   ```

3. In the PythonAnywhere **Web** tab, create a web app using **Manual configuration** and a Python version supported by your account.
4. Open the WSGI configuration file linked from the Web tab. Replace its contents with the following, changing `YOUR_USERNAME` to your PythonAnywhere username and adjusting the repository path if needed:

   ```python
   import sys
   project_path = "/home/YOUR_USERNAME/gasenquirypoc"
   if project_path not in sys.path:
       sys.path.insert(0, project_path)

   from wsgi import application
   ```

5. In the Web tab, set the source code / working directory to `/home/YOUR_USERNAME/gasenquirypoc` if shown, then click **Reload**.
6. Visit `https://YOUR_USERNAME.pythonanywhere.com`.

The SQLite database path defaults to `data/gas_enquiry.sqlite3` inside the repository. If needed, set `GAS_ENQUIRY_DB` in the WSGI configuration before importing `wsgi` to use a different persistent path. Keep the database and source datasets private if they contain information that should not be publicly accessible. PythonAnywhere account features and free-plan limits can change; consult their current Web-app setup help if the interface differs.

## Features

The page uses `page_framework.py` for shared section behaviour. The **Details** and **Meter Point Information** sections appear first. **Supplier Information** shows the current supplier code and effective dates; hovering or keyboard-focusing the code reveals the supplier name. The expandable Supplier history contains the timeline, ordered by Effective From Date from latest to oldest, with dates formatted as `DD/MM/YYYY`. Sections load independently: absent data is omitted and an unavailable source is shown as **Failed to load data**. Layout adapts to narrow viewports down to 240 px.

Run tests with `python3 -m unittest discover -s tests`.
