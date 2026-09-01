from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE)


DASHBOARD_VIEW = "vw_dryer_dashboard_powerbi"
CONTRIBUTORS_VIEW = "vw_dryer_contributors_powerbi"
LAB_SAMPLES_VIEW = "vw_dryer_lab_samples"
EVENTS_VIEW = "vw_dryer_anomaly_events"
OVERVIEW_VIEW = "vw_dryer_overview_trends_powerbi"
LATEST_VIEW = "vw_dryer_latest"


# The exact column names the Power BI semantic model expects. Each entry maps
# to a `sourceColumn:` line in
# "POWERBI DASHBOARD/MAP Dryer AI Dashboard.SemanticModel/definition/tables".
# Note the historical trailing space in "Air Flow Rate ".
EXPECTED_COLUMNS: dict[str, list[str]] = {
    DASHBOARD_VIEW: [
        "Timestamp",
        "Predicted Final Moisture",
        "Final Moisture (%H2O)",
        "Anomaly Score",
        "Anomaly Detected",
        "Severity",
        "Likely Subsystem",
        "Probable Diagnosis",
        "Possible Causes",
        "Recommended Verification",
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
        "Anomaly Risk",
        "Model Version",
        "Feature Schema Version",
        "Inference Timestamp",
        "Inference Latency Ms",
        "Latest Lab Sample Timestamp",
        "Latest Lab Product Density",
        "Latest Lab Final Product Temp",
        "Latest Lab Final Moisture",
        "Lab Result Age Min",
        "Lab Sample Available",
        "Is Lab Sample",
        "Validated Moisture Error",
        "Validated Absolute Error",
    ],
    CONTRIBUTORS_VIEW: [
        "Timestamp",
        "contribution_rank",
        "feature_name",
        "observed_value",
        "signed_deviation",
        "deviation_percent",
        "contribution_score",
        "deviation_direction",
        "variable_severity",
    ],
    LAB_SAMPLES_VIEW: [
        "Sample Timestamp",
        "Product Density",
        "Final Product Temp",
        "Laboratory Moisture",
        "Predicted Moisture At Sample",
        "Validated Error",
        "Validated Absolute Error",
        "Previous Sample Timestamp",
    ],
    EVENTS_VIEW: [
        "Event ID",
        "Event Start",
        "Event End",
        "Duration Min",
        "Rows In Event",
        "Peak Timestamp",
        "Peak Anomaly Score",
        "Peak Anomaly Risk",
        "Severity",
        "Subsystem",
        "Diagnosis",
        "Possible Causes",
        "Recommended Verification",
        "Predicted Moisture At Peak",
    ],
    OVERVIEW_VIEW: [
        "Timestamp",
        "Predicted Final Moisture",
        "Laboratory Moisture",
        "Anomaly Risk",
        "Anomaly Detected",
        "Dryer Air Temperature",
        "Wet Product Feed Rate",
        "Steam Pressure",
        "Air Flow Rate",
        "Vacuum",
    ],
    LATEST_VIEW: [
        "Timestamp",
        "Predicted Final Moisture",
        "Anomaly Score",
        "Anomaly Detected",
        "Severity",
        "Likely Subsystem",
        "Probable Diagnosis",
        "Possible Causes",
        "Recommended Verification",
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
        "Anomaly Risk",
        "Model Version",
        "Feature Schema Version",
        "Inference Timestamp",
        "Latest Lab Sample Timestamp",
        "Latest Lab Final Moisture",
    ],
}

# Views without their own Timestamp column use these for the freshness probe.
TIMESTAMP_COLUMN: dict[str, str] = {
    DASHBOARD_VIEW: "Timestamp",
    CONTRIBUTORS_VIEW: "Timestamp",
    LAB_SAMPLES_VIEW: "Sample Timestamp",
    EVENTS_VIEW: "Peak Timestamp",
    OVERVIEW_VIEW: "Timestamp",
    LATEST_VIEW: "Timestamp",
}


def require_environment_variable(name: str) -> str:
    value = os.getenv(name)

    if value is None or not value.strip():
        raise RuntimeError(
            f"Missing required environment variable: {name}"
        )

    return value.strip()


def build_connection_string() -> str:
    return (
        f"host={require_environment_variable('DB_HOST')} "
        f"port={require_environment_variable('DB_PORT')} "
        f"dbname={require_environment_variable('DB_NAME')} "
        f"user={require_environment_variable('DB_USER')} "
        f"password={require_environment_variable('DB_PASSWORD')}"
    )


def fetch_view_columns(
    cursor: psycopg.Cursor,
    view_name: str,
) -> list[tuple[str, str]]:
    cursor.execute(
        """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = %s
        ORDER BY ordinal_position;
        """,
        (view_name,),
    )
    return [(row[0], row[1]) for row in cursor.fetchall()]


def report_view(cursor: psycopg.Cursor, view_name: str) -> bool:
    print(f"\n{'=' * 72}\nVIEW public.{view_name}\n{'=' * 72}")

    cursor.execute(
        "SELECT to_regclass(%s);",
        (f"public.{view_name}",),
    )
    exists = cursor.fetchone()[0] is not None

    if not exists:
        print(
            "MISSING - the view does not exist. Create the full schema "
            "with\npython realtime_pipeline/src/bootstrap_database.py"
        )
        return False

    actual = fetch_view_columns(cursor, view_name)
    actual_names = [name for name, _ in actual]
    expected_names = EXPECTED_COLUMNS[view_name]

    print(f"{'COLUMN':<32} {'TYPE':<26} STATUS")
    for name, data_type in actual:
        status = "MATCH" if name in expected_names else "EXTRA (unused)"
        print(f"{name!r:<32} {data_type:<26} {status}")

    missing = [name for name in expected_names if name not in actual_names]
    all_match = not missing

    if missing:
        print("\nMISSING columns expected by the semantic model:")
        for name in missing:
            print(f"  {name!r}")
        print(
            "\nFix: either extend the view, or edit the matching "
            "'sourceColumn:' line in the .SemanticModel table TMDL files "
            "to the actual physical name."
        )

    timestamp_column = TIMESTAMP_COLUMN[view_name]
    cursor.execute(
        f'SELECT COUNT(*), MAX("{timestamp_column}") '
        f'FROM public."{view_name}";'
        if timestamp_column in actual_names
        else f'SELECT COUNT(*), NULL FROM public."{view_name}";'
    )
    row_count, latest = cursor.fetchone()
    print(f"\nRows: {row_count:,}")
    print(f"Latest timestamp: {latest or 'NO DATA'}")

    # Contributor and event views are legitimately empty while the process
    # stays normal; only the dashboard/lab views must contain data.
    may_be_empty = view_name in (CONTRIBUTORS_VIEW, EVENTS_VIEW)
    if row_count == 0:
        print(
            "NOTE - the view returns no rows."
            + (
                " That is expected when no anomaly has occurred."
                if may_be_empty
                else " Start realtime_pipeline/src/realtime_service.py "
                "to populate it."
            )
        )

    return all_match and (row_count > 0 or may_be_empty)


def main() -> None:
    connection_string = build_connection_string()

    try:
        with psycopg.connect(
            connection_string,
            connect_timeout=10,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT current_database(), current_user;"
                )
                database_name, user_name = cursor.fetchone()
                print("PostgreSQL connection: SUCCESS")
                print(f"Database: {database_name}")
                print(f"User: {user_name}")

                results = [
                    report_view(cursor, view_name)
                    for view_name in (
                        DASHBOARD_VIEW,
                        CONTRIBUTORS_VIEW,
                        LAB_SAMPLES_VIEW,
                        EVENTS_VIEW,
                        OVERVIEW_VIEW,
                        LATEST_VIEW,
                    )
                ]

        print(f"\n{'=' * 72}")
        if all(results):
            print(
                "RESULT: all six views match the Power BI semantic model "
                "contract. The .pbip can connect as-is."
            )
        else:
            print(
                "RESULT: at least one view is missing, empty, or renamed. "
                "Resolve the findings above before opening the .pbip."
            )
            sys.exit(2)

    except psycopg.OperationalError as error:
        print("PostgreSQL connection: FAILED", file=sys.stderr)
        print(error, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
