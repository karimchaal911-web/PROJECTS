"""End-to-end SQL validation of the 5-second pipeline state.

Prints, from the live database:

* base-table row counts and duplicate checks (must be zero duplicates);
* process rows vs model-output rows (orphan detection);
* laboratory sample count, latest sample, current lab-result age;
* anomaly-event and contributor counts;
* inference latency statistics recorded by the service;
* the latest joined dashboard row (vw_dryer_latest sanity).

Read-only; safe to run at any time.  Exits non-zero when an invariant is
violated so it can gate the demonstration.

Run:  python realtime_pipeline/src/validate_database_state.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv

PIPELINE_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PIPELINE_ROOT / ".env")


def require_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        raise RuntimeError(f"Missing environment variable {name!r}.")
    return value.strip()


CHECKS: list[tuple[str, str]] = [
    (
        "Process rows (dryer_map)",
        'SELECT COUNT(*) FROM public.dryer_map',
    ),
    (
        "Model output rows (dryer_model_outputs)",
        'SELECT COUNT(*) FROM public.dryer_model_outputs',
    ),
    (
        "Duplicate process timestamps  [must be 0]",
        '''SELECT COUNT(*) FROM (
               SELECT "Date", "Time" FROM public.dryer_map
               GROUP BY "Date", "Time" HAVING COUNT(*) > 1
           ) AS duplicates''',
    ),
    (
        "Duplicate output timestamps  [must be 0]",
        '''SELECT COUNT(*) FROM (
               SELECT "Date", "Time" FROM public.dryer_model_outputs
               GROUP BY "Date", "Time" HAVING COUNT(*) > 1
           ) AS duplicates''',
    ),
    (
        "Process rows without model output  [should be 0]",
        '''SELECT COUNT(*)
           FROM public.dryer_map AS d
           LEFT JOIN public.dryer_model_outputs AS m
               ON d."Date" = m."Date" AND d."Time" = m."Time"
           WHERE m."Date" IS NULL''',
    ),
    (
        "Latest process timestamp",
        'SELECT MAX("Date" + "Time") FROM public.dryer_map',
    ),
    (
        "Laboratory samples (vw_dryer_lab_samples)",
        'SELECT COUNT(*) FROM public.vw_dryer_lab_samples',
    ),
    (
        "Latest laboratory timestamp",
        'SELECT MAX("Sample Timestamp") FROM public.vw_dryer_lab_samples',
    ),
    (
        "Lab result age at latest process row (min)",
        'SELECT ROUND("Lab Result Age Min"::numeric, 1) '
        'FROM public.vw_dryer_latest',
    ),
    (
        "Validated lab samples with prediction",
        'SELECT COUNT(*) FROM public.vw_dryer_lab_samples '
        'WHERE "Validated Absolute Error" IS NOT NULL',
    ),
    (
        "Mean validated absolute error (%)",
        'SELECT ROUND(AVG("Validated Absolute Error")::numeric, 4) '
        'FROM public.vw_dryer_lab_samples',
    ),
    (
        "Anomalous 5-second rows",
        'SELECT COUNT(*) FROM public.dryer_model_outputs '
        'WHERE "Anomaly Detected" IS TRUE',
    ),
    (
        "Anomaly events (vw_dryer_anomaly_events)",
        'SELECT COUNT(*) FROM public.vw_dryer_anomaly_events',
    ),
    (
        "Contributor rows (vw_dryer_contributors_powerbi)",
        'SELECT COUNT(*) FROM public.vw_dryer_contributors_powerbi',
    ),
    (
        "Avg inference latency (ms)",
        'SELECT ROUND(AVG("Inference Latency Ms")::numeric, 1) '
        'FROM public.dryer_model_outputs',
    ),
    (
        "Max inference latency (ms)",
        'SELECT ROUND(MAX("Inference Latency Ms")::numeric, 1) '
        'FROM public.dryer_model_outputs',
    ),
    (
        "Cycles over the 5 s budget  [should be 0]",
        'SELECT COUNT(*) FROM public.dryer_model_outputs '
        'WHERE "Inference Latency Ms" > 5000',
    ),
    (
        "Future lab attached to earlier row  [must be 0]",
        'SELECT COUNT(*) FROM public.vw_dryer_dashboard_powerbi '
        'WHERE "Latest Lab Sample Timestamp" > "Timestamp"',
    ),
    (
        "Lab rows in dashboard view vs lab view diff  [must be 0]",
        '''SELECT
               (SELECT COUNT(*) FROM public.vw_dryer_dashboard_powerbi
                WHERE "Is Lab Sample")
               - (SELECT COUNT(*) FROM public.vw_dryer_lab_samples)''',
    ),
    (
        "Last ingest (wall clock)",
        'SELECT MAX("Inference Timestamp") FROM public.dryer_model_outputs',
    ),
    (
        "Model version in latest row",
        'SELECT "Model Version" FROM public.vw_dryer_latest',
    ),
]

MUST_BE_ZERO = {
    "Duplicate process timestamps  [must be 0]",
    "Duplicate output timestamps  [must be 0]",
    "Future lab attached to earlier row  [must be 0]",
    "Lab rows in dashboard view vs lab view diff  [must be 0]",
}


def main() -> None:
    connection_string = (
        f"host={require_env('DB_HOST')} port={require_env('DB_PORT')} "
        f"dbname={require_env('DB_NAME')} user={require_env('DB_USER')} "
        f"password={require_env('DB_PASSWORD')}"
    )
    failures = 0
    with psycopg.connect(connection_string) as connection:
        with connection.cursor() as cursor:
            print("DATABASE STATE VALIDATION")
            print("=" * 64)
            for label, query in CHECKS:
                cursor.execute(query)
                value = cursor.fetchone()[0]
                marker = ""
                if label in MUST_BE_ZERO and value != 0:
                    marker = "  << FAIL"
                    failures += 1
                print(f"{label:<46} {value}{marker}")
    print("=" * 64)
    if failures:
        print(f"{failures} invariant(s) violated.")
        sys.exit(1)
    print("All invariants hold.")


if __name__ == "__main__":
    main()
