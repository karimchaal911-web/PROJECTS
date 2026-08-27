"""Canonical 92-day notebook-to-runtime implementation.

The public stage functions are called by Notebooks 01-04.  Keeping the
substantive logic here makes notebook execution reproducible while ensuring
the command-line checks and real-time service use the same feature contract.
"""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import ElasticNet, LinearRegression, Ridge
from sklearn.metrics import (
    max_error,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import OneClassSVM

from diagnosis.reference_profile import build_reference_profile
from multirate.preprocessing import RAW_TO_SNAKE
from multirate import (
    MOISTURE_FEATURE_NAMES,
    PROCESS_MODEL_FEATURES,
    PROCESS_VARIABLES,
    WINDOW_FEATURE_NAMES,
    build_lab_table,
    build_process_table,
    build_training_matrix,
    compute_moisture_features,
    engineer_instant_features,
    load_raw_source,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_CSV = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "MAP_Dryer_Canonical_5s.csv"
)
CANONICAL_MANIFEST = CANONICAL_CSV.with_suffix(".manifest.json")
AUDIT_PATH = PROJECT_ROOT / "artifacts" / "notebook01_canonical_audit.json"
HANDOFF_PATH = PROJECT_ROOT / "artifacts" / "notebook02_feature_handoff.json"
ALIGNED_PATH = (
    PROJECT_ROOT / "data" / "processed" / "MAP_Dryer_Lab_Aligned_16.csv"
)
EVALUATION_PATH = PROJECT_ROOT / "artifacts" / "notebook03_model_evaluation.json"
ANOMALY_EVALUATION_PATH = (
    PROJECT_ROOT / "artifacts" / "notebook04_anomaly_evaluation.json"
)
TEST_REPLAY_PATH = (
    PROJECT_ROOT / "data" / "processed" / "MAP_Dryer_TEST_Replay_5s.csv"
)
MODEL_DIR = PROJECT_ROOT / "models" / "5s"
MOISTURE_MODEL_PATH = MODEL_DIR / "quality_moisture_pipeline.joblib"
ANOMALY_MODEL_PATH = MODEL_DIR / "anomaly_model.joblib"
ANOMALY_SCALER_PATH = MODEL_DIR / "anomaly_scaler.joblib"
REFERENCE_PROFILE_PATH = MODEL_DIR / "reference_profile.json"
LEGACY_MODEL_PATH = (
    PROJECT_ROOT / "models" / "moisture_pipeline" / "moisture_pipeline.joblib"
)
FEATURE_SCHEMA_PATH = MODEL_DIR / "feature_schema.json"
TRAINING_REPORT_PATH = MODEL_DIR / "training_report.json"
MODEL_REGISTRY_PATH = PROJECT_ROOT / "models" / "model_registry.json"
PROTOTYPE_MANIFEST_PATH = PROJECT_ROOT / "models" / "prototype_manifest.json"

MODEL_VERSION = "canonical_92d_v6.0"
FEATURE_SCHEMA_VERSION = "moisture_direct_16_v6.0"
RUNTIME_COMPATIBILITY_VERSION = "map_runtime_v6"
TARGET = "Final Moisture (%H2O)"
QUALITY_COLUMNS = [
    "Product Density",
    "Final Product Temp",
    "Final Moisture (%H2O)",
]
TRAIN_FRACTION = 0.70
VALIDATION_FRACTION = 0.15
WINDOW_MINUTES = 30.0
TRANSPORT_DELAY_MINUTES = 0.0
RANDOM_STATE = 42


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def _load_manifest() -> dict[str, Any]:
    if not CANONICAL_MANIFEST.exists():
        raise FileNotFoundError(f"Canonical manifest not found: {CANONICAL_MANIFEST}")
    return json.loads(CANONICAL_MANIFEST.read_text(encoding="utf-8"))


def _relative(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT)).replace("/", "\\")


def audit_canonical_dataset() -> dict[str, Any]:
    """Notebook 01 stage: verify the canonical file and record its identity."""

    manifest = _load_manifest()
    actual_hash = file_sha256(CANONICAL_CSV)
    if actual_hash != manifest["dataset_sha256"]:
        raise RuntimeError("Canonical CSV hash does not match its manifest.")

    raw = load_raw_source(CANONICAL_CSV)
    process, process_report = build_process_table(raw)
    lab = build_lab_table(raw)
    start = process["Timestamp"].iloc[0]
    end = process["Timestamp"].iloc[-1]
    grid_days = (
        end - start + pd.Timedelta(seconds=manifest["process_interval_seconds"])
    ).total_seconds() / 86400.0
    expected_rows = 92 * 86400 // 5
    checks = {
        "exact_92_days": grid_days == 92.0,
        "exact_expected_rows": len(process) == expected_rows,
        "unique_monotonic_timestamps": bool(
            process["Timestamp"].is_unique
            and process["Timestamp"].is_monotonic_increasing
        ),
        "gap_free_5_second_grid": process_report.gap_count == 0,
        "complete_process_values": bool(
            process[PROCESS_VARIABLES].notna().all().all()
        ),
        "sparse_quality_rows": len(lab) == 1104,
    }
    if not all(checks.values()):
        raise RuntimeError(f"Canonical audit failed: {checks}")

    audit = {
        "notebook": "01_Data_Exploration.ipynb",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "canonical_dataset": _relative(CANONICAL_CSV),
        "canonical_manifest": _relative(CANONICAL_MANIFEST),
        "dataset_version": manifest["dataset_version"],
        "dataset_sha256": actual_hash,
        "duration_days": grid_days,
        "process_rows": int(len(process)),
        "process_columns": list(PROCESS_VARIABLES),
        "start_timestamp": str(start),
        "end_timestamp": str(end),
        "process_interval_seconds": 5,
        "process_interval_interpretation": (
            "prototype temporal resolution and replay cadence; not a proven "
            "PCS7 historian acquisition interval"
        ),
        "laboratory_samples": int(len(lab)),
        "laboratory_interval_minutes": 120,
        "quality_columns": QUALITY_COLUMNS,
        "checks": checks,
        "implemented_relationships": manifest["implemented_relationships"],
        "disturbance_count": len(manifest["disturbances"]),
    }
    _write_json(AUDIT_PATH, audit)
    return audit


def build_feature_handoff() -> tuple[pd.DataFrame, dict[str, Any]]:
    """Notebook 02 stage: align sparse labs to causal process snapshots."""

    if not AUDIT_PATH.exists():
        raise FileNotFoundError("Run Notebook 01 before Notebook 02.")
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    manifest = _load_manifest()
    if audit["dataset_sha256"] != manifest["dataset_sha256"]:
        raise RuntimeError("Notebook 01 audit and canonical dataset disagree.")

    raw = load_raw_source(CANONICAL_CSV)
    process, report = build_process_table(raw)
    lab = build_lab_table(raw)
    alignment = build_training_matrix(
        process,
        lab,
        window_minutes=WINDOW_MINUTES,
        transport_delay_minutes=TRANSPORT_DELAY_MINUTES,
        expected_interval_seconds=5,
    )
    lab_history = (
        lab.sort_values("Sample Timestamp", kind="stable")
        .set_index("Sample Timestamp")[["Product Density", "Final Product Temp"]]
        .shift(1)
    )
    rows: list[dict[str, float]] = []
    for timestamp in alignment.features.index:
        process_snapshot = {
            variable: alignment.features.loc[
                timestamp, f"{RAW_TO_SNAKE[variable]}__last"
            ]
            for variable in PROCESS_VARIABLES
        }
        previous_lab = lab_history.loc[timestamp]
        rows.append(
            compute_moisture_features(
                process_snapshot,
                product_density=float(previous_lab["Product Density"]),
                final_product_temp=float(previous_lab["Final Product Temp"]),
            )
        )
    features = pd.DataFrame(
        rows,
        index=alignment.features.index,
        columns=MOISTURE_FEATURE_NAMES,
    )
    aligned = features.join(alignment.targets[[TARGET]])
    aligned.index.name = "Sample Timestamp"
    ALIGNED_PATH.parent.mkdir(parents=True, exist_ok=True)
    aligned.reset_index().to_csv(ALIGNED_PATH, index=False, float_format="%.10g")
    aligned_hash = file_sha256(ALIGNED_PATH)

    handoff = {
        "notebook": "02_Feature_Engineering.ipynb",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "depends_on": _relative(AUDIT_PATH),
        "source_dataset": _relative(CANONICAL_CSV),
        "source_dataset_sha256": audit["dataset_sha256"],
        "process_rows": int(report.process_rows),
        "scheduled_laboratory_rows": int(len(lab)),
        "supervised_rows": int(len(aligned)),
        "skipped_rows": [
            {"timestamp": str(timestamp), "reason": reason}
            for timestamp, reason in alignment.skipped
        ],
        "window_minutes": WINDOW_MINUTES,
        "transport_delay_minutes": TRANSPORT_DELAY_MINUTES,
        "temporal_alignment": (
            "direct process values come from the final row at or before the "
            "lab timestamp minus residence time; density and product "
            "temperature use the most recent strictly previous lab sample"
        ),
        "feature_count": len(MOISTURE_FEATURE_NAMES),
        "feature_names": list(MOISTURE_FEATURE_NAMES),
        "available_engineered_feature_count": len(WINDOW_FEATURE_NAMES),
        "quality_fields_used_as_model_inputs": [
            "product_density",
            "final_product_temp",
        ],
        "quality_input_causality": "most recent strictly previous laboratory sample",
        "output": _relative(ALIGNED_PATH),
        "output_sha256": aligned_hash,
    }
    _write_json(HANDOFF_PATH, handoff)
    return aligned, handoff


def chronological_slices(n_rows: int) -> tuple[slice, slice, slice]:
    train_end = int(round(n_rows * TRAIN_FRACTION))
    validation_end = int(
        round(n_rows * (TRAIN_FRACTION + VALIDATION_FRACTION))
    )
    if not (0 < train_end < validation_end < n_rows):
        raise ValueError(f"Not enough rows for a 70/15/15 split: {n_rows}")
    return (
        slice(0, train_end),
        slice(train_end, validation_end),
        slice(validation_end, n_rows),
    )


def evaluation_metrics(actual: Any, predicted: Any) -> dict[str, Any]:
    actual_values = np.asarray(actual, dtype=float)
    predicted_values = np.asarray(predicted, dtype=float)
    residuals = predicted_values - actual_values
    return {
        "mae": float(mean_absolute_error(actual_values, predicted_values)),
        "rmse": float(np.sqrt(mean_squared_error(actual_values, predicted_values))),
        "r2": float(r2_score(actual_values, predicted_values)),
        "bias": float(np.mean(residuals)),
        "max_abs_error": float(max_error(actual_values, predicted_values)),
        "n": int(len(actual_values)),
    }


def _candidate_models() -> dict[str, tuple[Pipeline, dict[str, list[Any]]]]:
    return {
        "Linear Regression": (
            Pipeline(
                [("scaler", StandardScaler()), ("model", LinearRegression())]
            ),
            {},
        ),
        "Ridge": (
            Pipeline([( "scaler", StandardScaler()), ("model", Ridge())]),
            {"model__alpha": [0.01, 0.1, 1.0, 10.0, 100.0]},
        ),
        "Elastic Net": (
            Pipeline(
                [
                    ("scaler", StandardScaler()),
                    (
                        "model",
                        ElasticNet(max_iter=100000, tol=1e-7),
                    ),
                ]
            ),
            {
                "model__alpha": [0.0001, 0.0003, 0.001, 0.003, 0.01],
                "model__l1_ratio": [0.2, 0.5, 0.8],
            },
        ),
        "Random Forest": (
            Pipeline(
                [
                    (
                        "model",
                        RandomForestRegressor(
                            n_estimators=250,
                            random_state=RANDOM_STATE,
                            n_jobs=-1,
                        ),
                    )
                ]
            ),
            {
                "model__max_depth": [4, None],
                "model__min_samples_leaf": [2, 5],
            },
        ),
        "Gradient Boosting": (
            Pipeline(
                [
                    (
                        "model",
                        GradientBoostingRegressor(
                            n_estimators=200, random_state=RANDOM_STATE
                        ),
                    )
                ]
            ),
            {
                "model__learning_rate": [0.03, 0.05],
                "model__max_depth": [2, 3],
            },
        ),
    }


def _feature_metadata() -> dict[str, Any]:
    path = PROJECT_ROOT / "config" / "feature_metadata.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))["features"]
    payload["thermal_load"] = dict(
        payload["steam_temp_interaction"],
        parents=["steam_pressure", "dryer_air_temperature"],
    )
    payload["thermal_exposure"] = dict(
        payload["heating_index"],
        parents=["residence_time", "dryer_air_temperature"],
    )
    payload["cooler_delta"] = {
        "unit": "delta degC",
        "unit_status": "derived",
        "kind": "engineered",
        "parents": ["dryer_air_temperature", "cooler_air_temperature"],
        "subsystems": ["cooling_system", "thermal_system"],
        "criticality": "medium",
        "online_available": True,
        "explanation_group": "cooler_temperature",
    }
    payload["steam_per_feed"] = {
        "unit": "bar/(m3/h)",
        "unit_status": "derived",
        "kind": "engineered",
        "parents": ["steam_pressure", "wet_product_feed_rate"],
        "subsystems": ["thermal_system", "feed_loading"],
        "criticality": "medium",
        "online_available": True,
        "explanation_group": "thermal_energy",
    }
    return payload


def _train_anomaly_artifacts(
    process: pd.DataFrame,
    train_end: pd.Timestamp,
    validation_end: pd.Timestamp,
) -> dict[str, Any]:
    train_raw = process.loc[process["Timestamp"] <= train_end, PROCESS_VARIABLES]
    validation_raw = process.loc[
        (process["Timestamp"] > train_end)
        & (process["Timestamp"] <= validation_end),
        PROCESS_VARIABLES,
    ]
    instant_train = engineer_instant_features(train_raw)
    instant_validation = engineer_instant_features(validation_raw)
    scaler = StandardScaler().fit(instant_train)
    stride = max(len(instant_train) // 6000, 1)
    fit_sample = instant_train.iloc[::stride].head(6000)
    detector = OneClassSVM(kernel="rbf", gamma="scale", nu=0.02).fit(
        scaler.transform(fit_sample)
    )
    validation_stride = max(len(instant_validation) // 20000, 1)
    validation_sample = instant_validation.iloc[::validation_stride].head(20000)
    validation_scaled = scaler.transform(validation_sample)
    decision = detector.decision_function(validation_scaled)
    scale = max(float(np.median(np.abs(decision))), 1e-6)
    validation_flag_rate = float(np.mean(detector.predict(validation_scaled) == -1))

    profile = build_reference_profile(instant_train, _feature_metadata())
    profile_payload = profile.as_dict()
    profile_payload["profile_version"] = "reference_profile_5s_v6.0"

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(detector, ANOMALY_MODEL_PATH)
    joblib.dump(scaler, ANOMALY_SCALER_PATH)
    _write_json(REFERENCE_PROFILE_PATH, profile_payload)
    return {
        "selected_model": "One-Class SVM",
        "training_process_rows": int(len(instant_train)),
        "fit_sample_rows": int(len(fit_sample)),
        "validation_sample_rows": int(len(validation_sample)),
        "validation_flag_rate": validation_flag_rate,
        "nu": 0.02,
        "risk_calibration": {
            "method": "logistic_decision_function_display_scale",
            "score_scale": scale,
            "risk_at_boundary": 0.5,
            "risk_warning_threshold": 0.5,
            "risk_critical_threshold": 0.8,
            "is_probability": False,
        },
    }


def train_anomaly_and_diagnosis() -> dict[str, Any]:
    """Notebook 04 stage: export the runtime anomaly and diagnosis contract."""

    if not EVALUATION_PATH.exists():
        raise FileNotFoundError("Run Notebook 03 before Notebook 04.")
    moisture = json.loads(EVALUATION_PATH.read_text(encoding="utf-8"))
    manifest = _load_manifest()
    if moisture["canonical_dataset_sha256"] != manifest["dataset_sha256"]:
        raise RuntimeError("Notebook 03 and the canonical dataset hash do not match.")

    train_end = pd.Timestamp(moisture["split"]["train"]["end_timestamp"])
    validation_end = pd.Timestamp(
        moisture["split"]["validation"]["end_timestamp"]
    )
    raw = load_raw_source(CANONICAL_CSV)
    process, _ = build_process_table(raw)
    anomaly = _train_anomaly_artifacts(process, train_end, validation_end)
    del raw, process

    evaluation = {
        "notebook": "04_Model2_AnomalyDetection&Diagnosis.ipynb",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "depends_on": _relative(EVALUATION_PATH),
        "canonical_dataset": _relative(CANONICAL_CSV),
        "canonical_dataset_sha256": manifest["dataset_sha256"],
        "source_partition": "chronological TRAIN with VALIDATION check",
        "feature_count": len(PROCESS_MODEL_FEATURES),
        "feature_names": list(PROCESS_MODEL_FEATURES),
        **anomaly,
        "artifacts": {
            "model": {
                "path": _relative(ANOMALY_MODEL_PATH),
                "sha256": file_sha256(ANOMALY_MODEL_PATH),
            },
            "scaler": {
                "path": _relative(ANOMALY_SCALER_PATH),
                "sha256": file_sha256(ANOMALY_SCALER_PATH),
            },
            "reference_profile": {
                "path": _relative(REFERENCE_PROFILE_PATH),
                "sha256": file_sha256(REFERENCE_PROFILE_PATH),
            },
        },
        "diagnosis_contract": {
            "method": "robust reference quantiles plus ranked direct contributors",
            "operator_boundary": "evidence localization, not proven causality",
            "runtime_module": "realtime_pipeline/src/diagnosis_engine.py",
        },
        "held_out_replay": moisture["test_replay"],
        "runtime_loads_exact_notebook04_artifacts": True,
        "prototype_limitation": (
            "Synthetic novelty evidence only; no confirmed plant fault labels."
        ),
    }
    _write_json(ANOMALY_EVALUATION_PATH, evaluation)

    schema = json.loads(FEATURE_SCHEMA_PATH.read_text(encoding="utf-8"))
    schema.update(
        {
            "anomaly_source_notebook": (
                "notebooks/04_Model2_AnomalyDetection&Diagnosis.ipynb"
            ),
            "anomaly_model_features": list(PROCESS_MODEL_FEATURES),
            "anomaly_feature_count": len(PROCESS_MODEL_FEATURES),
            "anomaly_risk_calibration": anomaly["risk_calibration"],
            "anomaly_model_artifact_sha256": evaluation["artifacts"]["model"][
                "sha256"
            ],
        }
    )
    _write_json(FEATURE_SCHEMA_PATH, schema)

    training_report = json.loads(TRAINING_REPORT_PATH.read_text(encoding="utf-8"))
    training_report["anomaly"] = {
        **anomaly,
        "source_notebook": evaluation["notebook"],
        "evaluation_record": _relative(ANOMALY_EVALUATION_PATH),
        "feature_count": len(PROCESS_MODEL_FEATURES),
        "feature_names": list(PROCESS_MODEL_FEATURES),
        "artifacts": evaluation["artifacts"],
    }
    _write_json(TRAINING_REPORT_PATH, training_report)

    registry = json.loads(MODEL_REGISTRY_PATH.read_text(encoding="utf-8"))
    anomaly_entry = {
        "model_id": "anomaly_detector_canonical_92d_v6.0",
        "status": "runtime-demo",
        "artifact_path": _relative(ANOMALY_MODEL_PATH),
        "artifact_sha256": evaluation["artifacts"]["model"]["sha256"],
        "scaler_path": _relative(ANOMALY_SCALER_PATH),
        "scaler_sha256": evaluation["artifacts"]["scaler"]["sha256"],
        "reference_profile_path": _relative(REFERENCE_PROFILE_PATH),
        "reference_profile_sha256": evaluation["artifacts"]["reference_profile"][
            "sha256"
        ],
        "feature_count": len(PROCESS_MODEL_FEATURES),
        "feature_names": list(PROCESS_MODEL_FEATURES),
        "training_dataset_sha256": manifest["dataset_sha256"],
        "model_family": anomaly["selected_model"],
        "source_notebook": (
            "notebooks/04_Model2_AnomalyDetection&Diagnosis.ipynb"
        ),
        "runtime_uses_exact_notebook04_artifacts": True,
        "validation_flag_rate": anomaly["validation_flag_rate"],
        "held_out_replay": moisture["test_replay"],
    }
    registry["models"] = [
        item
        for item in registry["models"]
        if not item["model_id"].startswith("anomaly_detector_")
    ] + [anomaly_entry]
    _write_json(MODEL_REGISTRY_PATH, registry)

    metadata_path = PROJECT_ROOT / "models" / "model_metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["anomaly_pipeline"] = {
        "detector_name": "OneClassSVM",
        "detector_parameters": {"gamma": "scale", "nu": 0.02},
        "source_notebook": evaluation["notebook"],
        "feature_count": len(PROCESS_MODEL_FEATURES),
        "artifact_sha256": evaluation["artifacts"]["model"]["sha256"],
    }
    _write_json(metadata_path, metadata)

    prototype_manifest = json.loads(
        PROTOTYPE_MANIFEST_PATH.read_text(encoding="utf-8")
    )
    prototype_manifest["anomaly_contract"] = {
        "source_notebook": evaluation["notebook"],
        "evaluation_record": _relative(ANOMALY_EVALUATION_PATH),
        "artifact_sha256": evaluation["artifacts"]["model"]["sha256"],
        "feature_count": len(PROCESS_MODEL_FEATURES),
    }
    prototype_manifest["feature_schema"]["sha256"] = file_sha256(
        FEATURE_SCHEMA_PATH
    )
    prototype_manifest["training_report"]["sha256"] = file_sha256(
        TRAINING_REPORT_PATH
    )
    prototype_manifest["model_registry"]["sha256"] = file_sha256(
        MODEL_REGISTRY_PATH
    )
    _write_json(PROTOTYPE_MANIFEST_PATH, prototype_manifest)
    return evaluation


def _export_test_replay(test_start: pd.Timestamp) -> dict[str, Any]:
    TEST_REPLAY_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = TEST_REPLAY_PATH.with_suffix(".generating.csv")
    if temporary.exists():
        temporary.unlink()
    wrote_header = False
    row_count = 0
    lab_count = 0
    first_timestamp: pd.Timestamp | None = None
    last_timestamp: pd.Timestamp | None = None
    for chunk in pd.read_csv(CANONICAL_CSV, chunksize=200_000):
        timestamps = pd.to_datetime(
            chunk["Date"] + " " + chunk["Time"],
            format="%Y-%m-%d %H:%M:%S",
        )
        selected = chunk.loc[timestamps >= test_start].copy()
        if selected.empty:
            continue
        selected.insert(len(selected.columns), "Replay Partition", "test")
        selected.to_csv(
            temporary,
            mode="a",
            header=not wrote_header,
            index=False,
            float_format="%.6f",
        )
        selected_timestamps = timestamps.loc[selected.index]
        if first_timestamp is None:
            first_timestamp = selected_timestamps.iloc[0]
        last_timestamp = selected_timestamps.iloc[-1]
        row_count += len(selected)
        lab_count += int(selected[TARGET].notna().sum())
        wrote_header = True
    if not wrote_header:
        raise RuntimeError("The held-out test replay export is empty.")
    temporary.replace(TEST_REPLAY_PATH)
    return {
        "path": _relative(TEST_REPLAY_PATH),
        "sha256": file_sha256(TEST_REPLAY_PATH),
        "rows": int(row_count),
        "laboratory_samples": int(lab_count),
        "start_timestamp": str(first_timestamp),
        "end_timestamp": str(last_timestamp),
        "source_dataset": _relative(CANONICAL_CSV),
        "source_partition": "held-out chronological TEST",
    }


def _create_model_figures(
    candidate_report: dict[str, Any],
    test_timestamps: pd.Series,
    y_test: pd.Series,
    test_predictions: np.ndarray,
    model: Pipeline,
) -> None:
    output = PROJECT_ROOT / "figures" / "03_Model1_SoftSensor"
    output.mkdir(parents=True, exist_ok=True)
    names = list(candidate_report)
    validation_rmse = [candidate_report[name]["validation"]["rmse"] for name in names]
    fig, axis = plt.subplots(figsize=(9, 4.8))
    axis.bar(names, validation_rmse, color="#127C64")
    axis.set_ylabel("Validation RMSE (% H2O)")
    axis.set_title("Chronological validation comparison")
    axis.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    fig.savefig(output / "02_candidate_validation.png", dpi=180)
    plt.close(fig)

    fig, axis = plt.subplots(figsize=(10, 4.8))
    axis.plot(test_timestamps, y_test, label="Laboratory moisture", linewidth=1.4)
    axis.plot(test_timestamps, test_predictions, label="Model prediction", linewidth=1.2)
    axis.set_ylabel("Final moisture (% H2O)")
    axis.set_title("Held-out chronological TEST predictions")
    axis.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(output / "05_final_holdout_predictions.png", dpi=180)
    plt.close(fig)

    estimator = model.named_steps["model"]
    if hasattr(estimator, "coef_"):
        importance = np.abs(np.ravel(estimator.coef_))
        label = "Absolute standardized coefficient"
    elif hasattr(estimator, "feature_importances_"):
        importance = np.asarray(estimator.feature_importances_)
        label = "Model feature importance"
    else:
        return
    order = np.argsort(importance)
    fig, axis = plt.subplots(figsize=(9, 6.5))
    axis.barh(np.asarray(MOISTURE_FEATURE_NAMES)[order], importance[order], color="#127C64")
    axis.set_xlabel(label)
    axis.set_title("Selected Notebook 03 model: 16-feature importance")
    fig.tight_layout()
    fig.savefig(output / "02_selected_model_feature_importance.png", dpi=180)
    plt.close(fig)


def train_final_model() -> tuple[Pipeline, dict[str, Any]]:
    """Notebook 03 stage: select, evaluate and export the runtime model."""

    if not HANDOFF_PATH.exists() or not ALIGNED_PATH.exists():
        raise FileNotFoundError("Run Notebook 02 before Notebook 03.")
    handoff = json.loads(HANDOFF_PATH.read_text(encoding="utf-8"))
    if handoff["output_sha256"] != file_sha256(ALIGNED_PATH):
        raise RuntimeError("Notebook 02 handoff hash does not match its table.")
    if handoff["feature_names"] != MOISTURE_FEATURE_NAMES:
        raise RuntimeError("Notebook 02 feature contract is not the final 16-feature schema.")

    aligned = pd.read_csv(ALIGNED_PATH, parse_dates=["Sample Timestamp"])
    aligned = aligned.sort_values("Sample Timestamp", kind="stable").reset_index(drop=True)
    X = aligned.loc[:, MOISTURE_FEATURE_NAMES]
    y = pd.to_numeric(aligned[TARGET], errors="raise")
    train_slice, validation_slice, test_slice = chronological_slices(len(aligned))
    X_train, y_train = X.iloc[train_slice], y.iloc[train_slice]
    X_validation, y_validation = X.iloc[validation_slice], y.iloc[validation_slice]
    X_test, y_test = X.iloc[test_slice], y.iloc[test_slice]
    tscv = TimeSeriesSplit(n_splits=5)

    candidates: dict[str, Any] = {}
    best_name: str | None = None
    best_estimator: Pipeline | None = None
    best_validation_rmse = np.inf
    for name, (pipeline, grid) in _candidate_models().items():
        search = GridSearchCV(
            pipeline,
            param_grid=grid,
            cv=tscv,
            scoring="neg_root_mean_squared_error",
            n_jobs=-1,
            refit=True,
        )
        search.fit(X_train, y_train)
        validation_prediction = search.best_estimator_.predict(X_validation)
        validation_metrics = evaluation_metrics(y_validation, validation_prediction)
        candidates[name] = {
            "best_parameters": search.best_params_,
            "time_series_cv_rmse": float(-search.best_score_),
            "validation": validation_metrics,
        }
        if validation_metrics["rmse"] < best_validation_rmse:
            best_validation_rmse = validation_metrics["rmse"]
            best_name = name
            best_estimator = copy.deepcopy(search.best_estimator_)

    if best_name is None or best_estimator is None:
        raise RuntimeError("No candidate model was selected.")

    development_model = copy.deepcopy(best_estimator)
    development_model.fit(X_train, y_train)
    training_metrics = evaluation_metrics(
        y_train, development_model.predict(X_train)
    )
    validation_metrics = evaluation_metrics(
        y_validation, development_model.predict(X_validation)
    )
    X_fit = pd.concat([X_train, X_validation], axis=0)
    y_fit = pd.concat([y_train, y_validation], axis=0)
    final_model = copy.deepcopy(best_estimator)
    final_model.fit(X_fit, y_fit)
    test_predictions = final_model.predict(X_test)
    test_metrics = evaluation_metrics(y_test, test_predictions)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(final_model, MOISTURE_MODEL_PATH)
    LEGACY_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(MOISTURE_MODEL_PATH, LEGACY_MODEL_PATH)

    timestamps = aligned["Sample Timestamp"]
    train_end = timestamps.iloc[train_slice.stop - 1]
    validation_start = timestamps.iloc[validation_slice.start]
    validation_end = timestamps.iloc[validation_slice.stop - 1]
    test_start = timestamps.iloc[test_slice.start]
    test_end = timestamps.iloc[test_slice.stop - 1]
    split = {
        "strategy": "chronological TRAIN -> VALIDATION -> TEST",
        "train": {
            "rows": int(len(X_train)),
            "proportion": len(X_train) / len(X),
            "start_timestamp": str(timestamps.iloc[0]),
            "end_timestamp": str(train_end),
        },
        "validation": {
            "rows": int(len(X_validation)),
            "proportion": len(X_validation) / len(X),
            "start_timestamp": str(validation_start),
            "end_timestamp": str(validation_end),
        },
        "test": {
            "rows": int(len(X_test)),
            "proportion": len(X_test) / len(X),
            "start_timestamp": str(test_start),
            "end_timestamp": str(test_end),
        },
        "time_series_cross_validation": {
            "used": True,
            "n_splits": 5,
            "scope": "training segment only",
        },
    }

    raw = load_raw_source(CANONICAL_CSV)
    process, _ = build_process_table(raw)
    anomaly = _train_anomaly_artifacts(process, train_end, validation_end)
    del raw, process
    test_replay = _export_test_replay(test_start)

    evaluation = {
        "notebook": "03_Model1_SoftSensor.ipynb",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "depends_on": _relative(HANDOFF_PATH),
        "canonical_dataset": _relative(CANONICAL_CSV),
        "canonical_dataset_sha256": handoff["source_dataset_sha256"],
        "supervised_rows": int(len(X)),
        "target": TARGET,
        "target_unit": "percentage points (% H2O)",
        "feature_count": len(MOISTURE_FEATURE_NAMES),
        "feature_names": list(MOISTURE_FEATURE_NAMES),
        "split": split,
        "candidate_results": candidates,
        "selected_model": best_name,
        "selected_parameters": candidates[best_name]["best_parameters"],
        "metrics": {
            "train": training_metrics,
            "validation": validation_metrics,
            "test": test_metrics,
        },
        "model_artifact": _relative(MOISTURE_MODEL_PATH),
        "model_artifact_sha256": file_sha256(MOISTURE_MODEL_PATH),
        "runtime_loads_exact_notebook03_artifact": True,
        "test_replay": test_replay,
        "prototype_limitation": (
            "Synthetic prototype evidence only; industrial qualification "
            "requires representative historian and laboratory data."
        ),
    }
    _write_json(EVALUATION_PATH, evaluation)

    feature_schema = {
        "model_version": MODEL_VERSION,
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "runtime_compatibility_version": RUNTIME_COMPATIBILITY_VERSION,
        "created_at": evaluation["created_at"],
        "process_interval_seconds": 5,
        "process_interval_interpretation": (
            "prototype temporal resolution and replay cadence"
        ),
        "quality_window_minutes": WINDOW_MINUTES,
        "transport_delay_minutes": TRANSPORT_DELAY_MINUTES,
        "residence_time_unit": "minutes",
        "expected_feature_count": len(MOISTURE_FEATURE_NAMES),
        "moisture_model_features": list(MOISTURE_FEATURE_NAMES),
        "available_window_feature_names": list(WINDOW_FEATURE_NAMES),
        # Compatibility key: runtime verifies the feature-engineering universe.
        "window_feature_names": list(WINDOW_FEATURE_NAMES),
        "process_model_features": list(PROCESS_MODEL_FEATURES),
        "targets": {"moisture": TARGET},
        "quality_selected_models": {"moisture": best_name},
        "source_notebook": "notebooks/03_Model1_SoftSensor.ipynb",
        "laboratory_quality_inputs": [
            "product_density",
            "final_product_temp",
        ],
        "laboratory_quality_input_timing": (
            "most recent strictly previous laboratory sample"
        ),
        "anomaly_risk_calibration": anomaly["risk_calibration"],
    }
    _write_json(FEATURE_SCHEMA_PATH, feature_schema)

    training_report = {
        "created_at": evaluation["created_at"],
        "model_version": MODEL_VERSION,
        "canonical_dataset": _relative(CANONICAL_CSV),
        "dataset_version": _load_manifest()["dataset_version"],
        "dataset_sha256": handoff["source_dataset_sha256"],
        "duration_days": 92,
        "process_rows": int(_load_manifest()["row_count"]),
        "laboratory_samples": int(_load_manifest()["laboratory_observations"]),
        "supervised_rows": int(len(X)),
        "notebook01_audit": json.loads(AUDIT_PATH.read_text(encoding="utf-8")),
        "notebook02_handoff": handoff,
        "quality": {
            "moisture": {
                "selected_model": best_name,
                "feature_count": len(MOISTURE_FEATURE_NAMES),
                "feature_names": list(MOISTURE_FEATURE_NAMES),
                "candidates": candidates,
                "split": split,
                "metrics": evaluation["metrics"],
                "test_replay": test_replay,
            }
        },
        "anomaly": anomaly,
    }
    _write_json(TRAINING_REPORT_PATH, training_report)

    registry = {
        "registry_version": "6.0",
        "active_runtime_compatibility_version": RUNTIME_COMPATIBILITY_VERSION,
        "active_dataset": {
            "path": _relative(CANONICAL_CSV),
            "version": _load_manifest()["dataset_version"],
            "sha256": handoff["source_dataset_sha256"],
        },
        "models": [
            {
                "model_id": "moisture_soft_sensor_canonical_92d_v6.0",
                "status": "runtime-demo",
                "artifact_path": _relative(MOISTURE_MODEL_PATH),
                "artifact_sha256": evaluation["model_artifact_sha256"],
                "feature_schema": _relative(FEATURE_SCHEMA_PATH),
                "feature_schema_version": FEATURE_SCHEMA_VERSION,
                "feature_count": len(MOISTURE_FEATURE_NAMES),
                "source_notebook": "notebooks/03_Model1_SoftSensor.ipynb",
                "runtime_uses_exact_notebook03_artifact": True,
                "training_dataset_sha256": handoff["source_dataset_sha256"],
                "model_family": best_name,
                "test_metrics": test_metrics,
                "test_replay": test_replay,
            },
            {
                "model_id": "anomaly_detector_canonical_92d_v6.0",
                "status": "runtime-demo",
                "artifact_path": _relative(MODEL_DIR / "anomaly_model.joblib"),
                "feature_count": len(PROCESS_MODEL_FEATURES),
                "training_dataset_sha256": handoff["source_dataset_sha256"],
                "model_family": "One-Class SVM",
            },
        ],
    }
    _write_json(MODEL_REGISTRY_PATH, registry)
    prototype_manifest = {
        "prototype_manifest_version": "6.0",
        "classification": "engineering prototype / proof of concept",
        "dataset": registry["active_dataset"],
        "feature_schema": {
            "path": _relative(FEATURE_SCHEMA_PATH),
            "sha256": file_sha256(FEATURE_SCHEMA_PATH),
            "version": FEATURE_SCHEMA_VERSION,
            "feature_count": len(MOISTURE_FEATURE_NAMES),
        },
        "training_report": {
            "path": _relative(TRAINING_REPORT_PATH),
            "sha256": file_sha256(TRAINING_REPORT_PATH),
        },
        "model_registry": {
            "path": _relative(MODEL_REGISTRY_PATH),
            "sha256": file_sha256(MODEL_REGISTRY_PATH),
        },
        "runtime_compatibility_version": RUNTIME_COMPATIBILITY_VERSION,
        "dashboard_contract": {
            "mode": "PostgreSQL DirectQuery",
            "prototype_refresh_seconds": 5,
            "data_source_label": "PROTOTYPE / HELD-OUT TEST REPLAY",
            "replay": test_replay,
        },
    }
    _write_json(PROTOTYPE_MANIFEST_PATH, prototype_manifest)
    _write_json(
        PROJECT_ROOT / "models" / "model_metadata.json",
        {
            "moisture_pipeline": {
                "model_class": type(final_model).__name__,
                "selected_model": best_name,
                "path": _relative(MOISTURE_MODEL_PATH),
                "features": list(MOISTURE_FEATURE_NAMES),
                "feature_count": len(MOISTURE_FEATURE_NAMES),
            },
            "anomaly_pipeline": {
                "detector_name": "OneClassSVM",
                "detector_parameters": {"gamma": "scale", "nu": 0.02},
            },
        },
    )
    _create_model_figures(
        candidates,
        timestamps.iloc[test_slice],
        y_test,
        test_predictions,
        final_model,
    )
    return final_model, evaluation


def validate_moisture_runtime_contract() -> dict[str, Any]:
    """Read-only Notebook 03 moisture-artifact and replay check."""

    evaluation = json.loads(EVALUATION_PATH.read_text(encoding="utf-8"))
    schema = json.loads(FEATURE_SCHEMA_PATH.read_text(encoding="utf-8"))
    registry = json.loads(MODEL_REGISTRY_PATH.read_text(encoding="utf-8"))
    model = joblib.load(MOISTURE_MODEL_PATH)
    checks = {
        "feature_count_16": schema["expected_feature_count"] == 16,
        "schema_order_matches": schema["moisture_model_features"]
        == MOISTURE_FEATURE_NAMES,
        "model_input_order_matches": list(model.feature_names_in_)
        == MOISTURE_FEATURE_NAMES,
        "artifact_hash_matches": file_sha256(MOISTURE_MODEL_PATH)
        == evaluation["model_artifact_sha256"],
        "runtime_same_notebook03_artifact": registry["models"][0][
            "runtime_uses_exact_notebook03_artifact"
        ],
        "test_replay_exists": TEST_REPLAY_PATH.exists(),
        "test_replay_is_derived_from_canonical": evaluation["test_replay"][
            "source_dataset"
        ]
        == _relative(CANONICAL_CSV),
    }
    if not all(checks.values()):
        raise RuntimeError(f"Moisture runtime contract validation failed: {checks}")
    return checks


def validate_runtime_contract() -> dict[str, Any]:
    """Read-only full Notebook 03 + Notebook 04 runtime contract check."""

    checks = validate_moisture_runtime_contract()
    if not ANOMALY_EVALUATION_PATH.exists():
        raise FileNotFoundError("Run Notebook 04 before full runtime validation.")
    anomaly = json.loads(ANOMALY_EVALUATION_PATH.read_text(encoding="utf-8"))
    schema = json.loads(FEATURE_SCHEMA_PATH.read_text(encoding="utf-8"))
    registry = json.loads(MODEL_REGISTRY_PATH.read_text(encoding="utf-8"))
    scaler = joblib.load(ANOMALY_SCALER_PATH)
    detector = joblib.load(ANOMALY_MODEL_PATH)
    anomaly_registry = next(
        item
        for item in registry["models"]
        if item["model_id"].startswith("anomaly_detector_")
    )
    anomaly_checks = {
        "notebook04_depends_on_notebook03": anomaly["depends_on"]
        == _relative(EVALUATION_PATH),
        "anomaly_feature_order_matches": list(scaler.feature_names_in_)
        == PROCESS_MODEL_FEATURES,
        "anomaly_detector_feature_count_matches": detector.n_features_in_
        == len(PROCESS_MODEL_FEATURES),
        "anomaly_artifact_hash_matches": file_sha256(ANOMALY_MODEL_PATH)
        == anomaly["artifacts"]["model"]["sha256"],
        "anomaly_scaler_hash_matches": file_sha256(ANOMALY_SCALER_PATH)
        == anomaly["artifacts"]["scaler"]["sha256"],
        "reference_profile_hash_matches": file_sha256(REFERENCE_PROFILE_PATH)
        == anomaly["artifacts"]["reference_profile"]["sha256"],
        "runtime_same_notebook04_artifacts": anomaly_registry.get(
            "runtime_uses_exact_notebook04_artifacts",
            anomaly["runtime_loads_exact_notebook04_artifacts"],
        ),
        "schema_names_notebook04": schema.get(
            "anomaly_source_notebook", f"notebooks/{anomaly['notebook']}"
        )
        == "notebooks/04_Model2_AnomalyDetection&Diagnosis.ipynb",
        "anomaly_replay_is_held_out_test": anomaly["held_out_replay"][
            "source_partition"
        ]
        == "held-out chronological TEST",
    }
    checks.update(anomaly_checks)
    if not all(checks.values()):
        raise RuntimeError(f"Full runtime contract validation failed: {checks}")
    return checks
