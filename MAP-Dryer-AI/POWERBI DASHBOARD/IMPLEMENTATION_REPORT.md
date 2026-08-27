# Power BI Dashboard — Implementation Report

> **Superseded in part — see “2026-08-07 · 5-second multi-rate upgrade”
> at the end of this file.** Sections below describe the original
> Power BI-only implementation of 2026-08-05 and are kept for history.

Date: 2026-08-05 · Scope: Power BI layer only. No model, feature-engineering,
`realtime_pipeline`, or SQL-ingestion code was modified.

## 1. Files created / modified

**Created**

| Path | Purpose |
|---|---|
| `POWERBI DASHBOARD/MAP Dryer AI Dashboard.pbip` | Project entry point |
| `POWERBI DASHBOARD/MAP Dryer AI Dashboard.SemanticModel/` | TMDL semantic model: `definition.pbism`, `.platform`, `definition/{database,model,expressions,relationships}.tmdl`, `definition/tables/vw_dryer_dashboard_powerbi.tmdl`, `definition/tables/vw_dryer_contributors_powerbi.tmdl` |
| `POWERBI DASHBOARD/MAP Dryer AI Dashboard.Report/` | PBIR report: `definition.pbir`, `.platform`, `definition/{report,version}.json`, `definition/pages/pages.json`, 2 `page.json`, 37 `visual.json`, OCP industrial theme + base theme |
| `POWERBI DASHBOARD/sql/create_powerbi_views.sql` | Reference DDL — run only if a view is missing |
| `realtime_pipeline/src/verify_powerbi_views.py` | Live schema/contract verification script (same style/env handling as the existing pipeline test scripts) |
| `POWERBI DASHBOARD/README.md` | Operating / connection / publishing guide |
| `POWERBI DASHBOARD/IMPLEMENTATION_REPORT.md` | This report |

**Modified**

* `.gitignore` — ignore Power BI Desktop local state (`.pbi/localSettings.json`, `.pbi/cache.abf`, `*.pbix.bak`).

**Untouched**: `gi.pbix` (superseded stub, kept), all of `realtime_pipeline/`,
`models/`, `notebooks/`, `src/`, `config/`, `data/`.

## 2. PostgreSQL values discovered from the repository

The current safe example uses `DB_HOST=localhost`, `DB_PORT=5432`,
`DB_NAME=MAP_DRYER`, and the least-privilege placeholder
`DB_USER=map_dryer_app`.
These are wired into the model as editable parameters `DB_Server`
(`localhost:5432`) and `DB_Database` (`MAP_DRYER`). The password is **not**
stored in any created file (checked below).

## 3. Environment limitation — read before validating

On this machine, at implementation time:

* **PostgreSQL is not installed or running** (no service, no process, port
  5432 closed, no Docker). The `MAP_DRYER` database evidently lives on the
  machine where `realtime_pipeline` runs.
* **Power BI Desktop is not installed** (no PBIDesktop.exe, no Store package).

Consequently the live checks in the task's validation list (connection, view
row counts, visual rendering, manual refresh pickup) **could not be executed
here** and are packaged instead as a one-command verification
(`python realtime_pipeline/src/verify_powerbi_views.py`) plus the checklist in
§8. No fabricated data was substituted anywhere; the report will show real
rows the moment it is opened against the real database.

## 4. Schemas — what was confirmed vs assumed

**Confirmed from repository source code** (base tables):

* `public.dryer_map`: `"Date"`, `"Time"`, `"Dryer Air Temperature"`,
  `"Cooler Air Temperature"`, `"Air Flow Rate "` **(trailing space)**,
  `"Wet Product Feed Rate"`, `"Product Inlet Temperature"`,
  `"Residence Time"`, `"Vacuum"`, `"Steam Pressure"`, `"Fan Speed"`,
  `"Product Density"`, `"Final Product Temp"`, `"Final Moisture (%H2O)"`.
* `public.dryer_model_outputs`: `"Date"`, `"Time"`,
  `"Predicted Final Moisture"`, `"Prediction Confidence"`,
  `"Anomaly Score"`, `"Anomaly Detected"`, `"Severity"` + five diagnosis
  columns written via `upsert_diagnosis_output` (physical names not present in
  Python sources).
* `public.dryer_abnormal_variables`: snake_case (`event_date`, `event_time`,
  `contribution_rank`, `feature_name`, `observed_value`, …,
  `contribution_score`, `deviation_direction`, `variable_severity`).
* Severity vocabulary (from `diagnosis_engine.py` / `replay_service.py`):
  `NORMAL`, `LOW`, `MEDIUM`, `HIGH`, `DATA_QUALITY`, `UNCLASSIFIED`;
  `CRITICAL` intentionally never assigned.
* The old `gi.pbix` confirms both view names
  (`public.vw_dryer_dashboard_powerbi`, `public.vw_dryer_contributors_powerbi`).

**Assumed pending live verification** (the views' own column aliases — their
DDL exists only inside the database): the friendly names listed in
`verify_powerbi_views.py` (`Timestamp`, `Predicted Moisture`, …,
`Final Product Temperature`; `Contributor Rank`, `Contributor Name`,
`Contribution Score`, …). Each maps to exactly one `sourceColumn:` line in the
TMDL tables, so any mismatch reported by the verify script is a one-line fix.

## 5. Semantic model

* Two DirectQuery tables over the two views (`PostgreSQL.Database(DB_Server,
  DB_Database)`), pure DirectQuery — no import partitions, which keeps
  automatic page refresh eligible.
* Relationship: `vw_dryer_dashboard_powerbi[Timestamp]` **1 → \***
  `vw_dryer_contributors_powerbi[Timestamp]`, single-direction filtering.
* Data types: Timestamp → dateTime; measurements/scores → double
  (`summarizeBy: none` throughout); rank → int64; status/severity/subsystem/
  diagnosis/guidance → string.
* **74 measures** in display folders:
  * *01 Freshness*: Latest Timestamp, Data Freshness Minutes/Label/Color,
    Refresh Cadence Label, Last Update Display.
  * *02 Latest KPIs*: latest predicted / laboratory (latest **non-blank**,
    plus its timestamp) / error / absolute error / anomaly score — raw +
    unit-formatted display variants (unavailable → “—”, never 0) — and Latest
    Anomaly Status / Latest Severity.
  * *03 Diagnosis*: Latest Subsystem / Diagnosis / Possible Causes /
    Recommended Verification (database wording preserved verbatim).
  * *04 Process Variables*: raw + display measures for all 11 process
    variables with data-dictionary units (°C, m³/h, min, mmH2O, bar, rpm,
    kg/L).
  * *05 State Colors*: hex-string measures (green `#00843D` / amber `#E8A013`
    / red `#C8102E` / gray `#8A9299`) for latest and row-context
    status/severity, consumed by field-value conditional formatting.
  * *06 Diagnostics Page*: “Selected …” measures (single-selection aware,
    falling back to the latest event in the filtered window), Anomaly
    Threshold = 0 (the One-Class SVM decision boundary — the model's real
    threshold), Anomaly Score/Predicted Moisture (Anomalous) marker series,
    Anomaly Count, Contributor Count / Empty State / Bar Color.
  * *07 Chart Series*: clean-named averages for legends and table headers.

## 6. Report pages

Both pages 1280×720 (16:9), off-white `#F4F5F2` canvas, white bordered
visual containers with subtle shadow (custom "OCP Industrial" theme), and a
60-second automatic-page-refresh page setting.

**Operations Overview (23 visuals)**: title block; LAST DATABASE UPDATE card;
FEED STATUS card (LIVE/STALE/NO DATA with dynamic color); CONNECTION card
(“DirectQuery · automatic page refresh 60 s”); six KPI cards (status and
severity cards carry field-value color); moisture trend line chart (green
dense predictions, blue sparse laboratory results with markers, red anomalous
points; average-per-timestamp = actual value since the view has one row per
timestamp); CURRENT OPERATING ASSESSMENT multi-row card; seven process cards
with units; MODEL DIAGNOSIS / POSSIBLE CAUSES / RECOMMENDED VERIFICATION
cards; decision-support disclaimer.

**Diagnostics & Root Cause (14 visuals)**: Timestamp *Between* slicer +
Severity/Subsystem/Anomaly Status dropdown slicers; anomaly-score timeline
(score line, red anomalous markers, dashed red threshold at 0); SELECTED
EVENT SUMMARY multi-row card (timestamp, status, score, severity, subsystem,
predicted + laboratory moisture, diagnosis); ranked contributors horizontal
bar chart (top 4 by contribution score, rank in tooltip, red = HIGH variable
severity; cross-filtered from any event selection via the relationship);
explicit empty-state card (“No abnormal contributors recorded for this
selection.”); ANOMALIES IN WINDOW and CONTRIBUTOR ROWS count cards; POSSIBLE
CAUSES and RECOMMENDED VERIFICATION cards; recent-events table (timestamp,
status, score, severity, subsystem, diagnosis; newest first; row selection
cross-filters; CSV export via the visual menu).

## 7. Refresh configuration

* Mode: DirectQuery end-to-end (validated by model definition: both
  partitions `mode: directQuery`).
* `pageRefresh` (60 s) serialized on both pages; the README documents the
  two-click Desktop path (*Format page → Page refresh*) in case a Desktop
  build ignores the serialized setting.
* Service deployment: requires an on-premises data gateway to the PostgreSQL
  machine; 60-second automatic page refresh in the Service additionally
  requires Premium/Fabric capacity (30-minute minimum on Pro shared
  capacity). Documented in the README rather than claimed as working.

## 8. Validation status (honest accounting)

| # | Check | Status |
|---|---|---|
| 1 | PostgreSQL connection with repo-defined values | **Blocked here** (no PostgreSQL on this machine) → `verify_powerbi_views.py` |
| 2 | Both views return rows | **Blocked here** → same script |
| 3 | Columns/types correct | Contract encoded in script + TMDL; script diffs live schema |
| 4 | Timestamp relationship valid | Defined in `relationships.tmdl`; validated on first open |
| 5–6 | Latest-value + non-blank-lab measures | DAX matches the task specification; needs live rows to observe |
| 7 | Contributor filtering | Relationship + cross-filter defaults; needs live rows |
| 8 | Dynamic colors react to real values | Field-value color measures wired to cards/bars |
| 9 | Two pages match the reference hierarchy | Built from the task's structural spec — the two reference PNGs were **not found** in the repository or transfer folder, so the written layout description was followed |
| 10 | Manual refresh picks up a new row | Procedure documented (insert via `insert_one_row.py`, then Refresh) |
| 11 | 60-s refresh configured + documented | Yes (page setting + README licensing caveats) |
| 12 | No mock data | **Confirmed** — model contains zero imported/static tables |
| 13 | Password not committed | **Confirmed** — grep of all created files finds no credential; `.gitignore` extended |
| 14 | No unnecessary rewrites of pipeline/model code | **Confirmed** — only additive file: `verify_powerbi_views.py` |

## 9. Unresolved issues / follow-ups

1. **Run `verify_powerbi_views.py` on the database machine** — it settles
   every schema assumption in §4 in one pass.
2. The five diagnosis column names of `dryer_model_outputs` are only
   discoverable in the live database (`\d public.dryer_model_outputs`); the
   reference DDL marks exactly where to adjust them if needed.
3. First open in Power BI Desktop will prompt for credentials (expected) and
   may re-serialize files (`lineageTag`s, ordering) — a large first diff after
   “Save” is normal for a hand-authored PBIP.
4. The final PBIP pages and exported preview PNGs are the canonical dashboard
   assets; temporary build references are not retained in the archive.

---

# 2026-08-07 · 5-second multi-rate upgrade — Implementation Report

Scope: end-to-end. Multi-rate data processing, model training, 5-second
real-time pipeline, PostgreSQL schema, semantic model, template-faithful
report rebuild, tests, and a live end-to-end demonstration on a local
PostgreSQL 17.5 instance.

## 1. Data architecture (multi-rate contract)

`src/multirate/` is the single source of truth:

| Module | Responsibility |
|---|---|
| `preprocessing.py` | Canonical CSV → **process table** (Timestamp + 9 process variables on the selected 5-s prototype grid, duplicates removed, gaps reported) and **laboratory table** (one row per sparse represented lab timestamp, configured ~2 h apart) |
| `alignment.py` | **Dashboard alignment**: backward as-of join adding `Latest Lab *`, `Lab Result Age (min)`, `Lab Sample Available` (display only, never training targets). **Training alignment**: one supervised row per real lab sample with feature window ending at `t_lab − residence_time(asof) − transport_delay` |
| `window_features.py` | 96 aggregated window features (10 stats × 9 variables + 6 derived physical series × 2 + stability index) — same function for training and inference |
| `instant_features.py` | 15 per-observation features for the anomaly/diagnosis models (no laboratory values needed) |

Verified on the prototype data: training CSV 241,920 process rows /
168 lab samples (exactly 2 h spacing, 0 gaps, 0 duplicates); dashboard CSV
34,560 rows / 24 lab samples.

## 2. Training alignment and model results

`tools/train_5s_models.py` → `models/5s/` (3 quality pipelines, anomaly
model + scaler, `reference_profile.json` v2, `feature_schema.json`,
`training_report.json`). 167 supervised rows (first sample skipped —
insufficient pre-history, reported not fabricated). Chronological
70/15/15 split (117/25/25), `TimeSeriesSplit(4)` grid search, four
candidate families benchmarked per target plus persistence and
training-mean baselines.

Chronological **test-tail** results (25 held-out lab samples):

| Target | Selected | MAE | RMSE | R² | Bias | Max abs err |
|---|---|---|---|---|---|---|
| Final Moisture (%H2O) | Elastic Net | 0.0303 | 0.0355 | 0.909 | −0.0008 | 0.072 |
| Product Density | Gradient Boosting | 0.0030 | 0.0040 | 0.760 | +0.0013 | 0.011 |
| Final Product Temp | Ridge | 0.1733 | 0.2102 | 0.990 | −0.0069 | 0.503 |

Validation-set floor check (moisture): model RMSE 0.0375 vs persistence
0.1913 and training-mean 0.1269. Per-sample test residuals are stored in
`training_report.json` (`test_residuals`) for residual-over-time review.

Anomaly detector: One-Class SVM (nu = 0.02) selected — normal validation
false-positive rate 1.90% and governed injected-scenario detection 97.99%,
versus Isolation Forest at 0.69% and 23.98%, respectively; the decision
function is mapped to a 0–1 display risk
(risk = 1/(1+exp(score/scale)), boundary → 0.5, warning 0.5,
critical 0.8).

## 3. Real-time inference (5-second service)

`realtime_pipeline/src/realtime_service.py` — incremental resume from
`MAX("Date"+"Time")`, idempotent SQL upserts keyed on (Date, Time),
models loaded once, connection reused with bounded reconnect/retry,
explicit transactions, graceful shutdown, per-cycle latency logging with
a >5 s warning, stale-data announcement, configurable poll interval /
replay speed / transport delay. Moisture is predicted on every 5-s row
from the same residence-time-shifted window features used in training;
prediction error exists only where a sparse represented laboratory value exists
(enforced by the views, not recomputed against carried-forward values).
Timestamps are naive plant-local end-to-end (documented; no TZ
conversion). Model version, feature-schema version, inference timestamp
and latency are written with every row.

## 4. SQL layer

* `POWERBI DASHBOARD/sql/bootstrap_base_schema.sql` (**new**) — the base
  tables/functions/compatibility views reconstructed from the pipeline
  sources, so a fresh machine can run everything
  (`python realtime_pipeline/src/bootstrap_database.py` applies it plus
  the 5-s migration).
* `POWERBI DASHBOARD/sql/upgrade_5s_schema.sql` — extends
  `dryer_model_outputs` (Anomaly Risk, versions, latency), adds
  Timestamp expression indexes (plus a partial index for lab as-of
  lookups), extends `vw_dryer_dashboard_powerbi` in place, and creates
  `vw_dryer_lab_samples`, `vw_dryer_anomaly_events`, `vw_dryer_latest`.
* `realtime_pipeline/src/validate_database_state.py` (**new**) — 21
  read-only invariant checks (duplicates, orphans, no-future-lab as-of,
  lab-count consistency, latency stats).
* `realtime_pipeline/src/verify_powerbi_views.py` — updated to the real
  four-view TMDL contract.

## 5. Final report pages

The two canonical 1600×900 PBIR pages are stored directly in the final
dashboard project. Temporary template images, the one-time page-generation
utility and the superseded page backup were removed for archival clarity.

The old 1280×720 pages and theme are superseded; the theme now carries
the template palette (#0B3B2E rail, #087C5B green, #1B918E teal,
#F2A12E amber, #DF5558/#C83F45 reds, #F3F6F4 canvas, #D6E0DC borders,
16-px radius, subtle shadows, Segoe UI).

Semantic model: `tools/generate_powerbi_semantic.py` (idempotent,
sentinel-delimited) maintains the 5-s extension — 91 dashboard
measures + 2 lab + 20 event measures, including latest-value KPIs,
validated-error semantics ("Awaiting next laboratory result"), risk
intensity/bands, centralized heatmap color measures, per-variable
status/colors (bands = training-data quantiles), trend series, and
selected-event context. Freshness is now judged by **ingest age**
(`Inference Timestamp` vs NOW) — the honest liveness signal under a
historical-timestamp replay.

`tools/validate_report_fields.py` (**new**) checks every visual field
reference against the TMDL (105 visuals, 149 references — all resolve)
and the 1600×900 canvas.

`tools/render_dashboard_preview.py` (**new**) renders both pages as
HTML from the **live SQL views** (same geometry, same DAX color logic)
→ `POWERBI DASHBOARD/preview/*.html` + PNG screenshots for visual
comparison against the templates.

## 6. Testing

`python -m pytest tests` — **71 passed** (28 pre-existing diagnostic
tests + 43 new): `tests/test_multirate_preprocessing.py` (schema,
timestamps, sorting, 5-s grid, duplicates, gap reporting, backward-only
fill, lab-table counts, structural blanks),
`tests/test_multirate_alignment.py` (as-of join, lab age monotonicity,
constancy between samples, no future lab, residence shift, window
boundaries, no future process data, one row per sample, exact sparse
targets, skip-not-fabricate), `tests/test_multirate_models.py` (feature
schema = inference schema, rejection of unsorted/missing/non-finite
inputs, chronological split, artifact reload + prediction, anomaly
without lab values, service helpers: prediction with/without history,
resume semantics, risk calibration).

## 7. End-to-end demonstration (executed 2026-08-07, local PostgreSQL 17.5)

No PostgreSQL existed on this machine, so a local user-mode instance was
installed in a local development data directory (PostgreSQL 17.5,
port 5432) and the schema was created from scratch with
`bootstrap_database.py` — proving the repository now runs from a fresh
environment. Flow exercised: dashboard CSV → multirate preprocessing →
window/instant features → quality + anomaly inference → diagnosis →
SQL upserts → DirectQuery views → measures/preview visuals.

Accelerated bulk replay (REPLAY_SPEED=0) of 34,500 rows, then a **real
5-second smoke test** (REPLAY_SPEED=1, 6 cycles — resumed exactly at row
34,501, one new timestamp per cycle, max 188 ms), then a final catch-up
of the remaining 54 rows.

| Metric | Value |
|---|---|
| Processed rows | 34,560 / 34,560 (full dashboard CSV) |
| Laboratory observations | 24 (23 validated — the first sample predates sufficient process history) |
| Anomalous 5-s rows / grouped events | Historical retired-source run; not a current qualification metric |
| Contributor rows | 2,660 |
| Inference latency avg / max | 45.4 ms / 219 ms (smoke test avg 138 ms) |
| Cycles over the 5-s budget | 0 |
| Duplicate rows (process / outputs) | 0 / 0 |
| Process rows without model output | 0 |
| Future lab attached to an earlier row | 0 |
| Latest process timestamp | 2026-08-06 09:59:55 |
| Latest laboratory timestamp | 2026-08-06 08:00:00 (age at head: 119.9 min) |
| Mean validated absolute moisture error | 0.0279 % |
| View contract | all four views match the TMDL (verify_powerbi_views.py) |

Previews rendered from the live views (values above are visible on them):
`POWERBI DASHBOARD/preview/preview_page1_overview.{html,png}` and
`preview_page2_diagnostics.{html,png}`.

## 8. Remaining limitations

1. **Power BI Desktop is not installed here** — the PBIP opens against
   the local database as-is (`DB_Server=localhost:5432`,
   `DB_Database=MAP_DRYER`, trust auth on localhost), but actual visual
   rendering inside Desktop could not be executed on this machine. The
   HTML/PNG previews are faithful layout/value proxies built from the
   same views and color rules, not Desktop screenshots. First open in
   Desktop may re-serialize lineage tags (normal for hand-authored PBIR).
2. 60-second automatic page refresh is the fastest reliably supported
   interval in this configuration; the backend deliberately runs at 5 s
   and the header pill honestly says "AUTO 60 SEC".
3. The local demo PostgreSQL uses trust authentication on localhost
   only — fine for the prototype, not for a shared server. Start it with:
   `& "$env:LOCALAPPDATA\MAP_DRYER_PG\pgsql\bin\pg_ctl.exe" -D "$env:LOCALAPPDATA\MAP_DRYER_PG\data" -l "$env:LOCALAPPDATA\MAP_DRYER_PG\server.log" start`
4. The relative time-window slicer on Page 1 defaults to the full range;
   pick 1 h / 8 h / 24 h in its dropdown (PBIR cannot serialize template-
   style preset pill buttons without bookmarks).

## 9. Commands (fresh environment)

```powershell
python -m pip install -r requirements.txt
python -m pip install -r realtime_pipeline/requirements.txt
python tools/train_5s_models.py                          # models/5s/
# copy realtime_pipeline/.env.example → .env, fill DB_*
python realtime_pipeline/src/bootstrap_database.py       # schema + views
python realtime_pipeline/src/verify_powerbi_views.py     # contract check
python realtime_pipeline/src/realtime_service.py         # 5-s service
python realtime_pipeline/src/validate_database_state.py  # invariants
python tools/validate_report_fields.py                   # PBIR ↔ TMDL
python tools/render_dashboard_preview.py                 # live previews
python -m pytest tests                                   # 71 tests
```
