# Final Technical QA — MAP Dryer AI Dashboard

Date: 2026-08-08  
Verdict: **READY FOR DEMO WITH MINOR LIMITATIONS**

## Executive result

The five-second Python → PostgreSQL → Power BI design is intact. The confirmed
one-minute behavior was traced to two independent causes: the report pages were
configured with legacy 60-second refresh metadata, and the obsolete one-minute
writer was still runnable and had inserted newer, unversioned rows that outranked
the valid five-second stream. Both causes are fixed without deleting retained
historical rows.

The overview was reduced from 69 to 46 visuals and from about 41 to 22
query-bearing visuals. The complete report now contains 86 visuals instead of
109. Its main overview trend uses a purpose-built 5,760-row rolling-eight-hour
view that executed in 16.904 ms during the final test. A 90-second real-time run
inserted 18 consecutive inference cycles at exactly five-second event cadence,
with 29 ms average and 163 ms maximum service latency.

The minor limitation is explicit: final native Power BI source-to-screen timing
and physical Ctrl+click navigation could not be recorded reliably because the
Windows UI automation transport lost focus to the active user desktop. PBIR
actions, destinations, z-order, bounds, field references, DirectQuery objects,
and APR/PT5S settings were validated statically and the live SQL-backed previews
were rendered and visually inspected. A short manual Desktop check is still
recommended on the presentation machine.

## 1. Confirmed issues reported by the user

### 1.1 Buttons were not clickable

- Root cause: the sidebar contained four decorative glyphs but the report had
  only two pages. None of the glyphs had an Action or destination, so they were
  visually misleading rather than functional controls.
- Files/settings: canonical PBIR visual JSON under both page folders.
- Fix: reduced the rail to the two real destinations and placed a transparent
  `actionButton` over each icon on each page. Every button has
  `visualLink.type = PageNavigation`, a valid internal page ID, and a tooltip.
  Obsolete decorative icons were removed.
- Validation: the report validator requires exactly two navigation actions per
  page, both page IDs, unique z/tab order, and in-canvas bounds. All four actions
  pass. No bookmarks are present, so no invalid bookmark state remains.

### 1.2 Automatic refresh was 60 seconds

- Root cause: both generated pages used the old numeric `refreshType=1D` and
  `duration=60D`; the header also queried a constant `AUTO 60 SEC` measure.
- Fix: both pages now use modern PBIR automatic page refresh metadata
  `refreshType='APR'`, `duration='PT5S'`. The header is a static
  `PROTOTYPE / REPLAY` textbox, so it no longer creates a DirectQuery request
  and cannot be mistaken for native plant acquisition.
- Validation: `tools/validate_report_fields.py` fails unless both page files are
  APR/PT5S. Current result: pass on both pages.
- Platform qualification: Power BI Desktop supports a one-second minimum for
  DirectQuery fixed-interval refresh, but actual cycles wait for previous work.
  Shared/Pro service capacity enforces a 30-minute minimum; a true five-second
  service interval needs dedicated Fabric/Premium/PPU capacity and an admin
  policy that permits it. See Microsoft's
  [automatic page refresh documentation](https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-automatic-page-refresh).

### 1.3 One-second refresh was slow

- Root cause: the overview repeatedly queried the full 34k-row dashboard view,
  including a per-row laboratory LATERAL as-of lookup, while also rendering
  duplicate process strips, five separate delta cards, KPI caption cards, and a
  repeated anomaly gauge.
- Fix: added `vw_dryer_overview_trends_powerbi`, restricted to the latest eight
  hours relative to the newest versioned event. It joins only process and model
  rows and deliberately omits the expensive lab as-of lookup. The main chart
  and five tile sparklines use this isolated table. Redundant visuals were
  removed. Five seconds, not one second, is now the supported demo target.
- Measured result: overview query 16.904 ms / 5,760 rows / 2,613 shared-buffer
  hits. The old all-history main trend measured 101.6 ms; even an eight-hour
  filter through the heavy view measured 83.0 ms.

### 1.4 Dashboard was too crowded

- Fixes on Operations Overview: removed four duplicate process-strip charts,
  five KPI-caption query cards, five delta query cards, the duplicate risk
  donut/score/severity group, the ambiguous relative-time slicer, and two fake
  nav icons. The main trend is taller; diagnosis context uses one wide
  multi-row component; critical-variable tiles retain value, state color, and
  eight-hour sparkline.
- Fixes on Diagnostics: shortened titles, clarified filters, retained the
  distinct investigation sequence (timeline → selected event → contributors →
  causes/verification → event table), and turned export into explicit guidance
  rather than a fake button.
- Validation: page 1 is 46 visuals/22 query visuals; page 2 is 40/15. The visual
  performance budgets are enforced in the validator.

### 1.5 Box/card redundancy

- Removed repeated anomaly risk/severity from the former assessment gauge.
- Removed four trends duplicated again inside the process-variable section.
- Removed separate KPI caption query cards and separate per-variable delta
  cards.
- Kept only components that answer different operator questions: current state,
  latest validation, recent trajectory, diagnostic context, and guidance.

### 1.6 Unclear titles

Representative replacements:

- `PREDICTED MOISTURE` → `PREDICTED FINAL MOISTURE`
- `LABORATORY MOISTURE` → `LATEST LAB MOISTURE`
- `VALIDATED ABS ERROR` → `VALIDATED MOISTURE ERROR`
- `ANOMALY SCORE` → `CURRENT ANOMALY RISK`
- `SEVERITY` → `CURRENT ANOMALY SEVERITY`
- `Current operating assessment` → `Current diagnosis context`
- `Ranked abnormal contributors` → `Top abnormal process contributors`
- Timeline and recent-event titles now include thresholds and interaction cues.

### 1.7 Slow page switching

- Root cause: page 1 initialized many redundant DirectQuery visuals and the
  overview charts requested a large/high-cost history through the KPI view.
- Fix: page 1 query visuals fell to 22; overview charts share the lightweight
  un-related eight-hour table; no page bookmarks or hidden visual stacks exist.
  Chart selection cannot alter current KPI cards because the trend table has no
  relationship to the current-state table.
- Result: query work is materially reduced. Native click-to-render latency was
  not safely measurable in the final automation session; see limitations.

## 2. Additional issues discovered

| Severity | Issue/cause | Fix |
|---|---|---|
| Critical | 127 newer one-minute rows had null model/schema/inference metadata and dense lab values. They became the “latest” dashboard rows, inflated labs from 24 to 151, and produced misleading red process cards. | Current dashboard, lab, event, latest, and trend views expose only rows with non-null `Model Version`. Legacy rows remain preserved in base tables. One collision in the final loop upgraded a legacy row, leaving 126 retained and zero exposed. |
| Superseded safety decision | Earlier QA enabled indefinite looping by default. | Final hardening sets `CONTINUOUS_DEMO_MODE=false`; finite replay stops clearly at EOF. Looping is explicit opt-in and every replay cycle is identified as synthetic replay. |
| High | `replay_service.py` could silently restart the incompatible one-minute writer. | Guarded it behind explicit `ENABLE_LEGACY_1MIN_REPLAY=true` and documented `realtime_service.py` as the supported writer. |
| Medium | Critical-variable quantile colors could show HIGH while the overall inference was NORMAL or stale. | Status DAX now gates on freshness and operating state. NORMAL suppresses unnecessary noise; STALE/NO DATA render gray. |
| Medium | Overview history used a NOW-relative slicer even though replay event times are historical. | Removed the slicer; the SQL trend window anchors to the latest versioned event, making replay output deterministic. |
| Medium | `requirements.txt` ended with malformed text (`openpyxlrealtime pipeline dependencies here`) and omitted the test runner. | Corrected `openpyxl`; added `pytest`. |
| Medium | View/report validation did not test refresh, navigation, bounds, z-order, or query budgets. | Expanded both validators and added continuous-history unit tests. |
| Low | SQL-backed HTML previews still advertised 60 seconds and reproduced the crowded layout. | Updated to five seconds, the lightweight trend view, two-item rail, consolidated overview, clarified titles, and stale-state rendering. |

## 3. Performance optimizations

### Visual/query reduction

| Metric | Before | After |
|---|---:|---:|
| Total report visuals | 109 | 86 |
| Page 1 visuals | 69 | 46 |
| Page 1 query-bearing visuals | ~41 | 22 |
| Page 2 query-bearing visuals | ~16 | 15 |

### SQL/query measurements

Final PostgreSQL `EXPLAIN (ANALYZE, BUFFERS)` results:

| Query | Execution | Rows | Shared hits |
|---|---:|---:|---:|
| Latest KPI state | 0.854 ms | 1 | 391 |
| Rolling eight-hour overview | 16.904 ms | 5,760 | 2,613 |
| Anomaly event list | 6.776 ms | 95 | 2,496 |
| Full dashboard count (diagnostic worst case) | 84.914 ms | 1 aggregate | 72,181 |

The heavy dashboard view is retained for correct latest-lab/as-of semantics,
but high-volume overview plots no longer use it. A partial timestamp index on
versioned model rows accelerates restart/latest-stream selection.

### Model/DAX behavior

- New DirectQuery table: `vw_dryer_overview_trends_powerbi` with ten physical
  fields and ten dedicated measures.
- No relationship by design, preventing historical chart interaction from
  recalculating current-state cards.
- Constant refresh label changed from a measure-driven card to a textbox.
- Status measures are centralized and freshness-aware.
- Auto time intelligence remains disabled.

## 4. Refresh and end-to-end test results

Test duration: 90 seconds. Configuration: `POLL_INTERVAL_SECONDS=5`,
The historical paced check used `REPLAY_SPEED=1`, `MAX_CYCLES=18` and explicit `CONTINUOUS_DEMO_MODE=true`; this is not the current safe default.

| Layer | Measured result |
|---|---|
| Simulator generation/event interval | Exactly 5.000 s across the recent sequence |
| SQL arrival/event interval | 23 consecutive recent deltas; min 5 s, max 5 s; zero duplicate timestamps |
| Inference/persist latency | 29 ms average, 163 ms max in the 18-cycle run; zero cycles over 5 s |
| Generated timestamps | 2026-08-06 10:00:00 through 10:01:25 (18 cycles) |
| SQL latest versioned timestamp | 2026-08-06 10:01:25 |
| Power BI automatic query interval | Configured and structurally validated at PT5S on both pages; not directly observed in the final native UI session |
| Source-to-SQL latency | Under 0.2 s in the measured run |
| Source-to-screen latency | Not directly measured; do not interpret the configured PT5S as an observed number |

The run produced one real sparse lab row at the wrapped boundary and no
anomalous rows. Final database invariants: 34,704 process rows, 34,704 model
rows, 25 valid lab samples, zero duplicates, zero orphans, zero future-lab
joins, zero legacy rows exposed to the dashboard, and model version `5s_v1.0`.

## 5. Navigation/control test

| Page | Control | Destination | Result |
|---|---|---|---|
| Operations Overview | Overview rail button | Operations Overview | PBIR action/target/z-order pass |
| Operations Overview | Diagnostics rail button | Diagnostics & Root Cause | PBIR action/target/z-order pass |
| Diagnostics & Root Cause | Overview rail button | Operations Overview | PBIR action/target/z-order pass |
| Diagnostics & Root Cause | Diagnostics rail button | Diagnostics & Root Cause | PBIR action/target/z-order pass |

There are no bookmark, back, information, or reset buttons. The export label is
explicitly instructional and is not styled as a clickable control. Page 2
slicers remain native query slicers; the events table remains the selection
source for the event/contributor detail relationship.

The four actions were verified in JSON against both existing internal page IDs.
Physical native clicking remains the one uncompleted check because the Windows
automation bridge could not retain Power BI focus safely during the active user
desktop session.

## 6. Page-by-page QA

### Operations Overview

- Clear three-to-five-second scan path: freshness → six current KPIs → eight-hour
  moisture/risk trend → diagnosis context → five critical variables → guidance.
- Full 1600×900 canvas; no out-of-bounds visuals, duplicate z/tab orders,
  scrollbars, or unresolved field references.
- Normal operation is quiet; stale state is gray; warning/anomaly colors remain
  prominent. Risk/severity are not repeated in the diagnosis panel.
- Live-data preview inspected at 1600×900 with no overlap/cropping.

### Diagnostics & Root Cause

- Investigation sequence remains information-rich without redundant KPI boxes.
- Thresholds are stated in the risk title; selected-event, contributor, cause,
  and event-table titles state their purpose.
- Event table interaction and contributor relationship are preserved.
- Live-data preview inspected at 1600×900 with no overlap/cropping.

## 7. Files modified

### Source/configuration files

- Canonical PBIR page definitions — APR/PT5S, real navigation actions,
  visual consolidation, lightweight trend bindings, clearer titles.
- `tools/generate_powerbi_semantic.py` — trend table/measures, five-second
  label, freshness/operating-state gating.
- `tools/render_dashboard_preview.py` — optimized view, synchronized layout,
  titles, navigation, refresh and stale rendering.
- `tools/validate_report_fields.py` — field, canvas, bounds, z/tab, APR,
  navigation and visual-budget gates.
- `powerbi_dashboard/sql/upgrade_5s_schema.sql` — versioned-stream filtering,
  partial index, lab/event cleanup, lightweight trend view.
- `powerbi_dashboard/sql/create_powerbi_views.sql` — marked explicitly as
  incompatible legacy reference DDL.
- `realtime_pipeline/src/realtime_service.py` — versioned resume point and
  continuous five-second loop.
- `realtime_pipeline/src/replay_service.py` — explicit legacy guard.
- `realtime_pipeline/src/validate_database_state.py` — valid/legacy stream and
  overview invariants.
- `realtime_pipeline/src/verify_powerbi_views.py` — five-view semantic contract
  and legacy-exposure check.
- `realtime_pipeline/.env.example` — continuous mode and legacy guard settings.
- `realtime_pipeline/requirements.txt` — corrected dependency line and pytest.
- `tests/test_realtime_service.py` — circular-history cadence/wrap tests.
- `README.md` and `powerbi_dashboard/README.md` — supported service, refresh,
  capacity, view, and limitation documentation.

### Generated Power BI/project artifacts

- Both page JSON files under
  `MAP Dryer AI Dashboard.Report/definition/pages/*/page.json`.
- Complete deterministic visual sets under both
  `.../pages/*/visuals/*/visual.json` folders (46 current overview visuals,
  40 current diagnostics visuals; obsolete visual folders removed; four new
  navigation action visual folders added).
- `MAP Dryer AI Dashboard.SemanticModel/definition/model.tmdl`.
- `.../tables/vw_dryer_dashboard_powerbi.tmdl`.
- New `.../tables/vw_dryer_overview_trends_powerbi.tmdl`.
- `preview/preview_page1_overview.html` and
  `preview/preview_page2_diagnostics.html`.
- QA evidence: `artifacts/final_preview_page1_v2.png`,
  `artifacts/final_preview_page2_v2.png`, and the 90-second service logs.

The pre-existing deletion of `powerbi_dashboard/gi.pbix` and the pre-existing
untracked prototype PDF were preserved and were not created or reverted by this
QA work.

### Live database changes

- Applied the idempotent five-second migration: view definitions and one
  partial index changed.
- Inserted 18 test inference cycles. No base data was deleted. One test timestamp
  replaced an incompatible legacy row through the existing idempotent upsert,
  reducing retained unversioned rows from 127 to 126.

## 8. Validation evidence

- Python compile: pass for all edited generators, services, and validators.
- Final hardening test suite (2026-08-14): **82 passed; 0 failed; 0 errors;
  0 skipped; 0 warnings**.
- Report validation: **86 visuals, 114 field references, 276 model fields in
  five tables; pass**.
- View contract: all five views pass; zero unversioned rows exposed.
- Database invariant validator: pass.
- Preview render: both pages rendered from live SQL at 1600×900 and visually
  inspected.
- Service stderr during the 90-second run: empty.

## 9. Remaining limitations and pre-demo check

1. Open the PBIP in Power BI Desktop on the presentation machine, Ctrl+click
   each of the two sidebar destinations from both pages, and watch the latest
   timestamp for at least three PT5S cycles. This closes the native UI evidence
   gap described above.
2. In the Power BI Service, five-second APR requires suitable dedicated
   capacity/admin settings and an on-premises gateway. Shared/Pro capacity will
   not honor five seconds.
3. The full KPI view still costs about 85 ms when forced to scan/count every row
   because correct lab as-of semantics are inherently heavier. Normal cards use
   latest-row filters (~0.85 ms), and charts use the optimized trend view.
4. The simulator is a deterministic prototype replay, not a production
   historian. Continuous mode advances event time by five seconds while reusing
   source patterns.
5. The report remains advisory decision support, not automatic process control;
   the target moisture band is a training-reference band, not an approved
   product specification.

## 10. Final verdict

**READY FOR DEMO WITH MINOR LIMITATIONS.**

The architecture, models, SQL contract, five-second writer, DirectQuery report,
navigation definitions, field references, data correctness, performance
budgets, and visual hierarchy are ready. The sole material sign-off item is a
short native Power BI Desktop click/refresh observation on the presentation
machine; it is called out rather than reported as an unmeasured success.
