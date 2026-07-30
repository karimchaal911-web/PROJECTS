# MAP Dryer AI

MAP Dryer AI is an industrial analytics and machine-learning project for a MAP
dryer. Its purpose is to turn operating data into earlier, practical insight
about product moisture and process performance. The project begins with a
regression **soft sensor**: it estimates final product moisture from process
measurements before the laboratory result is available.

The longer-term scope is to add off-spec classification, anomaly detection, a
process-health score, and a dashboard for operators and process engineers.

## Project goals

- Predict `final_moisture_h₂o` using process variables such as temperatures,
  air flow, feed rate, residence time, vacuum, pressure, and fan speed.
- Prepare a reliable, reproducible dataset from raw dryer records.
- Explore process distributions, relationships, and data-quality issues.
- Compare regression models with time-aware validation and clear error metrics.
- Provide a foundation for off-spec alerts, anomaly monitoring, and a simple
  operations dashboard.

## Current project status

The data preparation, feature engineering, and soft-sensor notebooks are the
working part of the project. The off-spec, anomaly, and model-comparison
notebooks are intentionally empty placeholders for the next stage. The
Streamlit dashboard is also a starter screen; it does not yet load a trained
model or make live predictions.

## Workflow

```text
Raw dryer data
  → schema validation and cleaning
  → exploratory analysis and duplicate review
  → feature engineering
  → time-ordered model training and evaluation
  → soft-sensor prediction
  → future off-spec / anomaly monitoring / dashboard
```

## Repository structure

```text
MAP-Dryer-AI/
├── dashboard/
│   └── app.py                         # Streamlit dashboard scaffold
├── data/
│   ├── raw/                           # Input Excel data (not committed)
│   └── processed/                     # Generated modelling datasets (not committed)
├── docs/                              # Process diagrams, literature, and report material
├── figures/                           # Generated exploratory figures
├── models/
│   ├── soft_sensor/                   # Future saved regression models
│   ├── off_spec/                      # Future classification models
│   └── anomaly/                       # Future anomaly-detection models
├── notebooks/
│   ├── 01_Data_Exploration.ipynb      # Cleaning, duplicate review, and EDA
│   ├── 02_Feature_Engineering.ipynb   # Model-ready feature creation
│   ├── 03_Model1_SoftSensor.ipynb     # Moisture-regression experiments
│   ├── 04_Model2_OffSpec.ipynb        # Placeholder
│   ├── 05_Model3_Anomaly.ipynb        # Placeholder
│   └── 06_Model_Comparison.ipynb      # Placeholder
├── reports/                           # Statistical reports and deliverables
└── src/
    ├── data/
    │   ├── data_cleaning.py           # Schema checks, parsing, timestamps
    │   └── project_paths.py           # Project-root discovery helper
    ├── stats/
    │   └── descriptive_statistics.py  # Numeric summary statistics
    ├── features/                      # Reserved for reusable feature code
    ├── models/                        # Reserved for reusable model code
    ├── visualization/                 # Reserved for reusable plotting code
    └── utils/                         # Reserved for shared utilities
```

## Notebook guide

Run the implemented notebooks in this order:

1. **01 — Data Exploration** loads the raw MAP dryer data, validates the
   expected schema, normalizes dates and decimal values, creates timestamps,
   reviews duplicate records, and produces exploratory output.
2. **02 — Feature Engineering** reads the cleaned dataset and writes the
   model-ready feature table used by the soft sensor.
3. **03 — Soft Sensor** predicts final moisture with a chronological 80/20
   split and time-series cross-validation. It compares linear regression,
   Ridge, random-forest, and gradient-boosting models using MAE, RMSE, and R²;
   the notebook also includes model interpretation work with SHAP.

Notebooks 04–06 are reserved for future work and do not yet contain analysis
cells.

## Data setup

Raw and processed dryer data are excluded from Git because they may be large
or operationally sensitive. The `.gitkeep` files preserve the required folder
structure, but you must supply the data locally before running the notebooks.

Place the files in these locations:

```text
data/raw/dryerMAP_prototype.xlsx
data/processed/dryerMAP_prototype_deduplicated.xlsx   # created by notebook 01
data/processed/dryerMAP_prototype_processed.csv        # created by notebook 02
```

For a clean run, provide the raw Excel file first, then execute notebooks 01,
02, and 03 in sequence. Do not commit proprietary raw data, processed datasets,
or trained model artefacts without confirming that they may be shared.

## Installation and use

Use a virtual environment and install the notebook and dashboard dependencies:

```powershell
cd "MAP-Dryer-AI"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install pandas numpy scipy matplotlib seaborn scikit-learn statsmodels shap joblib openpyxl jupyter streamlit
jupyter lab
```

Open the notebooks in Jupyter and run them in numerical order. Once Streamlit
is installed, launch the dashboard scaffold with:

```powershell
streamlit run dashboard/app.py
```

## Reproducibility notes

- The cleaner validates the expected 14-column MAP dataset, accepts decimal
  commas or decimal points, parses dates and times, and builds a timestamp.
- The soft-sensor notebook assumes that the feature-engineering output exists.
- Model artefacts are not currently saved or wired into the dashboard.
- This is a development and portfolio project, not a production control system;
  any production use requires data validation, acceptance criteria, monitoring,
  access controls, and process-owner approval.
