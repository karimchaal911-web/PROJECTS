# MAP Dryer AI

Prototype notebook pipeline for MAP dryer data preparation, feature engineering,
moisture soft sensing, anomaly detection, and rule-based diagnosis — plus a
5-second multi-rate real-time prototype (PostgreSQL + Power BI DirectQuery).

## 5-second real-time prototype (quickstart)

The 5-second datasets live in `resources/prototype_data/`. Process variables
arrive every 5 seconds; the three quality variables only exist where a real
laboratory analysis was made (about every 2 hours) — the blanks in between
are structural, never missing data.

```powershell
python -m pip install -r requirements.txt
python -m pip install -r realtime_pipeline/requirements.txt

# 1. Train the 5-second models (writes models/5s/)
python tools/train_5s_models.py

# 2. Configure credentials, then create the database schema
#    (copy realtime_pipeline/.env.example to .env and fill in DB_*)
python realtime_pipeline/src/bootstrap_database.py

# 3. Verify the Power BI view contract
python realtime_pipeline/src/verify_powerbi_views.py

# 4. Run the 5-second service
#    REPLAY_SPEED=1 → real time; 0 → accelerated bulk catch-up
python realtime_pipeline/src/realtime_service.py

# 5. Optional: render both dashboard pages as HTML previews from live SQL
python tools/render_dashboard_preview.py

# 6. Tests
python -m pytest tests
```

The Power BI project is `POWERBI DASHBOARD/MAP Dryer AI Dashboard.pbip`
(DirectQuery, 60-second automatic page refresh; the backend ingests every
5 seconds regardless). See `POWERBI DASHBOARD/README.md`.

Multi-rate rules enforced end-to-end: laboratory values are never
interpolated, forward-filled into training targets, or compared against a
carried-forward result; quality-model feature windows end at
`t_lab − residence_time − transport_delay` and never see future process
rows; splits are chronological (70/15/15, `TimeSeriesSplit` for CV).

## Run the notebook project

Create an environment, install the dependencies, and run the notebooks in order:

```powershell
python -m pip install -r requirements.txt
jupyter notebook
```

1. `01_Data_Exploration.ipynb` cleans and explores the raw workbook.
2. `02_Feature_Engineering.ipynb` adds the shared process indicators.
3. `03_Model1_SoftSensor.ipynb` trains and evaluates the moisture soft sensor.
4. `04_Model2_AnomalyDetection&Diagnosis.ipynb` detects persistent anomalies and
   diagnoses their likely process causes.

The notebooks locate the project root automatically, so they can be started from
the repository root or from the `notebooks` directory.

## Runtime architecture

```text
config/                 feature definitions, diagnostic rules, and thresholds
data/raw/               required prototype workbook
data/processed/         outputs shared by later notebooks
figures/                generated notebook figures
models/5s/              trained 5-second models + feature schema + report
models/diagnosis/       diagnostic metadata and event records
notebooks/              the four executable workflow notebooks
realtime_pipeline/      5-second ingestion/inference service + DB scripts
resources/              5-second prototype datasets + dashboard templates
src/anomaly/            scoring, thresholds, persistence, alarms, and evaluation
src/data/               paths, cleaning, and the feature catalog
src/diagnosis/          attribution, rules, severity, and diagnostic reports
src/features/           shared feature-engineering transformations
src/models/             model evaluation helpers
src/multirate/          5-second multi-rate preprocessing, alignment, features
src/stats/              descriptive statistics
tests/                  diagnostic, runtime-helper, and multirate tests
tools/                  training, report generation, validation, previews
```

Required input:

- `data/raw/dryerMAP_prototype_2.xlsx`

Generated pipeline datasets:

- `data/processed/dryerMAP_prototype_deduplicated_2.xlsx`
- `data/processed/dryerMAP_prototype_processed_2.csv`

Notebook 04 writes all anomaly and diagnosis plots to
`figures/04_Model2_Anomaly_and_Diagnosis/`.

## Measurement contract

The authoritative names, roles, units, and interpretations are in
`config/data_dictionary.yaml`. Key supplied units are:

| Feature | Unit |
|---|---|
| Air flow rate | m³/h |
| Wet product feed rate | m³/h |
| Vacuum | mmH2O; more negative means stronger depressure |
| Steam pressure | bar |
| Fan speed | rpm |

This repository is a prototype decision-support workflow, not a production PCS7
control system.
