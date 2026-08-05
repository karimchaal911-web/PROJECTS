from __future__ import annotations

import os
import sys
import warnings
from pathlib import Path

import joblib
import pandas as pd
import psycopg
from dotenv import load_dotenv
from sklearn.exceptions import InconsistentVersionWarning

from anomaly_features import (
    MODEL_FEATURES,
    engineer_anomaly_features,
)


PIPELINE_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(PIPELINE_ROOT / ".env")


def require_env(name: str) -> str:
    value = os.getenv(name)

    if value is None or not value.strip():
        raise RuntimeError(
            f"Missing environment variable: {name}"
        )

    return value.strip()


def resolve_path(environment_name: str) -> Path:
    path = Path(
        require_env(environment_name)
    )

    if not path.is_absolute():
        path = PIPELINE_ROOT / path

    return path.resolve()


def build_connection_string() -> str:
    return (
        f"host={require_env('DB_HOST')} "
        f"port={require_env('DB_PORT')} "
        f"dbname={require_env('DB_NAME')} "
        f"user={require_env('DB_USER')} "
        f"password={require_env('DB_PASSWORD')}"
    )


def load_artifact(path: Path):
    if not path.exists():
        raise FileNotFoundError(
            f"Artifact not found:\n{path}"
        )

    with warnings.catch_warnings():
        warnings.simplefilter(
            "error",
            InconsistentVersionWarning,
        )

        return joblib.load(path)


LATEST_PROCESS_SQL = """
SELECT
    "Date",
    "Time",
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


STORE_ANOMALY_SQL = """
SELECT public.upsert_anomaly_output(
    %s, %s, %s, %s, %s
);
"""


VERIFY_SQL = """
SELECT
    "Date",
    "Time",
    "Anomaly Score",
    "Anomaly Detected",
    "Severity"
FROM public.dryer_model_outputs
ORDER BY
    "Date" DESC,
    "Time" DESC
LIMIT 1;
"""


def main() -> None:
    model = load_artifact(
        resolve_path("ANOMALY_MODEL")
    )

    scaler = load_artifact(
        resolve_path("ANOMALY_SCALER")
    )

    connection_string = (
        build_connection_string()
    )

    with psycopg.connect(
        connection_string,
        autocommit=False,
    ) as connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    LATEST_PROCESS_SQL
                )

                row = cursor.fetchone()

                if row is None:
                    raise RuntimeError(
                        "dryer_map contains no rows."
                    )

                event_date = row[0]
                event_time = row[1]

                raw_data = pd.DataFrame(
                    [
                        {
                            "dryer_air_temperature": row[2],
                            "cooler_air_temperature": row[3],
                            "air_flow_rate": row[4],
                            "wet_product_feed_rate": row[5],
                            "product_inlet_temperature": row[6],
                            "residence_time": row[7],
                            "vacuum": row[8],
                            "steam_pressure": row[9],
                            "fan_speed": row[10],
                            "product_density": row[11],
                            "final_product_temp": row[12],
                        }
                    ]
                )

                features = (
                    engineer_anomaly_features(
                        raw_data
                    )
                )

                scaled_values = scaler.transform(
                    features
                )

                scaled_features = pd.DataFrame(
                    scaled_values,
                    columns=MODEL_FEATURES,
                    index=features.index,
                )

                prediction = int(
                    model.predict(
                        scaled_features
                    )[0]
                )

                raw_score = float(
                    model.decision_function(
                        scaled_features
                    )[0]
                )

                anomaly_detected = (
                    prediction == -1
                )

                severity = (
                    "UNCLASSIFIED"
                    if anomaly_detected
                    else "NORMAL"
                )

                cursor.execute(
                    STORE_ANOMALY_SQL,
                    (
                        event_date,
                        event_time,
                        raw_score,
                        anomaly_detected,
                        severity,
                    ),
                )

                cursor.fetchone()

                connection.commit()

                cursor.execute(VERIFY_SQL)
                saved_output = cursor.fetchone()

        except Exception:
            connection.rollback()
            raise

    print(
        "ANOMALY OUTPUT PERSISTENCE: SUCCESS"
    )
    print(
        f"Timestamp: {event_date} {event_time}"
    )
    print(
        f"Prediction: {prediction}"
    )
    print(
        f"Anomaly detected: {anomaly_detected}"
    )
    print(
        f"Raw score: {raw_score:.8f}"
    )
    print(
        f"Severity: {severity}"
    )
    print(
        f"Saved SQL row: {saved_output}"
    )


if __name__ == "__main__":
    try:
        main()

    except Exception as error:
        print(
            "\nANOMALY OUTPUT PERSISTENCE: FAILED",
            file=sys.stderr,
        )

        print(
            repr(error),
            file=sys.stderr,
        )

        sys.exit(1)