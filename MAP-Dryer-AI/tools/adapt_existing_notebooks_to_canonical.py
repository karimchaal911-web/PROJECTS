"""Patch only affected cells in the existing four-notebook structure.

Existing cell order, ids, and untouched cell sources are preserved. The script
adds only the two explicitly requested Elastic Net code cells to Notebook 03
and asserts every notebook shape so it cannot silently replace a layout.
"""

from __future__ import annotations

from pathlib import Path

import nbformat


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = ROOT / "notebooks"


def patch_notebook(name: str, expected_cells: int, replacements: dict[int, str]) -> None:
    path = NOTEBOOKS / name
    notebook = nbformat.read(path, as_version=4)
    if len(notebook.cells) != expected_cells:
        raise RuntimeError(
            f"Refusing to patch {name}: expected {expected_cells} cells, "
            f"found {len(notebook.cells)}."
        )
    for index, source in replacements.items():
        notebook.cells[index].source = source.strip("\n") + "\n"
    nbformat.write(notebook, path)
    print(f"{name}: preserved {len(notebook.cells)} cells; edited {sorted(replacements)}")


def ensure_elastic_net_cells(notebook: nbformat.NotebookNode) -> None:
    """Insert the requested NB3 training/metrics cells exactly once."""

    if len(notebook.cells) == 49:
        training = nbformat.v4.new_code_cell(
            source="""elastic_net_model = ElasticNet(
    alpha=0.0001,
    l1_ratio=0.8,
    max_iter=100000,
    tol=1e-7,
    random_state=42,
)
elastic_net_model.fit(X_train_scaled, y_train)
y_pred_elastic_net = elastic_net_model.predict(X_test_scaled)

print(\"Elastic Net baseline trained.\")"""
        )
        training.id = "elastic-net-training"
        metrics = nbformat.v4.new_code_cell(
            source="""elastic_net_metrics = pd.DataFrame(
    {
        \"MAE\": [mean_absolute_error(y_test, y_pred_elastic_net)],
        \"RMSE\": [np.sqrt(mean_squared_error(y_test, y_pred_elastic_net))],
        \"R²\": [r2_score(y_test, y_pred_elastic_net)],
        \"Maximum absolute error\": [max_error(y_test, y_pred_elastic_net)],
    },
    index=[\"Elastic Net\"],
)

display(elastic_net_metrics.round(4))"""
        )
        metrics.id = "elastic-net-metrics"
        notebook.cells[32:32] = [training, metrics]
    if len(notebook.cells) != 51:
        raise RuntimeError(
            "Refusing to patch Notebook 03: expected 49 original cells or "
            f"51 cells with the Elastic Net additions, found {len(notebook.cells)}."
        )
    if [notebook.cells[32].id, notebook.cells[33].id] != [
        "elastic-net-training",
        "elastic-net-metrics",
    ]:
        raise RuntimeError("Notebook 03 Elastic Net cells are not in the expected location.")


def patch_notebook_03(replacements: dict[int, str]) -> None:
    path = NOTEBOOKS / "03_Model1_SoftSensor.ipynb"
    notebook = nbformat.read(path, as_version=4)
    ensure_elastic_net_cells(notebook)
    for index, source in replacements.items():
        notebook.cells[index].source = source.strip("\n") + "\n"
    nbformat.write(notebook, path)
    print(
        "03_Model1_SoftSensor.ipynb: preserved 49 original cells; added "
        f"[32, 33]; edited {sorted(replacements)}"
    )


def main() -> None:
    patch_notebook(
        "01_Data_Exploration.ipynb",
        17,
        {
            6: """## 2. Locate the project and load the canonical source

Notebook 01 now audits the complete 92-day canonical CSV. A bounded deterministic
sample from that same file is retained for readable exploratory plots; it is not
a second dataset.""",
            7: """from canonical_pipeline import CANONICAL_CSV, audit_canonical_dataset
from multirate.preprocessing import RAW_SOURCE_COLUMNS

DATA_PATH = CANONICAL_CSV
canonical_audit = audit_canonical_dataset()

sampled_chunks = []
for chunk in pd.read_csv(DATA_PATH, usecols=RAW_SOURCE_COLUMNS, chunksize=200_000):
    sampled_chunks.append(chunk.iloc[::120])
    sampled_chunks.append(chunk.loc[chunk["Final Moisture (%H2O)"].notna()])
raw_sample = (
    pd.concat(sampled_chunks, ignore_index=True)
    .drop_duplicates(subset=["Date", "Time"])
    .reset_index(drop=True)
)
dryerMAP = prepare_dryer_map(raw_sample)
dryerMAP = dryerMAP.rename(columns={"final_moisture_h2o": "final_moisture_h₂o"})

print(f"Canonical source: {DATA_PATH}")
print(f"Full audited rows: {canonical_audit['process_rows']:,}")
print(f"Laboratory samples: {canonical_audit['laboratory_samples']:,}")
print(f"Exploration sample: {len(dryerMAP):,} rows")
dryerMAP.head(10)""",
            9: """expected_columns = [
    'date', 'time', 'dryer_air_temperature', 'cooler_air_temperature',
    'air_flow_rate', 'wet_product_feed_rate', 'product_inlet_temperature',
    'residence_time', 'vacuum', 'steam_pressure', 'fan_speed',
    'product_density', 'final_product_temp', 'final_moisture_h₂o'
]
assert dryerMAP.columns[:len(expected_columns)].tolist() == expected_columns

duplicate_count = int(dryerMAP.duplicated().sum())
dryerMAP_unique = dryerMAP.drop_duplicates().reset_index(drop=True)
validation_summary = pd.Series({
    "full_process_rows": canonical_audit["process_rows"],
    "full_laboratory_samples": canonical_audit["laboratory_samples"],
    "duration_days": canonical_audit["duration_days"],
    "process_interval_seconds": canonical_audit["process_interval_seconds"],
    "laboratory_interval_minutes": canonical_audit["laboratory_interval_minutes"],
    "exploration_sample_rows": len(dryerMAP_unique),
    "sample_duplicate_rows": duplicate_count,
    "all_canonical_checks_pass": all(canonical_audit["checks"].values()),
})
validation_summary""",
            16: """## Next step

Continue with **Notebook 02: Feature Engineering**, which consumes the same
canonical dataset hash and builds leakage-safe process snapshots aligned to the
sparse two-hour laboratory observations.""",
        },
    )

    patch_notebook(
        "02_Feature_Engineering.ipynb",
        36,
        {
            6: """## 2. Load the canonical Notebook 01 handoff

Build the residence-aware laboratory handoff directly from the canonical CSV.
The 16 modelling inputs retain the original Notebook 02 feature names: direct
process values, prior density/temperature results, and the five engineered
features. No mean/std feature replacement is used.""",
            7: """from canonical_pipeline import ALIGNED_PATH, build_feature_handoff

aligned_features, handoff = build_feature_handoff()
OUTPUT_PATH = ALIGNED_PATH

dryerMAP = pd.DataFrame({
    "timestamp": pd.to_datetime(aligned_features.index),
    "dryer_air_temperature": aligned_features["dryer_air_temperature"],
    "cooler_air_temperature": aligned_features["cooler_air_temperature"],
    "air_flow_rate": aligned_features["air_flow_rate"],
    "wet_product_feed_rate": aligned_features["wet_product_feed_rate"],
    "product_inlet_temperature": aligned_features["product_inlet_temperature"],
    "residence_time": aligned_features["residence_time"],
    "vacuum": aligned_features["vacuum"],
    "steam_pressure": aligned_features["steam_pressure"],
    "fan_speed": aligned_features["fan_speed"],
    "product_density": aligned_features["product_density"],
    "final_product_temp": aligned_features["final_product_temp"],
    "final_moisture_h₂o": aligned_features["Final Moisture (%H2O)"],
})
dryerMAP.insert(0, "time", dryerMAP["timestamp"].dt.time)
dryerMAP.insert(0, "date", dryerMAP["timestamp"].dt.normalize())

print(f"Canonical supervised rows: {handoff['supervised_rows']:,}")
print(f"Governed feature count: {handoff['feature_count']}")
print(f"Governed output: {OUTPUT_PATH}")
dryerMAP.info()""",
            17: """## 5. Confirm the aligned modelling table

Notebook 02 rejects the single initial timestamp that lacks sufficient causal
process history. Density and product temperature are the most recent strictly
previous laboratory results; the moisture target is never forward-filled.""",
            18: """print(f"Aligned laboratory rows: {len(dryerMAP):,}")
dryerMAP_model = dryerMAP.dropna().copy()
print(f"Complete aligned rows: {len(dryerMAP_model):,}")
print(f"Rows removed here: {len(dryerMAP) - len(dryerMAP_model):,}")""",
            33: """## 12. Verify the governed model-ready export

The canonical builder has already written the exact 16-feature handoff. This
cell verifies its location and schema rather than overwriting it with the
legacy exploratory projection.""",
            34: """assert OUTPUT_PATH.exists()
assert handoff["feature_count"] == 16
assert handoff["quality_fields_used_as_model_inputs"] == [
    "product_density", "final_product_temp"
]
print(f"Verified canonical model-ready data: {OUTPUT_PATH}")
print(f"Rows: {handoff['supervised_rows']:,}; features: {handoff['feature_count']}")""",
            35: """## Next step

Continue with **Notebook 03: Model 1: Soft Sensor**, which reads the governed
16-feature handoff, preserves chronological TRAIN → VALIDATION → TEST order,
and exports the selected moisture model.""",
        },
    )

    patch_notebook_03(
        {
            2: """from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import shap
from sklearn.base import clone
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import ElasticNet, LinearRegression, Ridge
from sklearn.metrics import max_error, mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

SRC_DIR = next(
    candidate / "src" for candidate in [Path.cwd(), *Path.cwd().parents]
    if (candidate / "src" / "canonical_pipeline.py").exists()
)
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from canonical_pipeline import (
    ALIGNED_PATH, train_final_model, validate_moisture_runtime_contract
)
from multirate import MOISTURE_FEATURE_NAMES
from data.feature_catalog import feature_axis_label, load_feature_catalog, select_feature_catalog
from data.project_paths import find_project_root
from stats.descriptive_statistics import descriptive_summary
from models.regression import calculate_regression_metrics

PROJECT_ROOT = find_project_root()
FIGURE_OUTPUT_DIR = PROJECT_ROOT / "figures" / "03_Model1_SoftSensor"
FIGURE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DATA_DICTIONARY_PATH = PROJECT_ROOT / "config" / "data_dictionary.yaml"
feature_catalog = load_feature_catalog(DATA_DICTIONARY_PATH)
sns.set_theme(style="whitegrid")
pd.set_option("display.max_columns", None)""",
            6: """## 2. Load the governed Notebook 02 feature table

Read the 1,103-row table produced from the canonical 92-day source. It retains
the original 16 Notebook 02 features without mean/std/last suffixes.""",
            7: """DATA_PATH = ALIGNED_PATH
dryerMAP_model = pd.read_csv(DATA_PATH, parse_dates=["Sample Timestamp"])
dryerMAP_model = dryerMAP_model.rename(columns={
    "Sample Timestamp": "timestamp",
    "Final Moisture (%H2O)": "final_moisture_hâ‚‚o",
})
dryerMAP_model.insert(0, "time", dryerMAP_model["timestamp"].dt.time.astype(str))
dryerMAP_model.insert(0, "date", dryerMAP_model["timestamp"].dt.normalize())
display(dryerMAP_model.head())
dryerMAP_model.info()""",
            10: """## 4. Define the prediction target and governed features

The target is final moisture. The explicit list below is your original feature
set from Notebook 02 and is also the ordered runtime contract.""",
            11: """TARGET = "final_moisture_hâ‚‚o"
FEATURES = [
    "dryer_air_temperature",
    "cooler_air_temperature",
    "air_flow_rate",
    "wet_product_feed_rate",
    "product_inlet_temperature",
    "residence_time",
    "vacuum",
    "steam_pressure",
    "fan_speed",
    "product_density",
    "final_product_temp",
    "temperature_drop",
    "air_product_delta",
    "air_per_feed",
    "steam_temp_interaction",
    "heating_index",
]
assert FEATURES == list(MOISTURE_FEATURE_NAMES)
MOISTURE_UNIT = "percentage points (% H2O)"
print(f"Target: {TARGET}; features: {len(FEATURES)}")""",
            14: """## 6. Create chronological TRAIN, VALIDATION, and TEST splits

Use the first 70% for training, the next 15% for model-family validation, and
the final 15% once for testing. No observations are shuffled.""",
            15: """n_train = int(round(len(dryerMAP_model) * 0.70))
validation_stop = int(round(len(dryerMAP_model) * 0.85))
n_validation = validation_stop - n_train

X_train, y_train = X.iloc[:n_train], y.iloc[:n_train]
X_validation, y_validation = X.iloc[n_train:validation_stop], y.iloc[n_train:validation_stop]
X_test, y_test = X.iloc[validation_stop:], y.iloc[validation_stop:]

print("Training samples   :", len(X_train))
print("Validation samples :", len(X_validation))
print("Testing samples    :", len(X_test))""",
            17: """scaler = StandardScaler()
X_train_scaled = pd.DataFrame(
    scaler.fit_transform(X_train), columns=X_train.columns, index=X_train.index
)
X_validation_scaled = pd.DataFrame(
    scaler.transform(X_validation), columns=X_validation.columns, index=X_validation.index
)
X_test_scaled = pd.DataFrame(
    scaler.transform(X_test), columns=X_test.columns, index=X_test.index
)
print("Training features standardized:", X_train_scaled.shape)
print("Validation features standardized:", X_validation_scaled.shape)
print("Testing features standardized:", X_test_scaled.shape)""",
            31: """## 12. Baseline model 5: Elastic Net

Train Elastic Net in its own cell and display its holdout metrics in the next
cell, following the same structure as the other four baseline models.""",
            34: """model_comparison = pd.concat(
    [
        baseline_metrics,
        ridge_metrics,
        random_forest_metrics,
        gradient_boosting_metrics,
        elastic_net_metrics,
    ]
).sort_values("RMSE")

display(model_comparison.round(4))
print(f"Best current model by RMSE: {model_comparison.index[0]}")""",
            36: """tscv = TimeSeriesSplit(n_splits=5)
scoring = {"MAE": "neg_mean_absolute_error", "RMSE": "neg_root_mean_squared_error", "R²": "r2"}
cv_models = {
    "Linear Regression": Pipeline([("scaler", StandardScaler()), ("model", LinearRegression())]),
    "Ridge Regression": Pipeline([("scaler", StandardScaler()), ("model", Ridge(alpha=1.0))]),
    "Elastic Net": Pipeline([
        ("scaler", StandardScaler()),
        ("model", ElasticNet(alpha=0.0001, l1_ratio=0.8, max_iter=100000, tol=1e-7)),
    ]),
    "Random Forest": RandomForestRegressor(n_estimators=300, random_state=42, n_jobs=-1),
    "Gradient Boosting": GradientBoostingRegressor(
        n_estimators=100, learning_rate=0.05, max_depth=2, random_state=42
    ),
}
cv_rows = []
for model_name, model in cv_models.items():
    scores = cross_validate(model, X_train, y_train, cv=tscv, scoring=scoring)
    cv_rows.append({
        "Model": model_name,
        "CV MAE": -scores["test_MAE"].mean(),
        "CV RMSE": -scores["test_RMSE"].mean(),
        "CV R²": scores["test_R²"].mean(),
    })
cross_validation_results = pd.DataFrame(cv_rows).set_index("Model").sort_values("CV RMSE")
display(cross_validation_results.round(4))""",
            37: """## 14. Tune the nonlinear and regularised candidates

Use the same five-fold time-series validation to tune Ridge, Elastic Net,
Random Forest, and Gradient Boosting inside the TRAIN period.""",
            38: """tuning_searches = {
    "Ridge Regression": GridSearchCV(
        Pipeline([("scaler", StandardScaler()), ("model", Ridge())]),
        param_grid={"model__alpha": [0.01, 0.1, 1.0, 10.0, 100.0]},
        scoring="neg_root_mean_squared_error",
        cv=tscv,
    ),
    "Elastic Net": GridSearchCV(
        Pipeline([
            ("scaler", StandardScaler()),
            ("model", ElasticNet(max_iter=100000, tol=1e-7, random_state=42)),
        ]),
        param_grid={
            "model__alpha": [0.0001, 0.0003, 0.001, 0.003, 0.01],
            "model__l1_ratio": [0.2, 0.5, 0.8],
        },
        scoring="neg_root_mean_squared_error",
        cv=tscv,
    ),
    "Random Forest": GridSearchCV(
        RandomForestRegressor(random_state=42, n_jobs=1),
        param_grid={
            "n_estimators": [100, 200],
            "max_depth": [None, 3],
            "min_samples_leaf": [1, 2],
        },
        scoring="neg_root_mean_squared_error",
        cv=tscv,
        n_jobs=-1,
    ),
    "Gradient Boosting": GridSearchCV(
        GradientBoostingRegressor(random_state=42),
        param_grid={
            "n_estimators": [50, 100],
            "learning_rate": [0.03, 0.05],
            "max_depth": [1, 2],
        },
        scoring="neg_root_mean_squared_error",
        cv=tscv,
        n_jobs=-1,
    ),
}

tuning_rows = []
for model_name, search in tuning_searches.items():
    search.fit(X_train, y_train)
    tuning_rows.append({
        "Model": model_name,
        "Best CV RMSE": -search.best_score_,
        "Best parameters": search.best_params_,
    })

tuning_results = pd.DataFrame(tuning_rows).set_index("Model").sort_values("Best CV RMSE")
display(tuning_results)""",
            39: """## 15. Select and refit the final candidate

The canonical selection routine tunes every candidate with five training-only
time-series folds, selects the family by the later VALIDATION RMSE, refits on
TRAIN plus VALIDATION, evaluates TEST once, and exports that exact artifact.""",
            40: """final_model, evaluation = train_final_model()
final_model_name = evaluation["selected_model"]
selection_results = pd.DataFrame({
    name: {
        "Training-fold CV RMSE": result["time_series_cv_rmse"],
        "VALIDATION RMSE": result["validation"]["rmse"],
    }
    for name, result in evaluation["candidate_results"].items()
}).T.sort_values("VALIDATION RMSE")
display(selection_results)
print(f"Selected final candidate: {final_model_name}")""",
            46: """y_pred_final = final_model.predict(X_test)
final_test_metrics = pd.DataFrame({
    "MAE": [mean_absolute_error(y_test, y_pred_final)],
    "RMSE": [np.sqrt(mean_squared_error(y_test, y_pred_final))],
    "R²": [r2_score(y_test, y_pred_final)],
    "Maximum absolute error": [max_error(y_test, y_pred_final)],
}, index=[final_model_name])
final_test_predictions = pd.DataFrame({
    "timestamp": dryerMAP_model.loc[y_test.index, "timestamp"],
    "Actual moisture": y_test,
    "Predicted moisture": y_pred_final,
    "Residual (actual - predicted)": y_test - y_pred_final,
})
display(final_test_metrics.round(6))
plt.figure(figsize=(10, 5))
plt.plot(final_test_predictions["timestamp"], final_test_predictions["Actual moisture"], label="Actual")
plt.plot(final_test_predictions["timestamp"], final_test_predictions["Predicted moisture"], label="Predicted")
plt.title(f"MAP Dryer Soft Sensor: Chronological TEST — {final_model_name}")
plt.xlabel("Timestamp")
plt.ylabel("Final Moisture (%H2O)")
plt.legend()
plt.tight_layout()
plt.savefig(FIGURE_OUTPUT_DIR / "05_final_holdout_predictions.png", dpi=300, bbox_inches="tight")
plt.show()""",
            48: """train_validation_test_metrics = pd.DataFrame(evaluation["metrics"]).T
train_validation_test_metrics.insert(
    0, "Samples", [evaluation["metrics"][name]["n"] for name in ["train", "validation", "test"]]
)
display(train_validation_test_metrics.round(6))

fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
train_validation_test_metrics[["mae", "rmse"]].plot(kind="bar", ax=axes[0], rot=15)
axes[0].set_title("Error by chronological split")
axes[0].set_ylabel(f"Error ({MOISTURE_UNIT})")
train_validation_test_metrics["r2"].plot(kind="bar", ax=axes[1], rot=15, color="tab:green")
axes[1].set_title("R² by chronological split")
axes[1].axhline(0, color="black", linewidth=0.8)
fig.suptitle(f"TRAIN / VALIDATION / TEST check: {final_model_name}", y=1.02)
fig.tight_layout()
fig.savefig(FIGURE_OUTPUT_DIR / "06_train_validation_test_overfitting_check.png", dpi=300, bbox_inches="tight")
plt.show()""",
            49: """## Next step

Notebook 04 consumes the Notebook 03 evaluation record, trains the authoritative
process-only anomaly/diagnosis artifacts, and validates the complete runtime
bundle on the held-out chronological TEST replay.""",
            50: """contract_checks = validate_moisture_runtime_contract()
display(pd.Series({
    **contract_checks,
    "selected_model": evaluation["selected_model"],
    "model_artifact": evaluation["model_artifact"],
    "feature_count": evaluation["feature_count"],
    "test_replay": evaluation["test_replay"]["path"],
}, name="Notebook 03 export"))""",
        },
    )

    patch_notebook(
        "04_Model2_AnomalyDetection&Diagnosis.ipynb",
        64,
        {
            8: """## 2. Load the canonical Notebook 02/03 handoffs

The existing diagnostic analysis uses the 1,103 laboratory-aligned rows from
Notebook 02 so its figures and scenario sections remain intact. The final
cells export the authoritative process-only runtime artifacts from the full
canonical TRAIN period and validate them against Notebook 03 provenance.""",
            9: """from canonical_pipeline import ALIGNED_PATH, EVALUATION_PATH
from features.engineering import recompute_engineered_features

DATA_PATH = ALIGNED_PATH
aligned = pd.read_csv(DATA_PATH, parse_dates=["Sample Timestamp"])
moisture_evaluation = json.loads(EVALUATION_PATH.read_text(encoding="utf-8"))
if moisture_evaluation["supervised_rows"] != len(aligned):
    raise RuntimeError("Notebook 03 evaluation and Notebook 02 handoff disagree.")

dryerMAP_model = pd.DataFrame({
    "timestamp": aligned["Sample Timestamp"],
    "dryer_air_temperature": aligned["dryer_air_temperature"],
    "cooler_air_temperature": aligned["cooler_air_temperature"],
    "air_flow_rate": aligned["air_flow_rate"],
    "wet_product_feed_rate": aligned["wet_product_feed_rate"],
    "product_inlet_temperature": aligned["product_inlet_temperature"],
    "residence_time": aligned["residence_time"],
    "vacuum": aligned["vacuum"],
    "steam_pressure": aligned["steam_pressure"],
    "fan_speed": aligned["fan_speed"],
    "product_density": aligned["product_density"],
    "final_product_temp": aligned["final_product_temp"],
    "final_moisture_h2o": aligned["Final Moisture (%H2O)"],
})
dryerMAP_model.insert(0, "time", dryerMAP_model["timestamp"].dt.time.astype(str))
dryerMAP_model.insert(0, "date", dryerMAP_model["timestamp"].dt.normalize())
dryerMAP_model = recompute_engineered_features(dryerMAP_model)

print(f"Canonical aligned rows: {len(dryerMAP_model):,}")
print(f"Depends on Notebook 03: {EVALUATION_PATH.relative_to(PROJECT_ROOT)}")
display(dryerMAP_model.head())
dryerMAP_model.info()""",
            18: """## 6. Create chronological train, validation, and test sets

Use the same 70% / 15% / 15% chronological boundaries as Notebook 03. The
diagnostic exploration is never shuffled, and the final runtime export below
uses the corresponding full five-second process periods.""",
            19: """TRAIN_FRACTION = 0.70
VALIDATION_FRACTION = 0.15
ordered_anomaly_data = (
    dryerMAP_model[["timestamp", *MODEL_FEATURES]]
    .sort_values("timestamp", kind="stable")
    .reset_index(drop=True)
)
if ordered_anomaly_data["timestamp"].duplicated().any():
    raise ValueError("Duplicate timestamps are not allowed.")

train_end = moisture_evaluation["split"]["train"]["rows"]
validation_end = train_end + moisture_evaluation["split"]["validation"]["rows"]
train_data = ordered_anomaly_data.iloc[:train_end].copy()
validation_data = ordered_anomaly_data.iloc[train_end:validation_end].copy()
test_data = ordered_anomaly_data.iloc[validation_end:].copy()

X_train, train_timestamps = train_data[MODEL_FEATURES].copy(), train_data["timestamp"].copy()
X_validation = validation_data[MODEL_FEATURES].copy()
validation_timestamps = validation_data["timestamp"].copy()
X_test, test_timestamps = test_data[MODEL_FEATURES].copy(), test_data["timestamp"].copy()

split_summary = pd.DataFrame({
    "Rows": [len(train_data), len(validation_data), len(test_data)],
    "Start": [train_data.timestamp.min(), validation_data.timestamp.min(), test_data.timestamp.min()],
    "End": [train_data.timestamp.max(), validation_data.timestamp.max(), test_data.timestamp.max()],
}, index=["Reference training", "Validation", "Testing"])
display(split_summary)""",
            59: """## Prototype summary

Notebook 04 preserves the existing detector-comparison and diagnostic analysis
on the canonical laboratory-aligned handoff. The final export cells below are
authoritative for runtime: they create the 15-feature process-only One-Class
SVM, scaler, and reference profile from the canonical chronological TRAIN and
VALIDATION periods, then verify their hashes against the runtime registry.""",
            60: """## Next step

Use the held-out chronological TEST replay for PostgreSQL and Power BI. Treat
the anomaly result as synthetic novelty evidence and the diagnosis as a
verification prompt, not a confirmed plant fault or control command.""",
            61: """from canonical_pipeline import train_anomaly_and_diagnosis

runtime_anomaly_evaluation = train_anomaly_and_diagnosis()
display(pd.Series({
    "selected_model": runtime_anomaly_evaluation["selected_model"],
    "feature_count": runtime_anomaly_evaluation["feature_count"],
    "training_process_rows": runtime_anomaly_evaluation["training_process_rows"],
    "fit_sample_rows": runtime_anomaly_evaluation["fit_sample_rows"],
    "validation_sample_rows": runtime_anomaly_evaluation["validation_sample_rows"],
    "validation_flag_rate": runtime_anomaly_evaluation["validation_flag_rate"],
    "model_artifact": runtime_anomaly_evaluation["artifacts"]["model"]["path"],
}, name="Authoritative Notebook 04 runtime export"))""",
            62: """from canonical_pipeline import validate_runtime_contract

runtime_contract_checks = validate_runtime_contract()
display(pd.Series(runtime_contract_checks, name="Full NB1 → NB2 → NB3 → NB4 runtime contract"))
assert all(runtime_contract_checks.values())""",
            63: """import joblib
from canonical_pipeline import ANOMALY_MODEL_PATH, ANOMALY_SCALER_PATH, REFERENCE_PROFILE_PATH

runtime_anomaly_model = joblib.load(ANOMALY_MODEL_PATH)
runtime_anomaly_scaler = joblib.load(ANOMALY_SCALER_PATH)
print("Runtime anomaly model:", ANOMALY_MODEL_PATH)
print("Runtime anomaly scaler:", ANOMALY_SCALER_PATH)
print("Runtime reference profile:", REFERENCE_PROFILE_PATH)
print("Expected feature count:", runtime_anomaly_model.n_features_in_)
print("Ordered features:")
for position, feature in enumerate(runtime_anomaly_scaler.feature_names_in_, start=1):
    print(f"{position:02d}. {feature}")""",
        },
    )


if __name__ == "__main__":
    main()
