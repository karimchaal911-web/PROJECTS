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


# The exact column names the Power BI semantic model expects. Each entry maps
# to a `sourceColumn:` line in
# "POWERBI DASHBOARD/MAP Dryer AI Dashboard.SemanticModel/definition/tables".
EXPECTED_COLUMNS: dict[str, list[str]] = {
    DASHBOARD_VIEW: [
        "Timestamp",
        "Predicted Moisture",
        "Laboratory Moisture",
        "Moisture Error",
        "Absolute Moisture Error",
        "Anomaly Score",
        "Anomaly Status",
        "Severity",
        "Subsystem",
        "Diagnosis",
        "Possible Causes",
        "Recommended Verification",
        "Dryer Air Temperature",
        "Cooler Air Temperature",
        "Air Flow Rate",
        "Wet Product Feed Rate",
        "Product Inlet Temperature",
        "Residence Time",
        "Vacuum",
        "Steam Pressure",
        "Fan Speed",
        "Product Density",
        "Final Product Temperature",
    ],
    CONTRIBUTORS_VIEW: [
        "Timestamp",
        "Contributor Rank",
        "Contributor Name",
        "Observed Value",
        "Signed Deviation",
        "Deviation Percent",
        "Contribution Score",
        "Deviation Direction",
        "Variable Severity",
    ],
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
            "MISSING - the view does not exist. Create it with\n"
            "POWERBI DASHBOARD/sql/create_powerbi_views.sql"
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

    cursor.execute(
        f'SELECT COUNT(*), MAX("Timestamp") FROM public."{view_name}";'
        if "Timestamp" in actual_names
        else f'SELECT COUNT(*), NULL FROM public."{view_name}";'
    )
    row_count, latest = cursor.fetchone()
    print(f"\nRows: {row_count:,}")
    print(f"Latest timestamp: {latest or 'NO DATA'}")

    if row_count == 0:
        print(
            "WARNING - the view returns no rows. Start "
            "realtime_pipeline/src/replay_service.py to populate it."
        )

    return all_match and row_count > 0


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

                dashboard_ok = report_view(cursor, DASHBOARD_VIEW)
                contributors_ok = report_view(cursor, CONTRIBUTORS_VIEW)

        print(f"\n{'=' * 72}")
        if dashboard_ok and contributors_ok:
            print(
                "RESULT: both views match the Power BI semantic model "
                "contract and contain data. The .pbip can connect as-is."
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
