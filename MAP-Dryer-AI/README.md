# MAP Dryer AI

MAP Dryer AI is an end-to-end engineering prototype for monitoring a soluble
monoammonium phosphate (MAP) fertilizer dryer. It combines a moisture soft
sensor, process anomaly detection, evidence-based diagnosis, PostgreSQL
storage, and a live Power BI dashboard.

The project uses a deterministic **92-day synthetic dataset**. It demonstrates
the architecture and analytical workflow; it is not a validated plant control
system or a substitute for operator judgment.

## What the system does

- Estimates final product moisture between sparse laboratory measurements.
- Detects unusual process behavior from process variables only.
- Ranks abnormal variables and maps them to likely subsystems and checks.
- Replays a separate two-day dashboard demonstration fork at one row every five seconds.
- Writes process values, predictions, risks, and diagnoses to PostgreSQL.
- Presents the latest state, trends, events, and contributors in Power BI.

## Architecture

```text
92-day canonical CSV
        │
        ├── Notebooks 01–02: audit, causal alignment, 16-feature handoff
        │                         │
        │                  Notebook 03: moisture soft sensor (Ridge)
        │                  Notebook 04: anomaly model (One-Class SVM)
        │                         │
        │                    models/5s/
        │                         │
        └── dashboard demo fork ────> realtime_service.py
                                          │
                         moisture + anomaly + diagnosis
                                          │
                                      PostgreSQL
                                          │
                                  five semantic SQL views
                                          │ DirectQuery, ~5 s APR
                                          ▼
                              Power BI operations dashboard
```

The runtime reads `data/dashboard_demo/MAP_Dryer_Dashboard_Demo_5s.csv`,
an isolated copy of July 15–16 enriched with eight traceable occurrences of
scenario families already present in the canonical data. The canonical
dataset, chronological splits, notebooks, trained artifacts, and reported
metrics remain unchanged. The dashboard fork is demonstration data, never a
new test set.

## Data and modeling contract

| Item | Current implementation |
|---|---|
| Canonical source | `data/raw/MAP_Dryer_Canonical_5s_deterministic.csv`, restored from the versioned `.csv.xz` archive |
| Process history | 1,589,760 gap-free rows over 92 days |
| Prototype cadence | 5 seconds |
| Laboratory results | 1,104 sparse samples, approximately every 2 hours |
| Moisture inputs | 16 direct and engineered features |
| Temporal alignment | Process snapshot at or before `lab time − residence time`; latest strictly prior lab density and temperature |
| Data split | Chronological TRAIN → VALIDATION → TEST |
| Moisture model | Ridge regression, selected by validation RMSE |
| Anomaly model | One-Class SVM on 15 process-only features |
| Diagnosis | Robust reference limits, ranked contributors, and process rules |

The moisture model uses the project’s original process features—not rolling
means or standard deviations. Its held-out TEST results are MAE `0.001069`,
RMSE `0.001403`, and R² `0.8245` across 165 laboratory targets. The selected
artifacts and their ordered feature contracts are stored in `models/5s/`.

Detailed units and interpretations live in `config/data_dictionary.yaml`.
Final moisture uses a percentage-point scale: `0.075` means `0.075% H₂O`, not
`7.5%`.

## One-command demonstration

Prerequisites are Python 3, PostgreSQL with the project schema, and Power BI
Desktop. Configure database credentials and the existing source/model paths in
`realtime_pipeline/.env` (use `.env.example` as the template), then close any
open Power BI Desktop window and run from the repository root:

```powershell
.\RUN_FINAL_DEMO.ps1
```

The launcher validates the environment, clears only runtime/demo tables,
starts a fresh five-second dashboard-demo replay, verifies the Power BI SQL views, and
opens the canonical dashboard directly in a borderless, edge-to-edge
presentation view. The live report canvas stays interactive while the Power BI
editor chrome and Windows taskbar remain outside the display. Press `F11` to
toggle presentation mode or `Esc` to return to the editor. The simulation
continues while Power BI is open and stops when Power BI closes or when
`Ctrl+C` is pressed.

To deliberately start in the normal Power BI editor window:

```powershell
.\RUN_FINAL_DEMO.ps1 -Windowed
```

You can still press `F11` from that window to enter presentation mode.

To keep existing runtime rows and resume after the newest stored timestamp:

```powershell
.\RUN_FINAL_DEMO.ps1 -Resume
```

To accelerate the five-second source replay without making page navigation
fight a two-second visual refresh cycle:

```powershell
.\RUN_FINAL_DEMO.ps1 -ReplaySeconds 2
```

This advances one source row every two wall-clock seconds while Power BI keeps
its smooth five-second display refresh. The older `-RefreshSeconds 2` spelling
remains supported. `-PageRefreshSeconds` is available as
an explicit override, but values below five seconds are intentionally warned.

The launcher never retrains models, regenerates datasets, executes notebooks,
or rebuilds the report.

## Reproducing the analytical workflow

The canonical 92-day CSV is 235 MB, past GitHub's per-file limit, so the
repository versions it as a 40 MB XZ archive. It is user-supplied and
deterministic; nothing here regenerates it, so that archive is the copy of
record. Expand it once before running the notebooks:

```powershell
python tools/restore_canonical_dataset.py
```

That writes both referenced paths - `data/raw/MAP_Dryer_Canonical_5s_deterministic.csv`
and `data/processed/MAP_Dryer_Canonical_5s.csv` - and verifies each against the
SHA-256 in `data/processed/MAP_Dryer_Canonical_5s.manifest.json`. Use
`--check` to re-verify an existing copy without writing anything.

Then install the notebook dependencies and run the notebooks in order:

```powershell
python -m pip install -r requirements.txt
jupyter notebook
```

1. `01_Data_Exploration.ipynb` audits completeness, cadence, distributions,
   trends, and multi-rate quality sampling.
2. `02_Feature_Engineering.ipynb` performs causal residence-time alignment and
   produces the ordered 16-feature supervised handoff.
3. `03_Model1_SoftSensor.ipynb` compares regression candidates using
   time-aware validation, evaluates the final TEST split, and exports the
   moisture model.
4. `04_Model2_AnomalyDetection&Diagnosis.ipynb` trains and evaluates the
   process-only novelty detector and diagnosis workflow.

To execute the same four notebooks unattended, in order, saving their
outputs in place:

```powershell
python tools/run_canonical_notebooks.py
```

Notebook execution is the reproducibility path, not a prerequisite for the
final demo. Machine-readable notebook results are retained in `artifacts/`.
Notebook 03 rewrites `models/5s/reference_profile.json`, whose integrity record
is re-issued by Notebook 04, so run the four notebooks as a set rather than
individually.

## Runtime and dashboard layers

| Layer | Responsibility |
|---|---|
| `realtime_pipeline/src/realtime_service.py` | Loads the exported models once, performs five-second inference, and uses idempotent database writes |
| PostgreSQL | Stores `dryer_map`, `dryer_model_outputs`, and `dryer_abnormal_variables` and exposes five Power BI views |
| `realtime_pipeline/src/verify_powerbi_views.py` | Checks live SQL columns against the checked-in TMDL contracts |
| `powerbi_dashboard/` | Two-page PBIP report using PostgreSQL DirectQuery and five-second automatic page refresh |

Power BI performs visualization only; it does not load joblib files or execute
model inference. See `powerbi_dashboard/README.md` for connection details,
semantic-model behavior, and dashboard limitations.

For a new PostgreSQL instance, apply
`powerbi_dashboard/sql/bootstrap_base_schema.sql`, then run:

```powershell
python realtime_pipeline/src/apply_sql_migration.py
python realtime_pipeline/src/verify_powerbi_views.py
```

## Tests and validation

`pytest.ini` adds `src/` to Python’s import path and limits discovery to
`tests/`. Run the automated contracts from the repository root:

```powershell
pytest -q
```

The suite covers feature metadata, scoring, attribution, diagnosis rules,
temporal behavior, artifact compatibility, and runtime helpers. Two checks need
the git-ignored `data/processed/MAP_Dryer_TEST_Replay_5s.csv` and skip with an
explanatory message until the notebooks have regenerated it, so a fresh clone
reports 75 passed and 2 skipped. The latest
full implementation record is `artifacts/FINAL_VALIDATION_2026-08-24.md`; the
complete technical narrative is in
`final_report/MAP_Dryer_AI_Internship_Report.pdf`.

## Repository map

```text
artifacts/                machine-readable audits, metrics, and validation record
config/                   data dictionary, thresholds, subsystems, diagnosis rules
data/raw/                 canonical 92-day dataset, versioned as .csv.xz (see .gitignore)
data/processed/           canonical manifest and the versioned Notebook 02 handoff
figures/                  notebook-generated analytical figures
final_presentation/ Three.js soutenance keynote, exports, speaker notes and QA
final_report/             LaTeX sources and final internship report
models/5s/                active moisture, anomaly, scaler, schema, and profile
notebooks/                four-stage analytical workflow
powerbi_dashboard/        PBIP report, TMDL model, PBIR pages, and SQL definitions
realtime_pipeline/        environment, database utilities, and replay service
data/dashboard_demo/      the two-day replay fork the runtime reads
final_presentation/reference_resources/ process and site reference material
src/                      reusable data, feature, model, anomaly, and diagnosis code
tests/                    automated behavioral and integration contracts
tools/                    dashboard-demo, Power BI, report and notebook generators
conftest.py               test import paths for src/ and realtime_pipeline/src/
.gitattributes            byte-stable checkout for the hash-verified artifacts
RUN_FINAL_DEMO.ps1        canonical one-command dashboard launcher
RUN_PRESENTATION.ps1      canonical one-command soutenance keynote launcher
```

## Final deliverables

| Deliverable | Location |
|---|---|
| Internship report | `final_report/MAP_Dryer_AI_Internship_Report.pdf` (LaTeX sources alongside) |
| Soutenance keynote | `final_presentation/` — interactive Three.js build plus PDF and PPTX fallbacks |
| Operations dashboard | `powerbi_dashboard/MAP Dryer AI Dashboard.pbip` |
| Model artifacts | `models/5s/` |
| Validation record | `artifacts/FINAL_VALIDATION_2026-08-24.md` |

## Interpretation boundaries

- The data, disturbances, labels, and model evidence are synthetic.
- Five seconds is the prototype replay/visualization cadence, not a verified
  PCS7 historian acquisition rate.
- Anomaly risk is a calibrated display score, not a probability of failure.
- Diagnosis localizes supporting evidence; it does not prove root cause.
- Moisture bands and anomaly thresholds are analytical references, not
  approved product specifications, alarms, interlocks, or safety limits.
