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

from anomaly_features import engineer_anomaly_features


PIPELINE_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PIPELINE_ROOT / ".env")


def require_env(name: str) -> str:
    value = os.getenv(name)

    if value is None or not value.strip():
        raise RuntimeError(
            f"Missing environment variable: {name}"
        )

    return value.strip()


def resolve_path(name: str) -> Path:
    path = Path(require_env(name))

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


def load_model(path: Path):
    if not path.exists():
        raise FileNotFoundError(
            f"Moisture model not found:\n{path}"
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
    "Final Product Temp",
    "Final Moisture (%H2O)"
FROM public.dryer_map
ORDER BY
    "Date" DESC,
    "Time" DESC
LIMIT 1;
"""


STORE_MOISTURE_SQL = """
SELECT public.upsert_moisture_output(
    %s, %s, %s, %s
);
"""


VERIFY_SQL = """
SELECT
    "Date",
    "Time",
    "Predicted Final Moisture",
    "Prediction Confidence"
FROM public.dryer_model_outputs
ORDER BY
    "Date" DESC,
    "Time" DESC
LIMIT 1;
"""


def main() -> None:
    moisture_pipeline = load_model(
        resolve_path("MOISTURE_MODEL")
    )

    with psycopg.connect(
        build_connection_string(),
        autocommit=False,
    ) as connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute(LATEST_PROCESS_SQL)
                row = cursor.fetchone()

                if row is None:
                    raise RuntimeError(
                        "dryer_map contains no observations."
                    )

                event_date = row[0]
                event_time = row[1]
                reference_moisture = row[13]

                raw_features = pd.DataFrame(
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

                # Reuse the exact same 16-feature engineering contract.
                model_features = engineer_anomaly_features(
                    raw_features
                )

                # The moisture pipeline already contains StandardScaler.
                predicted_moisture = float(
                    moisture_pipeline.predict(
                        model_features
                    )[0]
                )

                # No calibrated confidence model currently exists.
                prediction_confidence = None

                cursor.execute(
                    STORE_MOISTURE_SQL,
                    (
                        event_date,
                        event_time,
                        predicted_moisture,
                        prediction_confidence,
                    ),
                )
                cursor.fetchone()

                connection.commit()

                cursor.execute(VERIFY_SQL)
                saved_row = cursor.fetchone()

        except Exception:
            connection.rollback()
            raise

    print("\nMOISTURE INFERENCE TEST: SUCCESS")
    print(f"Timestamp: {event_date} {event_time}")
    print(
        f"Predicted final moisture: "
        f"{predicted_moisture:.8f}"
    )
    print(
        f"Reference final moisture: "
        f"{reference_moisture}"
    )
    print("Prediction confidence: NOT CALIBRATED")
    print(f"Saved SQL row: {saved_row}")


if __name__ == "__main__":
    try:
        main()

    except Exception as error:
        print(
            "\nMOISTURE INFERENCE TEST: FAILED",
            file=sys.stderr,
        )
        print(repr(error), file=sys.stderr)
        sys.exit(1)