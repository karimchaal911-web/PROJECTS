# MAP Dryer AI — Power BI Dashboard

Two-page Power BI engineering-prototype report for the soluble MAP fertilizer
dryer, reading synthetic replay/model outputs from PostgreSQL over
**DirectQuery**. A visible `PROTOTYPE / REPLAY` indicator prevents the dashboard
from being mistaken for a live plant historian or production control system.

```
POWERBI DASHBOARD/
├── MAP Dryer AI Dashboard.pbip            ← open THIS in Power BI Desktop
├── MAP Dryer AI Dashboard.SemanticModel/  ← tables, relationship, measures (TMDL)
├── MAP Dryer AI Dashboard.Report/         ← the two report pages (PBIR, 1600×900)
├── sql/bootstrap_base_schema.sql          ← base tables/functions (fresh machine)
├── sql/upgrade_5s_schema.sql              ← 5-second multi-rate extension
├── sql/create_powerbi_views.sql           ← legacy reference DDL (pre-5s naming)
├── preview/                               ← canonical PNG page previews
├── README.md
└── IMPLEMENTATION_REPORT.md
```

The two final report pages are stored directly in the canonical PBIP project.
Their one-time template inputs and page-generation utility were removed during
archival cleanup. `tools/render_dashboard_preview.py` produces layout previews,
and `tools/validate_report_fields.py` checks every visual's field references
against the semantic model.

## Division of responsibility

| Layer | Responsibility |
|---|---|
| `realtime_pipeline` (Python) | Replays the canonical dashboard partition on the selected prototype cadence, runs the final 16-feature moisture model and process-only anomaly/diagnosis models, and writes outputs to PostgreSQL (`realtime_service.py`) |
| PostgreSQL | Stores `dryer_map`, `dryer_model_outputs`, `dryer_abnormal_variables`; exposes the KPI, contributor, lab, event, lightweight eight-hour trend, and latest-state views |
| Power BI (this folder) | **Reads the views only** over DirectQuery with 5-second automatic page refresh. It never loads the joblib models and never executes inference; the freshness pill reflects wall-clock inference arrival age |

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

This connects using `realtime_pipeline/.env`, confirms all five semantic views exist,
lists their physical columns against the names the semantic model expects,
and prints row counts and the latest timestamp.

* **View missing** → run `python realtime_pipeline/src/apply_sql_migration.py`,
  then re-run the verification. `create_powerbi_views.sql` is legacy reference
  DDL and must not replace the current five-second views.
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
   authentication, enter the configured read-only Power BI user and its password.
   **Credentials are stored in Power BI Desktop's encrypted credential store
   on your machine — never in this repository.** Nothing in this folder
   contains the password; do not add it to any committed file.
4. If PostgreSQL runs on another computer, `localhost` will not reach it:
   set `DB_Server` to that machine's hostname/IP, and make sure PostgreSQL
   accepts the connection (`listen_addresses` in `postgresql.conf` and a
   `pg_hba.conf` entry for your client address).

Encryption note: the Python configuration exposes `DB_SSLMODE`; local demos may
use a permissive local mode, while deployment should use encrypted and verified
connections where available. TLS has not been qualified by this prototype.

## Refresh behavior (five-second cadence)

* The model is **pure DirectQuery** — every visual query goes to PostgreSQL,
  so a refresh always returns whatever `realtime_pipeline` last inserted.
* Both pages carry an **automatic page refresh** configuration of **5 s**,
  matching `POLL_INTERVAL_SECONDS=5`. To confirm in Desktop: click the page
  canvas → *Format page → Page refresh* → On, Auto page refresh, 5 seconds.
* **Manual validation:** *Home → Refresh* (or F5 on the page) after the
  replay service has inserted a new row; the “LAST DATABASE UPDATE” card and
  the latest event/inference timestamp and trend charts must advance by five
  seconds.
* Freshness is computed from `Inference Timestamp`, so a historical event-time
  replay reports the wall-clock replay/ingest health: **LIVE** (≤2 min),
  **DELAYED** (≤10 min), **STALE**, or **NO DATA**.
  This data-status label is separate from process status and never means that
  the dashboard is connected to a live plant historian.

### Publishing to the Power BI Service (optional)

* Publish from Desktop (*Home → Publish*) to a workspace.
* Because PostgreSQL is on a private machine, the Service needs an
  **on-premises data gateway** installed on a machine that can reach the
  database, with a PostgreSQL data source mapped to the same server/database
  and credentials entered in the gateway configuration.
* A five-second interval in the Service requires DirectQuery (met) and a
  dedicated Fabric/Premium/PPU capacity whose administrator permits that
  minimum. Shared/Pro capacity enforces a 30-minute minimum; this is a service
  capacity limit, not a report defect.

## Report contents

**Page 1 — Operations Overview**: header with prototype/replay identity, latest
DB timestamp and data freshness; six KPI cards (predicted moisture, laboratory
moisture, absolute error, anomaly score, anomaly status, severity); moisture
rolling eight-hour trend (dense predictions vs sparse laboratory results,
anomalous points overlaid in red); current diagnosis context; five process-variable cards
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
  represented laboratory result, which can be older than the latest prediction.
* Five seconds is the replay/inference/visualization choice, not a claim about
  native plant instrumentation or historian sampling.
* Severity/status vocabularies are those written by `realtime_pipeline`:
  NORMAL, LOW, MEDIUM, HIGH, DATA_QUALITY, UNCLASSIFIED.
* The moisture band is a documented training-reference band (rounded p10–p90),
  not an approved product specification or control limit.
* DirectQuery disables some DAX/modeling conveniences (no calculated tables);
  all measures were written DirectQuery-safe.
* `replay_service.py` is a guarded legacy one-minute compatibility path. The
  supported dashboard writer is `realtime_service.py`; the SQL semantic views
  exclude unversioned legacy rows without deleting them.
