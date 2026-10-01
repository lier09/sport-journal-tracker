# Sport Journal Tracker

A Streamlit dashboard for discovering and reviewing new research across sport science, coaching, training, sports medicine, nutrition, environmental physiology, and recovery.

## Run locally

Install Python 3.11+ and Node.js/npm, then run `scripts\\run_app.bat` on Windows. The launcher installs the frontend packages if needed, builds the React interface, and starts the local Python server at `http://127.0.0.1:8765`.

For frontend development, use two terminals from the project root:

```powershell
python api.py
```

```powershell
cd frontend
npm install
npm run dev
```

The Vite development server is at `http://127.0.0.1:5173` and proxies API calls to the local Python server. The API binds to `127.0.0.1` only. Article status, favorites, tags, and notes are written to `data/private_reading_state.sqlite3`, which is ignored by Git; they do not enter the shared article database.

## Journal coverage

`config/journals.csv` contains the original core catalog; `config/journal_expansion.csv` adds 48 titles across coaching, sport analytics and psychology, exercise science, environmental physiology, nutrition, and recovery/rehabilitation. The journal library shows the collection group and whether a title is collected as a whole-journal feed or through a keyword filter.

Expansion titles are discovery sources, not a claim that every resulting record is relevant or that every publisher feed is available. Until an official publisher RSS/API endpoint is individually verified, collection uses Crossref and/or PubMed fallback searches and the source registry marks it as unverified. Broad adjacent journals use explicit sport-related keywords to reduce unrelated records. Internal priority labels (S/A/B/C) are not journal quartiles.

## Data and deployment

The public dashboard is read-only for personal reading fields. The scheduled GitHub workflow refreshes the shared article database; it must not receive a user's local reading-state database. Do not commit API keys or personal account data.

`app.py` retains the previous Streamlit interface for the existing Streamlit deployment. The new React interface is the default local experience; publishing it as a hosted site requires a deployment target that can run the Python API alongside the frontend. No deployment or scheduled collection is started by the local launcher.

First-seen date means the date the tracker first collected a record, not necessarily its publication date. The dashboard displays publication date separately when available.

## Sources

- `config/journals.csv` — core journal catalog.
- `config/journal_expansion.csv` — expanded journal catalog and collection rules.
- `config/journal_source_registry.csv` — publisher-source verification and fallback status.
- `config/publisher_sources.csv` — enabled publisher-specific collectors.
- `src/` — retrieval, filtering, classification, and database logic.
