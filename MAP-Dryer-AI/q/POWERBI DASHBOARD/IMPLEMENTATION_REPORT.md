# Power BI Dashboard — Implementation Report

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

From `realtime_pipeline/.env.example` (no local `.env` exists on this machine):
`DB_HOST=localhost`, `DB_PORT=5432`, `DB_NAME=MAP_DRYER`, `DB_USER=postgres`.
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
4. The reference layout PNGs (`dashboard_template_page_1_overview.png`,
   `dashboard_template_page_2_diagnostics.png`) were not present anywhere on
   this machine; if pixel-level fidelity to them matters, drop them into the
   repo and compare against the built pages.
