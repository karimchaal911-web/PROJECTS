# Resource Audit — MAP Dryer Digitalization Soutenance

## Source boundary

The pre-existing repository folder `final_presentation/` is explicitly excluded from visual, narrative, structural, and implementation reference. It remains untouched during development and is replaced only after the new canonical package passes QA.

This presentation is grounded only in primary project evidence: `final_report/`, `figures/`, `models/`, `artifacts/`, `data/`, `powerbi dashboard/`, `resources/presentation_resources/`, and the repository test suite.

## Communication job

By the end, an industrial engineering jury should understand that the project closes a real supervision gap between sparse laboratory measurements and continuously evolving dryer conditions, using an advisory soft sensor, novelty detection, evidence localization, PostgreSQL, and Power BI—without overstating the prototype as a live control system.

## Canonical technical claims

| Topic | Verified claim | Presentation treatment |
| --- | --- | --- |
| Process visibility | Laboratory moisture measurements are approximately two hours apart. | Sparse laboratory orbs sit above a continuous process timeline. |
| Prototype cadence | The replay and visualization cadence is 5 seconds. It is not claimed as the plant historian frequency. | Persistent qualifier: `PROTOTYPE REPLAY Δt = 5 s`. |
| Dataset | Deterministic synthetic 92-day dataset; 1,589,760 gap-free rows; 1,104 lab observations; 1,103 supervised rows. | Evidence chapter only; clearly labeled synthetic prototype data. |
| Soft sensor | Ridge regression, α = 10, 16 features. | Shown as a disciplined quality-estimation path, not “AI magic.” |
| Holdout performance | TEST: R² 0.8245; MAE 0.001069; RMSE 0.001403; bias 0.000066; units are percentage points `% H₂O`. | Large evidence figures beside the real holdout plot. |
| Anomaly model | One-Class SVM over 15 process-only features; 5.925% validation novelty flag rate. | Shown as process novelty intelligence. |
| Risk | Display risk is logistic, with 0.5 warning and 0.8 critical display boundaries. It is not a probability. | Explicit label in notes and detail view. |
| Diagnosis | Robust quantiles plus ranked direct contributors localize evidence; they do not prove causality. | Operator verification remains in the loop. |
| Runtime | Python inference → PostgreSQL (3 tables, 5 views) → Power BI DirectQuery/APR. | Spatial data pipeline with authentic component labels. |
| Scope | No live PCS7 connection, actuator write-back, autonomous control, or laboratory replacement. | Today→Next path makes governance and shadow validation explicit. |

## Primary visual resources

### Brand

- `final_report/figures/branding/ocp.png` — official local OCP mark. Dominant green sampled near `#017B30`.
- `final_report/figures/branding/ensam_umi.png` — academic partner mark.

### Plant evidence

- `final_report/figures/process_photos/drying_section_structure.jpeg` — structural hero image: green-painted steel, elevated ducts, access platforms.
- `final_report/figures/process_photos/rotary_dryer_shell.jpeg` — physical rotary-dryer geometry.
- `final_report/figures/process_photos/downstream_solids_transfer.jpeg` — solids handling after drying.
- `final_report/figures/process_photos/soluble_map_storage.jpeg` — product storage and industrial scale.
- `final_report/figures/screenshots/pcs7_drying.jpeg` — real supervisory context; used as evidence, never imitated as a fictional interface.

### Model evidence

- `figures/03_Model1_SoftSensor/05_final_holdout_predictions.png` — authentic TEST actual-versus-predicted behavior.
- `figures/04_Model2_Anomaly_and_Diagnosis/02_anomaly_scores_over_time.png` — authentic novelty score behavior.
- `models/5s/training_report.json` and manifests — authoritative metrics and split sizes.

### Dashboard evidence

- `powerbi dashboard/preview/preview_page1_overview.png` — six KPIs, trends, process variables, diagnosis context.
- `powerbi dashboard/preview/preview_page2_diagnostics.png` — event selection, contributors, guidance, and recent events.
- Power BI is treated as visualization and supervision only; no fictional interactivity or fabricated data is added.

## External art-direction references

- OCP: green/cream editorial restraint, large photography, strong whitespace.
- SiteAssist: industrial aerial imagery, monospace metadata, decisive scale shifts.
- Otsuka Air ZEROZ: chaptered spatial travel and a single continuous visual experience.
- KMZ Industries: legible industrial machinery and process-scale material handling.

These references inform atmosphere and composition only. No external copy, metrics, proprietary assets, or interface replicas are used.

## Resource gaps and responses

- No usable local video exists: the presentation creates motion procedurally in Three.js and exports a deterministic backup video.
- No trustworthy 3D CAD or plant model exists: the persistent world is a stylized, non-CAD industrial abstraction based on real process topology and photographs.
- No live plant data connection is included: all dynamic behavior is clearly labeled as prototype replay.
- The source Power BI pages are static previews in this package: live navigation is optional and separately documented for the presentation machine.

## Acceptance constraints

- No fabricated production benefit, ROI, safety improvement, or plant KPI.
- No inference that 5 seconds is the historian sampling interval.
- No claim of closed-loop control or causality.
- Model units remain percentage points `% H₂O`.
- One persistent renderer and one spatial world; chapters are camera/state changes, not unrelated slide canvases.

