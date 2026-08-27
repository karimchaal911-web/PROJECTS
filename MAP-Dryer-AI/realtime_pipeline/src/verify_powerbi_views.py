"""Verify live PostgreSQL views against the checked-in Power BI TMDL.

Physical `sourceColumn` names are read directly from the five active semantic
model tables. This avoids confusing Power BI display names or calculated
columns with SQL view columns.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv


PIPELINE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = PIPELINE_ROOT.parent
ENV_FILE = PIPELINE_ROOT / ".env"
TMDL_DIR = (
    PROJECT_ROOT
    / "POWERBI DASHBOARD"
    / "MAP Dryer AI Dashboard.SemanticModel"
    / "definition"
    / "tables"
)
load_dotenv(ENV_FILE)

VIEW_CONTRACTS = {
    "vw_dryer_dashboard_powerbi": {
        "tmdl": "vw_dryer_dashboard_powerbi.tmdl",
        "timestamp": "Timestamp",
        "must_have_rows": True,
    },
    "vw_dryer_contributors_powerbi": {
        "tmdl": "vw_dryer_contributors_powerbi.tmdl",
        "timestamp": "Timestamp",
        "must_have_rows": False,
    },
    "vw_dryer_lab_samples": {
        "tmdl": "vw_dryer_lab_samples.tmdl",
        "timestamp": "Sample Timestamp",
        "must_have_rows": True,
    },
    "vw_dryer_anomaly_events": {
        "tmdl": "vw_dryer_anomaly_events.tmdl",
        "timestamp": "Event Start",
        "must_have_rows": False,
    },
    "vw_dryer_overview_trends_powerbi": {
        "tmdl": "vw_dryer_overview_trends_powerbi.tmdl",
        "timestamp": "Timestamp",
        "must_have_rows": True,
    },
}
SOURCE_COLUMN_PATTERN = re.compile(r"^\s*sourceColumn:\s*(.+?)\s*$")


def require_environment_variable(name: str) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value.strip()


def build_connection_string() -> str:
    return (
        f"host={require_environment_variable('DB_HOST')} "
        f"port={require_environment_variable('DB_PORT')} "
        f"dbname={require_environment_variable('DB_NAME')} "
        f"user={require_environment_variable('DB_USER')} "
        f"password={require_environment_variable('DB_PASSWORD')}"
    )


def expected_source_columns(tmdl_name: str) -> list[str]:
    path = TMDL_DIR / tmdl_name
    columns: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = SOURCE_COLUMN_PATTERN.match(line)
        if not match:
            continue
        value = match.group(1)
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        columns.append(value)
    if not columns:
        raise RuntimeError(f"No sourceColumn entries found in {path}")
    return columns


def fetch_view_columns(
    cursor: psycopg.Cursor, view_name: str
) -> list[tuple[str, str]]:
    cursor.execute(
        """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s
        ORDER BY ordinal_position;
        """,
        (view_name,),
    )
    return [(row[0], row[1]) for row in cursor.fetchall()]


def report_view(
    cursor: psycopg.Cursor,
    view_name: str,
    contract: dict[str, object],
) -> bool:
    print(f"\n{'=' * 72}\nVIEW public.{view_name}\n{'=' * 72}")
    cursor.execute("SELECT to_regclass(%s);", (f"public.{view_name}",))
    if cursor.fetchone()[0] is None:
        print("MISSING - apply POWERBI DASHBOARD/sql/upgrade_5s_schema.sql")
        return False

    actual = fetch_view_columns(cursor, view_name)
    actual_names = [name for name, _ in actual]
    expected_names = expected_source_columns(str(contract["tmdl"]))
    missing = [name for name in expected_names if name not in actual_names]
    print(f"TMDL physical columns: {len(expected_names)}")
    print(f"SQL view columns:      {len(actual_names)}")
    if missing:
        print("MISSING physical sourceColumn values:")
        for name in missing:
            print(f"  {name!r}")
    else:
        print("Column contract: PASS")

    timestamp_column = str(contract["timestamp"])
    cursor.execute(
        f'SELECT COUNT(*), MAX("{timestamp_column}") '
        f'FROM public."{view_name}";'
    )
    row_count, latest = cursor.fetchone()
    print(f"Rows: {row_count:,}")
    print(f"Latest timestamp: {latest or 'NO DATA'}")
    row_requirement = (not bool(contract["must_have_rows"])) or row_count > 0
    if not row_requirement:
        print("Row requirement: FAIL (this semantic table must be populated)")
    elif row_count == 0:
        print("Row requirement: PASS (empty event/evidence table is allowed)")
    else:
        print("Row requirement: PASS")
    return not missing and row_requirement


def main() -> None:
    with psycopg.connect(build_connection_string(), connect_timeout=10) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database(), current_user;")
            database_name, user_name = cursor.fetchone()
            print("PostgreSQL connection: SUCCESS")
            print(f"Database: {database_name}")
            print(f"User: {user_name}")
            outcomes = {
                view_name: report_view(cursor, view_name, contract)
                for view_name, contract in VIEW_CONTRACTS.items()
            }

    print(f"\n{'=' * 72}")
    if all(outcomes.values()):
        print(
            "RESULT: all five PostgreSQL views match the checked-in Power BI "
            "physical source-column contract."
        )
        return
    print("RESULT: Power BI backend contract FAILED.")
    sys.exit(2)


if __name__ == "__main__":
    try:
        main()
    except psycopg.OperationalError as error:
        print("PostgreSQL connection: FAILED", file=sys.stderr)
        print(error, file=sys.stderr)
        sys.exit(1)
