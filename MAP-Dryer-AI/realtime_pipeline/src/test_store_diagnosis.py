from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
import psycopg
from dotenv import load_dotenv

from anomaly_features import engineer_anomaly_features
from diagnosis_engine import (
    diagnose_event,
    load_reference_profile,
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


def build_connection_string() -> str:
    return (
        f"host={require_env('DB_HOST')} "
        f"port={require_env('DB_PORT')} "
        f"dbname={require_env('DB_NAME')} "
        f"user={require_env('DB_USER')} "
        f"password={require_env('DB_PASSWORD')}"
    )


def resolve_reference_profile() -> Path:
    path = Path(
        require_env("REFERENCE_PROFILE")
    )

    if not path.is_absolute():
        path = PIPELINE_ROOT / path

    return path.resolve()


LATEST_EVENT_SQL = """
SELECT
    d."Date",
    d."Time",
    d."Dryer Air Temperature",
    d."Cooler Air Temperature",
    d."Air Flow Rate ",
    d."Wet Product Feed Rate",
    d."Product Inlet Temperature",
    d."Residence Time",
    d."Vacuum",
    d."Steam Pressure",
    d."Fan Speed",
    d."Product Density",
    d."Final Product Temp",
    m."Anomaly Detected",
    m."Anomaly Score"
FROM public.dryer_map AS d
LEFT JOIN public.dryer_model_outputs AS m
    ON d."Date" = m."Date"
   AND d."Time" = m."Time"
ORDER BY
    d."Date" DESC,
    d."Time" DESC
LIMIT 1;
"""


STORE_DIAGNOSIS_SQL = """
SELECT public.upsert_diagnosis_output(
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s
);
"""


DELETE_CONTRIBUTORS_SQL = """
DELETE FROM public.dryer_abnormal_variables
WHERE event_date = %s
  AND event_time = %s;
"""


INSERT_CONTRIBUTOR_SQL = """
INSERT INTO public.dryer_abnormal_variables (
    event_date,
    event_time,
    contribution_rank,
    feature_name,
    observed_value,
    reference_center,
    reference_scale,
    lower_normal_limit,
    upper_normal_limit,
    signed_deviation,
    deviation_percent,
    contribution_score,
    deviation_direction,
    is_direct_process_feature,
    variable_severity
)
VALUES (
    %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s
);
"""


def build_model_features(
    row: tuple,
) -> pd.DataFrame:
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

    return engineer_anomaly_features(
        raw_features
    )


def main() -> None:
    reference_profile = load_reference_profile(
        resolve_reference_profile()
    )

    connection_string = build_connection_string()

    with psycopg.connect(
        connection_string
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(LATEST_EVENT_SQL)
            row = cursor.fetchone()

        if row is None:
            raise RuntimeError(
                "No process observation exists in public.dryer_map."
            )

        event_date = row[0]
        event_time = row[1]
        anomaly_detected = row[13]

        if anomaly_detected is None:
            raise RuntimeError(
                "The latest process observation has no anomaly result."
            )

        model_features = build_model_features(
            row
        )

        diagnosis = diagnose_event(
            model_features=model_features,
            anomaly_detected=bool(
                anomaly_detected
            ),
            reference_profile=reference_profile,
        )

        diagnosis_parameters = (
            event_date,
            event_time,
            diagnosis.severity,
            diagnosis.likely_subsystem,
            diagnosis.probable_diagnosis,
            diagnosis.possible_causes,
            diagnosis.diagnosis_confidence,
            diagnosis.recommended_verification,
        )

        with connection.transaction():
            with connection.cursor() as cursor:
                cursor.execute(
                    STORE_DIAGNOSIS_SQL,
                    diagnosis_parameters,
                )
                cursor.fetchone()

                cursor.execute(
                    DELETE_CONTRIBUTORS_SQL,
                    (
                        event_date,
                        event_time,
                    ),
                )

                for rank, contributor in enumerate(
                    diagnosis.direct_contributors,
                    start=1,
                ):
                    contributor_parameters = (
                        event_date,
                        event_time,
                        rank,
                        contributor.feature_name,
                        contributor.observed_value,
                        contributor.reference_center,
                        contributor.reference_scale,
                        contributor.lower_normal_limit,
                        contributor.upper_normal_limit,
                        contributor.signed_deviation,
                        contributor.deviation_percent,
                        contributor.contribution_score,
                        contributor.direction,
                        contributor.is_direct_process_feature,
                        contributor.variable_severity,
                    )

                    cursor.execute(
                        INSERT_CONTRIBUTOR_SQL,
                        contributor_parameters,
                    )

    print("\nDIAGNOSIS STORAGE TEST: SUCCESS")
    print(f"Timestamp: {event_date} {event_time}")
    print(f"Severity: {diagnosis.severity}")
    print(
        f"Likely subsystem: "
        f"{diagnosis.likely_subsystem}"
    )
    print(
        f"Probable diagnosis: "
        f"{diagnosis.probable_diagnosis}"
    )
    print(
        "Stored abnormal variables: "
        f"{len(diagnosis.direct_contributors)}"
    )
    print(
        "Diagnosis confidence: "
        "NOT CALIBRATED"
    )


if __name__ == "__main__":
    try:
        main()

    except Exception as error:
        print(
            "\nDIAGNOSIS STORAGE TEST: FAILED",
            file=sys.stderr,
        )
        print(
            repr(error),
            file=sys.stderr,
        )
        sys.exit(1)