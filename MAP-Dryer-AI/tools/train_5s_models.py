"""Train the 5-second prototype models from the multi-rate training dataset.

Produces, under ``models/5s/``:

* three laboratory-quality regression pipelines (Final Moisture, Product
  Density, Final Product Temp) trained on residence-time-shifted process
  windows — one supervised row per real laboratory sample, chronological
  70/15/15 split, no shuffling, no forward-filled targets;
* a process-only anomaly detector (One-Class SVM + scaler) that runs on
  every 5-second observation without laboratory values, benchmarked against
  an Isolation Forest;
* ``reference_profile.json`` (v2, process-only) for the diagnosis engine;
* ``feature_schema.json`` and ``training_report.json`` so the real-time
  service can verify model/feature versions at startup.

Run from the repository root:

    realtime_pipeline/.venv/Scripts/python.exe tools/train_5s_models.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
for entry in (str(PROJECT_ROOT), str(PROJECT_ROOT / "src")):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from sklearn.ensemble import (  # noqa: E402
    GradientBoostingRegressor,
    IsolationForest,
    RandomForestRegressor,
)
from sklearn.linear_model import ElasticNet, Ridge  # noqa: E402
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit  # noqa: E402
from sklearn.pipeline import Pipeline  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402
from sklearn.svm import OneClassSVM  # noqa: E402

from multirate import (  # noqa: E402
    PROCESS_MODEL_FEATURES,
    WINDOW_FEATURE_NAMES,
    build_lab_table,
    build_process_table,
    build_training_matrix,
    engineer_instant_features,
    load_raw_source,
)
from multirate.alignment import (  # noqa: E402
    DEFAULT_TRANSPORT_DELAY_MINUTES,
    DEFAULT_WINDOW_MINUTES,
)

TRAINING_CSV = (
    PROJECT_ROOT
    / "resources"
    / "prototype_data"
    / "MAP_Dryer_5s_Training_Original_Columns.csv"
)
OLD_REFERENCE_PROFILE = (
    PROJECT_ROOT / "models" / "anomaly_pipeline" / "reference_profile.json"
)
DIAGNOSTIC_BUNDLE_METADATA = (
    PROJECT_ROOT
    / "models"
    / "diagnosis"
    / "diagnostic_bundle_metadata.diag_v1.0.json"
)
OUTPUT_DIR = PROJECT_ROOT / "models" / "5s"

MODEL_VERSION = "5s_v1.0"
FEATURE_SCHEMA_VERSION = "5s_features_v1.0"

TARGETS = {
    "moisture": "Final Moisture (%H2O)",
    "density": "Product Density",
    "product_temp": "Final Product Temp",
}

TRAIN_FRACTION = 0.70
VALIDATION_FRACTION = 0.15

# One-Class SVM cost grows quadratically with rows; a uniform chronological
# subsample of the training portion keeps fitting tractable while preserving
# the operating envelope.
OCSVM_MAX_TRAINING_ROWS = 6000
ANOMALY_NU = 0.02

RANDOM_STATE = 42


def evaluation_metrics(actual: np.ndarray, predicted: np.ndarray) -> dict:
    residuals = predicted - actual
    return {
        "mae": float(np.mean(np.abs(residuals))),
        "rmse": float(np.sqrt(np.mean(residuals**2))),
        "r2": float(
            1.0
            - np.sum(residuals**2)
            / max(np.sum((actual - np.mean(actual)) ** 2), 1e-12)
        ),
        "bias": float(np.mean(residuals)),
        "max_abs_error": float(np.max(np.abs(residuals))),
        "n": int(len(actual)),
    }


def candidate_models() -> dict[str, tuple[Pipeline, dict]]:
    return {
        "ridge": (
            Pipeline(
                [("scaler", StandardScaler()), ("model", Ridge())]
            ),
            {"model__alpha": [0.1, 1.0, 10.0, 100.0]},
        ),
        "elastic_net": (
            Pipeline(
                [
                    ("scaler", StandardScaler()),
                    ("model", ElasticNet(max_iter=100000)),
                ]
            ),
            {
                "model__alpha": [0.001, 0.01, 0.1, 1.0],
                "model__l1_ratio": [0.2, 0.5, 0.8],
            },
        ),
        "random_forest": (
            Pipeline(
                [
                    (
                        "model",
                        RandomForestRegressor(
                            n_estimators=400,
                            random_state=RANDOM_STATE,
                            n_jobs=-1,
                        ),
                    )
                ]
            ),
            {
                "model__max_depth": [None, 5, 10],
                "model__min_samples_leaf": [1, 3],
            },
        ),
        "gradient_boosting": (
            Pipeline(
                [
                    (
                        "model",
                        GradientBoostingRegressor(
                            n_estimators=300, random_state=RANDOM_STATE
                        ),
                    )
                ]
            ),
            {
                "model__learning_rate": [0.05, 0.1],
                "model__max_depth": [2, 3],
            },
        ),
    }


def chronological_split(n_rows: int) -> tuple[slice, slice, slice]:
    train_end = int(round(n_rows * TRAIN_FRACTION))
    validation_end = int(
        round(n_rows * (TRAIN_FRACTION + VALIDATION_FRACTION))
    )
    return (
        slice(0, train_end),
        slice(train_end, validation_end),
        slice(validation_end, n_rows),
    )


def residual_track(
    index: pd.DatetimeIndex, actual: np.ndarray, predicted: np.ndarray
) -> list[dict]:
    return [
        {
            "timestamp": str(timestamp),
            "actual": float(a),
            "predicted": float(p),
            "residual": float(p - a),
        }
        for timestamp, a, p in zip(index, actual, predicted)
    ]


def train_quality_models(
    features: pd.DataFrame, targets: pd.DataFrame
) -> tuple[dict[str, Pipeline], dict]:
    report: dict = {}
    fitted: dict[str, Pipeline] = {}

    n_rows = len(features)
    train_slice, validation_slice, test_slice = chronological_split(n_rows)
    split_summary = {
        "train_rows": train_slice.stop - train_slice.start,
        "validation_rows": validation_slice.stop - validation_slice.start,
        "test_rows": test_slice.stop - test_slice.start,
        "train_end": str(features.index[train_slice.stop - 1]),
        "validation_end": str(features.index[validation_slice.stop - 1]),
    }

    for short_name, target_column in TARGETS.items():
        mask = targets[target_column].notna().to_numpy()
        x_all = features.loc[mask]
        y_all = targets.loc[mask, target_column].to_numpy(dtype=float)
        index_all = x_all.index

        t_slice, v_slice, s_slice = chronological_split(len(x_all))
        x_train, y_train = x_all.iloc[t_slice], y_all[t_slice]
        x_validation, y_validation = x_all.iloc[v_slice], y_all[v_slice]
        x_test, y_test = x_all.iloc[s_slice], y_all[s_slice]

        target_report: dict = {"candidates": {}}

        # Defensible floor: persistence (previous laboratory value) and the
        # training mean. A model must beat these to justify itself.
        previous_values = np.concatenate(([np.nan], y_all[:-1]))
        persistence_mask = ~np.isnan(previous_values[v_slice])
        target_report["baselines"] = {
            "persistence_validation": evaluation_metrics(
                y_validation[persistence_mask],
                previous_values[v_slice][persistence_mask],
            ),
            "train_mean_validation": evaluation_metrics(
                y_validation,
                np.full_like(y_validation, float(np.mean(y_train))),
            ),
        }

        best_name = None
        best_rmse = np.inf
        best_estimator = None

        for name, (pipeline, grid) in candidate_models().items():
            search = GridSearchCV(
                pipeline,
                grid,
                cv=TimeSeriesSplit(n_splits=4),
                scoring="neg_root_mean_squared_error",
                n_jobs=-1,
            )
            search.fit(x_train, y_train)
            validation_prediction = search.best_estimator_.predict(
                x_validation
            )
            metrics = evaluation_metrics(y_validation, validation_prediction)
            target_report["candidates"][name] = {
                "best_params": search.best_params_,
                "validation": metrics,
            }
            if metrics["rmse"] < best_rmse:
                best_rmse = metrics["rmse"]
                best_name = name
                best_estimator = search.best_estimator_

        # Refit the selected family on train+validation, report on the
        # untouched chronological test tail.
        x_fit = pd.concat([x_train, x_validation])
        y_fit = np.concatenate([y_train, y_validation])
        final_model = best_estimator
        final_model.fit(x_fit, y_fit)

        test_prediction = final_model.predict(x_test)
        target_report["selected_model"] = best_name
        target_report["validation_rmse"] = best_rmse
        target_report["test"] = evaluation_metrics(y_test, test_prediction)
        target_report["test_residuals"] = residual_track(
            index_all[s_slice], y_test, test_prediction
        )

        fitted[short_name] = final_model
        report[short_name] = target_report

    report["split"] = split_summary
    return fitted, report


def robust_statistics(values: np.ndarray) -> dict:
    quantiles = np.quantile(values, [0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99])
    median = quantiles[3]
    mad = float(np.median(np.abs(values - median)))
    iqr = float(quantiles[4] - quantiles[2])
    deltas = np.diff(values)
    delta_median = float(np.median(deltas)) if len(deltas) else 0.0
    delta_mad = (
        float(np.median(np.abs(deltas - delta_median))) if len(deltas) else 0.0
    )
    delta_iqr = (
        float(np.quantile(deltas, 0.75) - np.quantile(deltas, 0.25))
        if len(deltas)
        else 0.0
    )
    return {
        "median": float(median),
        "mad": mad,
        "iqr": iqr,
        "q01": float(quantiles[0]),
        "q05": float(quantiles[1]),
        "q25": float(quantiles[2]),
        "q75": float(quantiles[4]),
        "q95": float(quantiles[5]),
        "q99": float(quantiles[6]),
        "delta_median": delta_median,
        "delta_mad": delta_mad,
        "delta_iqr": delta_iqr,
    }


def load_old_feature_metadata() -> dict:
    """Metadata of the 1-minute profile, carried into the 5-second one.

    The standalone reference_profile.json only exists on machines that ran
    notebook 04; the same profile also ships inside the versioned
    diagnostic bundle metadata, which is committed to the repository.
    """

    if OLD_REFERENCE_PROFILE.exists():
        with OLD_REFERENCE_PROFILE.open("r", encoding="utf-8") as file:
            return json.load(file)["feature_metadata"]
    with DIAGNOSTIC_BUNDLE_METADATA.open("r", encoding="utf-8") as file:
        bundle = json.load(file)
    return bundle["reference_profile"]["feature_metadata"]


def build_reference_profile(
    instant_features: pd.DataFrame, training_rows: int
) -> dict:
    old_metadata = load_old_feature_metadata()

    # Carry metadata over from the 1-minute profile; two engineered
    # features were renamed for clarity and two are new.
    carried = {
        name: old_metadata[name]
        for name in PROCESS_MODEL_FEATURES
        if name in old_metadata
    }
    carried["thermal_load"] = dict(
        old_metadata["steam_temp_interaction"],
        parents=["steam_pressure", "dryer_air_temperature"],
    )
    carried["thermal_exposure"] = dict(
        old_metadata["heating_index"],
        parents=["residence_time", "dryer_air_temperature"],
    )
    carried["cooler_delta"] = {
        "criticality": "medium",
        "explanation_group": "cooler_temperature",
        "kind": "engineered",
        "online_available": True,
        "parents": ["dryer_air_temperature", "cooler_air_temperature"],
        "subsystems": ["cooling_system", "thermal_system"],
        "unit": "Δ°C",
        "unit_status": "derived",
    }
    carried["steam_per_feed"] = {
        "criticality": "medium",
        "explanation_group": "thermal_energy",
        "kind": "engineered",
        "online_available": True,
        "parents": ["steam_pressure", "wet_product_feed_rate"],
        "subsystems": ["thermal_system", "feed_loading"],
        "unit": "bar/(m³/h)",
        "unit_status": "derived",
    }

    metadata = {name: carried[name] for name in PROCESS_MODEL_FEATURES}
    statistics = {
        name: robust_statistics(
            instant_features[name].to_numpy(dtype=float)
        )
        for name in PROCESS_MODEL_FEATURES
    }

    return {
        "profile_version": "reference_profile_5s_v2.0",
        "training_rows": training_rows,
        "feature_names": PROCESS_MODEL_FEATURES,
        "feature_metadata": metadata,
        "statistics": statistics,
    }


def train_anomaly_model(process: pd.DataFrame) -> tuple[dict, dict]:
    instant = engineer_instant_features(process)

    n_rows = len(instant)
    train_end = int(round(n_rows * TRAIN_FRACTION))
    train_features = instant.iloc[:train_end]
    validation_features = instant.iloc[train_end:]

    scaler = StandardScaler().fit(train_features)

    stride = max(len(train_features) // OCSVM_MAX_TRAINING_ROWS, 1)
    svm_sample = train_features.iloc[::stride]
    one_class_svm = OneClassSVM(gamma="scale", nu=ANOMALY_NU).fit(
        scaler.transform(svm_sample)
    )

    isolation_forest = IsolationForest(
        n_estimators=200,
        contamination=ANOMALY_NU,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    ).fit(scaler.transform(train_features))

    def flag_rate(model, frame: pd.DataFrame) -> float:
        return float(
            np.mean(model.predict(scaler.transform(frame)) == -1)
        )

    # Calibrate a 0–1 display risk from the raw decision function:
    # risk = 1 / (1 + exp(score / scale)). The model boundary (score = 0)
    # maps to risk 0.5, deeply normal scores approach 0, strong anomalies
    # approach 1. ``scale`` is the robust spread of training scores.
    training_scores = one_class_svm.decision_function(
        scaler.transform(svm_sample)
    )
    score_scale = float(
        max(1.4826 * np.median(np.abs(training_scores
                                      - np.median(training_scores))), 1e-6)
    )
    risk_calibration = {
        "method": "logistic_decision_function",
        "score_scale": score_scale,
        "risk_at_boundary": 0.5,
        "risk_warning_threshold": 0.5,
        "risk_critical_threshold": 0.8,
    }

    comparison = {
        "risk_calibration": risk_calibration,
        "one_class_svm": {
            "training_subsample_rows": int(len(svm_sample)),
            "flag_rate_train": flag_rate(one_class_svm, svm_sample),
            "flag_rate_validation": flag_rate(
                one_class_svm, validation_features
            ),
        },
        "isolation_forest": {
            "flag_rate_train": flag_rate(
                isolation_forest, train_features.iloc[::stride]
            ),
            "flag_rate_validation": flag_rate(
                isolation_forest, validation_features
            ),
        },
        "target_rate_nu": ANOMALY_NU,
        "selected": "one_class_svm",
        "selection_reason": (
            "Keeps the existing detector family, decision_function "
            "threshold semantics (0) and severity mapping; validation flag "
            "rate is compared against the Isolation Forest above."
        ),
    }

    artifacts = {
        "anomaly_model": one_class_svm,
        "anomaly_scaler": scaler,
        "isolation_forest_candidate": isolation_forest,
        "instant_features_train": train_features,
    }
    return artifacts, comparison


def main() -> None:
    started = datetime.now()
    print("TRAINING 5-SECOND PROTOTYPE MODELS")
    print("=" * 72)

    raw = load_raw_source(TRAINING_CSV)
    process, process_report = build_process_table(raw)
    lab = build_lab_table(raw)
    print(
        f"Process rows: {process_report.process_rows:,} | gaps: "
        f"{process_report.gap_count} | duplicates removed: "
        f"{process_report.duplicate_timestamps_removed}"
    )
    print(f"Laboratory samples: {len(lab)}")

    alignment = build_training_matrix(
        process,
        lab,
        window_minutes=DEFAULT_WINDOW_MINUTES,
        transport_delay_minutes=DEFAULT_TRANSPORT_DELAY_MINUTES,
    )
    print(
        f"Supervised rows: {len(alignment.features)} | skipped: "
        f"{[(str(t), reason) for t, reason in alignment.skipped]}"
    )

    quality_models, quality_report = train_quality_models(
        alignment.features, alignment.targets
    )

    anomaly_artifacts, anomaly_report = train_anomaly_model(process)

    reference_profile = build_reference_profile(
        anomaly_artifacts["instant_features_train"],
        training_rows=len(anomaly_artifacts["instant_features_train"]),
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        quality_models["moisture"],
        OUTPUT_DIR / "quality_moisture_pipeline.joblib",
    )
    joblib.dump(
        quality_models["density"],
        OUTPUT_DIR / "quality_density_pipeline.joblib",
    )
    joblib.dump(
        quality_models["product_temp"],
        OUTPUT_DIR / "quality_product_temp_pipeline.joblib",
    )
    joblib.dump(
        anomaly_artifacts["anomaly_model"], OUTPUT_DIR / "anomaly_model.joblib"
    )
    joblib.dump(
        anomaly_artifacts["anomaly_scaler"],
        OUTPUT_DIR / "anomaly_scaler.joblib",
    )

    with (OUTPUT_DIR / "reference_profile.json").open(
        "w", encoding="utf-8"
    ) as file:
        json.dump(reference_profile, file, indent=2, ensure_ascii=False)

    feature_schema = {
        "model_version": MODEL_VERSION,
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "created_at": started.isoformat(timespec="seconds"),
        "process_interval_seconds": 5,
        "quality_window_minutes": DEFAULT_WINDOW_MINUTES,
        "transport_delay_minutes": DEFAULT_TRANSPORT_DELAY_MINUTES,
        "residence_time_unit": "minutes",
        "window_feature_names": WINDOW_FEATURE_NAMES,
        "process_model_features": PROCESS_MODEL_FEATURES,
        "targets": TARGETS,
        "quality_selected_models": {
            name: quality_report[name]["selected_model"] for name in TARGETS
        },
        "anomaly_risk_calibration": anomaly_report["risk_calibration"],
    }
    with (OUTPUT_DIR / "feature_schema.json").open(
        "w", encoding="utf-8"
    ) as file:
        json.dump(feature_schema, file, indent=2, ensure_ascii=False)

    training_report = {
        "created_at": started.isoformat(timespec="seconds"),
        "model_version": MODEL_VERSION,
        "training_csv": str(TRAINING_CSV.relative_to(PROJECT_ROOT)),
        "process_rows": process_report.process_rows,
        "laboratory_samples": len(lab),
        "supervised_rows": len(alignment.features),
        "skipped_samples": [
            (str(t), reason) for t, reason in alignment.skipped
        ],
        "quality": quality_report,
        "anomaly": anomaly_report,
    }
    with (OUTPUT_DIR / "training_report.json").open(
        "w", encoding="utf-8"
    ) as file:
        json.dump(training_report, file, indent=2, ensure_ascii=False)

    print("\nQUALITY MODEL RESULTS")
    for name in TARGETS:
        entry = quality_report[name]
        test = entry["test"]
        print(
            f"  {name:13s} selected={entry['selected_model']:18s} "
            f"val_RMSE={entry['validation_rmse']:.5f} | test MAE="
            f"{test['mae']:.5f} RMSE={test['rmse']:.5f} R2={test['r2']:.3f} "
            f"bias={test['bias']:+.5f} maxAE={test['max_abs_error']:.5f}"
        )

    print("\nANOMALY DETECTOR")
    for name in ("one_class_svm", "isolation_forest"):
        entry = anomaly_report[name]
        print(
            f"  {name:17s} validation flag rate: "
            f"{entry['flag_rate_validation']:.4f} (target ~ {ANOMALY_NU})"
        )

    print(f"\nArtifacts written to {OUTPUT_DIR}")
    print(f"Elapsed: {(datetime.now() - started).total_seconds():.1f}s")


if __name__ == "__main__":
    main()
