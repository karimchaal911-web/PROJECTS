# MAP Dryer AI

Prototype notebook pipeline for MAP dryer data preparation, feature engineering,
moisture soft sensing, anomaly detection, and rule-based diagnosis.

## Run the project

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
models/diagnosis/       diagnostic metadata and event records
notebooks/              the four executable workflow notebooks
src/anomaly/            scoring, thresholds, persistence, alarms, and evaluation
src/data/               paths, cleaning, and the feature catalog
src/diagnosis/          attribution, rules, severity, and diagnostic reports
src/features/           shared feature-engineering transformations
src/models/             model evaluation helpers
src/stats/              descriptive statistics
tests/                  automated diagnostic and runtime-helper tests
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
