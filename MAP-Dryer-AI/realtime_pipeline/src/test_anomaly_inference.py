from __future__ import annotations

import os
import sys
import warnings
from pathlib import Path

import joblib
import pandas as pd
import psycopg
import sklearn
from dotenv import load_dotenv
from sklearn.exceptions import InconsistentVersionWarning

from anomaly_features import (
    MODEL_FEATURES,
    engineer_anomaly_features,
)


# ================================================================
# CONFIGURATION
# ================================================================

PIPELINE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = PIPELINE_ROOT.parent

load_dotenv(PIPELINE_ROOT / ".env")


def require_environment_variable(name: str) -> str:
    value = os.getenv(name)

    if value is None or not value.strip():
        raise RuntimeError(
            f"Missing environment variable: {name}"
        )

    return value.strip()


def resolve_project_path(
    environment_name: str,
) -> Path:
    configured_path = Path(
        require_environment_variable(
            environment_name
        )
    )

    if not configured_path.is_absolute():
        configured_path = (
            PIPELINE_ROOT / configured_path
        )

    return configured_path.resolve()


def build_connection_string() -> str:
    return (
        f"host={require_environment_variable('DB_HOST')} "
        f"port={require_environment_variable('DB_PORT')} "
        f"dbname={require_environment_variable('DB_NAME')} "
        f"user={require_environment_variable('DB_USER')} "
        f"password={require_environment_variable('DB_PASSWORD')}"
    )


# ================================================================
# ARTIFACT VALIDATION
# ================================================================

def load_artifact(path: Path):
    if not path.exists():
        raise FileNotFoundError(
            f"Model artifact was not found:\n{path}"
        )

    with warnings.catch_warnings():
        warnings.simplefilter(
            "error",
            InconsistentVersionWarning,
        )

        return joblib.load(path)


def validate_feature_contract(
    anomaly_model,
    anomaly_scaler,
) -> None:
    expected_features = list(MODEL_FEATURES)

    scaler_feature_count = getattr(
        anomaly_scaler,
        "n_features_in_",
        None,
    )

    model_feature_count = getattr(
        anomaly_model,
        "n_features_in_",
        None,
    )

    if scaler_feature_count != len(expected_features):
        raise ValueError(
            "Scaler feature-count mismatch.\n"
            f"Expected: {len(expected_features)}\n"
            f"Scaler: {scaler_feature_count}"
        )

    if model_feature_count != len(expected_features):
        raise ValueError(
            "Model feature-count mismatch.\n"
            f"Expected: {len(expected_features)}\n"
            f"Model: {model_feature_count}"
        )

    scaler_features = getattr(
        anomaly_scaler,
        "feature_names_in_",
        None,
    )

    if scaler_features is not None:
        if list(scaler_features) != expected_features:
            raise ValueError(
                "Scaler feature order does not match "
                "MODEL_FEATURES."
            )

    model_features = getattr(
        anomaly_model,
        "feature_names_in_",
        None,
    )

    if model_features is not None:
        if list(model_features) != expected_features:
            raise ValueError(
                "Model feature order does not match "
                "MODEL_FEATURES."
            )


# ================================================================
# SQL INPUT
# ================================================================

LATEST_PROCESS_ROW_SQL = """
SELECT
    ("Date" + "Time")::timestamp
        AS event_timestamp,

    "Dryer Air Temperature",
    "Cooler Air Temperature",
    "Air Flow Rate ",
    "Wet Product Feed Rate",
    "Product Inlet Temperature",
    "Residence Time",
    "Vacuum",
    "Steam Pressure",
    "Fan Speed",
    "Product Density",
    "Final Product Temp"

FROM public.dryer_map

ORDER BY
    "Date" DESC,
    "Time" DESC

LIMIT 1;
"""


def load_latest_process_observation() -> tuple[
    object,
    pd.DataFrame,
]:
    with psycopg.connect(
        build_connection_string()
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                LATEST_PROCESS_ROW_SQL
            )

            row = cursor.fetchone()

    if row is None:
        raise RuntimeError(
            "dryer_map contains no process observations."
        )

    event_timestamp = row[0]

    raw_data = pd.DataFrame(
        [
            {
                "dryer_air_temperature": row[1],
                "cooler_air_temperature": row[2],
                "air_flow_rate": row[3],
                "wet_product_feed_rate": row[4],
                "product_inlet_temperature": row[5],
                "residence_time": row[6],
                "vacuum": row[7],
                "steam_pressure": row[8],
                "fan_speed": row[9],
                "product_density": row[10],
                "final_product_temp": row[11],
            }
        ]
    )

    return event_timestamp, raw_data


# ================================================================
# INFERENCE
# ================================================================

def run_test() -> None:
    model_path = resolve_project_path(
        "ANOMALY_MODEL"
    )

    scaler_path = resolve_project_path(
        "ANOMALY_SCALER"
    )

    print(
        "Current Scikit-learn version:",
        sklearn.__version__,
    )
    print("Anomaly model:", model_path)
    print("Anomaly scaler:", scaler_path)

    anomaly_model = load_artifact(
        model_path
    )

    anomaly_scaler = load_artifact(
        scaler_path
    )

    validate_feature_contract(
        anomaly_model=anomaly_model,
        anomaly_scaler=anomaly_scaler,
    )

    event_timestamp, raw_data = (
        load_latest_process_observation()
    )

    model_features = engineer_anomaly_features(
        raw_data
    )

    scaled_values = anomaly_scaler.transform(
        model_features
    )

    # The One-Class SVM was fitted with named columns.
    scaled_features = pd.DataFrame(
        scaled_values,
        columns=MODEL_FEATURES,
        index=model_features.index,
    )

    prediction = int(
        anomaly_model.predict(
            scaled_features
        )[0]
    )

    decision_score = float(
        anomaly_model.decision_function(
            scaled_features
        )[0]
    )

    anomaly_detected = prediction == -1

    print("\nANOMALY INFERENCE TEST: SUCCESS")
    print(f"Event timestamp: {event_timestamp}")
    print(f"Feature count: {model_features.shape[1]}")
    print(f"One-Class SVM prediction: {prediction}")
    print(f"Anomaly detected: {anomaly_detected}")
    print(
        "Raw decision-function score: "
        f"{decision_score:.8f}"
    )

    print("\nEngineered features:")

    for column in MODEL_FEATURES[11:]:
        value = model_features.iloc[0][column]
        print(f"- {column}: {value:.8f}")

    print(
        "\nImportant: the raw decision-function score "
        "is not a probability or calibrated confidence."
    )


if __name__ == "__main__":
    try:
        run_test()

    except Exception as error:
        print(
            "\nANOMALY INFERENCE TEST: FAILED",
            file=sys.stderr,
        )

        print(
            repr(error),
            file=sys.stderr,
        )

        sys.exit(1)