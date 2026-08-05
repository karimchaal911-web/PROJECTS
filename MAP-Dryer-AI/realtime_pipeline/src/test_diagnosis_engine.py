from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
import psycopg
from dotenv import load_dotenv

from anomaly_features import engineer_anomaly_features
from diagnosis_engine import diagnose_event, load_reference_profile


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
    configured_path = Path(
        require_env("REFERENCE_PROFILE")
    )

    if not configured_path.is_absolute():
        configured_path = PIPELINE_ROOT / configured_path

    return configured_path.resolve()


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


def main() -> None:
    reference_profile = load_reference_profile(
        resolve_reference_profile()
    )

    with psycopg.connect(
        build_connection_string()
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(LATEST_EVENT_SQL)
            row = cursor.fetchone()

    if row is None:
        raise RuntimeError(
            "No process observation exists in public.dryer_map."
        )

    anomaly_detected = row[13]

    if anomaly_detected is None:
        raise RuntimeError(
            "The latest process row has no anomaly output."
        )

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

    model_features = engineer_anomaly_features(
        raw_features
    )

    diagnosis = diagnose_event(
        model_features=model_features,
        anomaly_detected=bool(anomaly_detected),
        reference_profile=reference_profile,
    )

    print("\nDIAGNOSIS ENGINE TEST: SUCCESS")
    print(f"Timestamp: {row[0]} {row[1]}")
    print(f"Anomaly detected: {anomaly_detected}")
    print(f"Raw anomaly score: {row[14]}")
    print(f"Operational severity: {diagnosis.severity}")
    print(f"Likely subsystem: {diagnosis.likely_subsystem}")
    print(f"Probable diagnosis: {diagnosis.probable_diagnosis}")
    print(f"Possible causes: {diagnosis.possible_causes}")
    print(
        "Recommended verification: "
        f"{diagnosis.recommended_verification}"
    )
    print("Diagnosis confidence: NOT CALIBRATED")

    print("\nTop direct abnormal variables:")

    if not diagnosis.direct_contributors:
        print("- None for the latest observation.")
        return

    for rank, contributor in enumerate(
        diagnosis.direct_contributors,
        start=1,
    ):
        deviation_percent = (
            "N/A"
            if contributor.deviation_percent is None
            else f"{contributor.deviation_percent:+.2f}%"
        )

        unit = contributor.unit or "unit not defined"

        print(
            f"{rank}. {contributor.feature_name} | "
            f"value={contributor.observed_value:.6f} {unit} | "
            f"baseline={contributor.reference_center:.6f} | "
            f"normal_range=["
            f"{contributor.lower_normal_limit:.6f}, "
            f"{contributor.upper_normal_limit:.6f}] | "
            f"direction={contributor.direction} | "
            f"severity={contributor.variable_severity} | "
            f"deviation={deviation_percent} | "
            f"score={contributor.contribution_score:.4f}"
        )


if __name__ == "__main__":
    try:
        main()

    except Exception as error:
        print(
            "\nDIAGNOSIS ENGINE TEST: FAILED",
            file=sys.stderr,
        )
        print(repr(error), file=sys.stderr)
        sys.exit(1)