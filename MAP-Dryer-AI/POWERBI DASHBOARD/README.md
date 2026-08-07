# MAP Dryer AI — Power BI Dashboard

Two-page Power BI report for the OCP soluble MAP fertilizer dryer, reading
completed model outputs from PostgreSQL over **DirectQuery**.

```
POWERBI DASHBOARD/
├── MAP Dryer AI Dashboard.pbip            ← open THIS in Power BI Desktop
├── MAP Dryer AI Dashboard.SemanticModel/  ← tables, relationship, measures (TMDL)
├── MAP Dryer AI Dashboard.Report/         ← the two report pages (PBIR, 1600×900)
├── sql/bootstrap_base_schema.sql          ← base tables/functions (fresh machine)
├── sql/upgrade_5s_schema.sql              ← 5-second multi-rate extension
├── sql/create_powerbi_views.sql           ← legacy reference DDL (pre-5s naming)
├── preview/                               ← HTML/PNG page previews from live SQL
├── backup_report_pages_20260806/          ← pages before the template rebuild
├── gi.pbix                                ← earlier stub kept for reference
├── README.md
└── IMPLEMENTATION_REPORT.md
```

The two report pages are generated from
`tools/generate_powerbi_report.py` and mirror the reference templates in
`resources/dashboard_templates/` (dark-green 86-px navigation rail,
pill-shaped status controls, full-card heatmap coloring). Re-running the
generator is deterministic; layout previews rendered from the live SQL
views are produced by `tools/render_dashboard_preview.py` into
`preview/`. `tools/validate_report_fields.py` checks every visual's field
references against the semantic model.

## Division of responsibility

| Layer | Responsibility |
|---|---|
| `realtime_pipeline` (Python) | Reads observations, runs the window-feature moisture model and the process-only anomaly/diagnosis models, **writes everything into PostgreSQL every 5 s** (`realtime_service.py`) |
| PostgreSQL | Stores `dryer_map`, `dryer_model_outputs`, `dryer_abnormal_variables`; exposes `vw_dryer_dashboard_powerbi`, `vw_dryer_contributors_powerbi`, `vw_dryer_lab_samples`, `vw_dryer_anomaly_events`, `vw_dryer_latest` |
| Power BI (this folder) | **Reads the views only** over DirectQuery with 60-second automatic page refresh. It never loads the joblib models and never executes inference. Data acquisition (5 s) is deliberately faster than report rendering (60 s); the freshness pill reflects ingest age |

## Prerequisites

1. **Power BI Desktop** (2024-Q4 or later so `.pbip` with TMDL + PBIR is supported).
   Enable both preview features under *File → Options → Preview features* if
   your version still lists them: “Power BI Project (.pbip) save option” and
   “Store reports using enhanced metadata format (PBIR)”.
2. **PostgreSQL connectivity**: recent Power BI Desktop ships the PostgreSQL
   connector (Npgsql) built in. If *Get data → PostgreSQL database* reports a
   missing provider, install [Npgsql](https://github.com/npgsql/npgsql/releases)
   (choose the GAC installation option) and restart Desktop.
3. A reachable PostgreSQL server containing the `MAP_DRYER` database populated
   by `realtime_pipeline`.

## Step 0 — verify the database contract (once, before first open)

From the repository root, with the `realtime_pipeline` virtual environment:

```powershell
python realtime_pipeline/src/verify_powerbi_views.py
```

This connects using `realtime_pipeline/.env`, confirms both views exist,
lists their physical columns against the names the semantic model expects,
and prints row counts and the latest timestamp.

* **View missing** → run `sql/create_powerbi_views.sql` (for example in psql
  or pgAdmin), then re-run the verification.
* **Column name differs** → edit the matching `sourceColumn:` line in
  `MAP Dryer AI Dashboard.SemanticModel/definition/tables/*.tmdl`
  (one line per column; the model was written so this is the only place a
  physical name appears).
* **Zero rows** → start `python realtime_pipeline/src/realtime_service.py`.

## Opening and connecting

1. Double-click `MAP Dryer AI Dashboard.pbip`.
2. The model targets server `localhost:5432`, database `MAP_DRYER`
   (from `realtime_pipeline/.env.example`). If your database is elsewhere,
   change *only* the parameters: *Transform data → Edit parameters* →
   `DB_Server` (format `host:port`) and `DB_Database`.
3. On first refresh Desktop asks for credentials. Choose **Database**
   authentication, user `postgres`, and enter the PostgreSQL password.
   **Credentials are stored in Power BI Desktop's encrypted credential store
   on your machine — never in this repository.** Nothing in this folder
   contains the password; do not add it to any committed file.
4. If PostgreSQL runs on another computer, `localhost` will not reach it:
   set `DB_Server` to that machine's hostname/IP, and make sure PostgreSQL
   accepts the connection (`listen_addresses` in `postgresql.conf` and a
   `pg_hba.conf` entry for your client address).

Encryption note: local development servers usually have SSL disabled; if
Desktop shows an encryption warning, choose the unencrypted connection for
`localhost` only.

## Refresh behavior (60-second cadence)

* The model is **pure DirectQuery** — every visual query goes to PostgreSQL,
  so a refresh always returns whatever `realtime_pipeline` last inserted.
* Both pages carry an **automatic page refresh** configuration of **60 s**
  (matching `REPLAY_INTERVAL_SECONDS=60`). To confirm in Desktop: click the
  page canvas → *Format page → Page refresh* → On, Auto page refresh,
  1 minute. Desktop honors this while the report is open.
* **Manual validation:** *Home → Refresh* (or F5 on the page) after the
  replay service has inserted a new row; the “LAST DATABASE UPDATE” card and
  the trend charts must advance by one minute.
* The header “FEED STATUS” card computes freshness from the latest SQL
  timestamp: **LIVE** (≤ 3 min, green), **STALE · n min** (amber ≤ 10 min,
  red beyond), **NO DATA** (gray) — so operators can tell a healthy feed from
  a stale one regardless of refresh cadence.

### Publishing to the Power BI Service (optional)

* Publish from Desktop (*Home → Publish*) to a workspace.
* Because PostgreSQL is on a private machine, the Service needs an
  **on-premises data gateway** installed on a machine that can reach the
  database, with a PostgreSQL data source mapped to the same server/database
  and credentials entered in the gateway configuration.
* **Automatic page refresh at 60 s in the Service requires DirectQuery (met)
  and a workspace on Premium/Fabric capacity**; capacity admins can cap the
  minimum interval. On shared (Pro) capacity the minimum automatic page
  refresh interval is 30 minutes — a true 60-second cadence in the Service is
  only available on capacity. This is a Power BI licensing limitation, not a
  defect of this report.

## Report contents

**Page 1 — Operations Overview**: header with latest DB timestamp + live/stale
indicator + connection label; six KPI cards (predicted moisture, laboratory
moisture, absolute error, anomaly score, anomaly status, severity); moisture
trend (dense model predictions vs sparse laboratory results, anomalous points
overlaid in red); current operating assessment; seven process-variable cards
with engineering units; operator guidance (diagnosis, possible causes,
recommended verification) with an explicit decision-support disclaimer.

**Page 2 — Diagnostics & Root Cause**: time-window/severity/subsystem/status
slicers; anomaly-score timeline with the One-Class SVM decision boundary at 0
(scores below 0 are anomalous — the model's real threshold, not an invented
one); selected-event summary; ranked abnormal contributors bar chart (top 4,
red = HIGH variable severity, amber otherwise) fed by the one-to-many
Timestamp relationship, with an explicit empty-state message; possible causes
and recommended verification cards; recent-events table (export filtered rows
via the visual's `···` menu → *Export data*).

Dynamic coloring: green `#00843D` = normal, amber `#E8A013` = LOW/MEDIUM,
red `#C8102E` = HIGH/ANOMALY, gray `#8A9299` = unavailable/UNCLASSIFIED/
DATA_QUALITY. Severity `CRITICAL` is mapped red for completeness but the
diagnosis engine intentionally never assigns it (statistical, not safety,
limits). Color is never the only indicator — every state is also shown as text.

## Known limitations

* Laboratory moisture is sparse; its KPI card shows the **latest non-blank**
  laboratory result, which can be older than the latest prediction.
* Severity/status vocabularies are those written by `realtime_pipeline`:
  NORMAL, LOW, MEDIUM, HIGH, DATA_QUALITY, UNCLASSIFIED.
* No moisture target band is drawn: no approved specification limit exists in
  the repository configuration, and inventing one was explicitly out of scope.
* DirectQuery disables some DAX/modeling conveniences (no calculated tables);
  all measures were written DirectQuery-safe.
* `gi.pbix` is the earlier single-page stub; it is superseded by the `.pbip`
  project but left untouched.
