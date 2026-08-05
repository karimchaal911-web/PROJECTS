from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import psycopg
from dotenv import load_dotenv


# ================================================================
# CONFIGURATION
# ================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE)


# Exact CSV column names.
# The CSV Air Flow Rate field has no trailing space.
EXPECTED_CSV_COLUMNS = [
    "Date",
    "Time",
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
    "Final Product Temp",
    "Final Moisture (%H2O)",
]


# ================================================================
# ENVIRONMENT HELPERS
# ================================================================

def require_environment_variable(name: str) -> str:
    """Read a mandatory value from the .env file."""

    value = os.getenv(name)

    if value is None or not value.strip():
        raise RuntimeError(
            f"Missing required environment variable: {name}"
        )

    return value.strip()


def get_source_path() -> Path:
    """Resolve the source CSV path."""

    source_path = Path(
        require_environment_variable("SOURCE_CSV")
    )

    if not source_path.is_absolute():
        source_path = PROJECT_ROOT / source_path

    return source_path.resolve()


def build_connection_string() -> str:
    """Build the PostgreSQL connection string."""

    return (
        f"host={require_environment_variable('DB_HOST')} "
        f"port={require_environment_variable('DB_PORT')} "
        f"dbname={require_environment_variable('DB_NAME')} "
        f"user={require_environment_variable('DB_USER')} "
        f"password={require_environment_variable('DB_PASSWORD')}"
    )


# ================================================================
# SOURCE DATA
# ================================================================

def convert_numeric(value: Any) -> float | None:
    """
    Convert a pandas value into a PostgreSQL-safe value.

    Missing values become None and are stored as SQL NULL.
    """

    if pd.isna(value):
        return None

    return float(value)


def load_first_source_row() -> pd.Series:
    """Load and validate the first observation from the source CSV."""

    source_path = get_source_path()

    print(f"Source CSV: {source_path}")

    if not source_path.exists():
        raise FileNotFoundError(
            f"Source CSV does not exist:\n{source_path}"
        )

    dataframe = pd.read_csv(
        source_path,
        encoding="utf-8-sig",
        keep_default_na=True,
    )

    if dataframe.empty:
        raise ValueError("The source CSV contains no observations.")

    actual_columns = list(dataframe.columns)

    if actual_columns != EXPECTED_CSV_COLUMNS:
        raise ValueError(
            "CSV schema does not match the required schema.\n\n"
            f"Expected:\n{EXPECTED_CSV_COLUMNS}\n\n"
            f"Actual:\n{actual_columns}"
        )

    return dataframe.iloc[0]


def build_function_parameters(
    source_row: pd.Series,
    event_timestamp: datetime,
) -> tuple[Any, ...]:
    """Create the 14 parameters expected by the SQL function."""

    return (
        event_timestamp.date(),
        event_timestamp.time().replace(microsecond=0),

        convert_numeric(
            source_row["Dryer Air Temperature"]
        ),
        convert_numeric(
            source_row["Cooler Air Temperature"]
        ),
        convert_numeric(
            source_row["Air Flow Rate"]
        ),
        convert_numeric(
            source_row["Wet Product Feed Rate"]
        ),
        convert_numeric(
            source_row["Product Inlet Temperature"]
        ),
        convert_numeric(
            source_row["Residence Time"]
        ),
        convert_numeric(
            source_row["Vacuum"]
        ),
        convert_numeric(
            source_row["Steam Pressure"]
        ),
        convert_numeric(
            source_row["Fan Speed"]
        ),
        convert_numeric(
            source_row["Product Density"]
        ),
        convert_numeric(
            source_row["Final Product Temp"]
        ),
        convert_numeric(
            source_row["Final Moisture (%H2O)"]
        ),
    )


# ================================================================
# SQL
# ================================================================

# Python now calls the PostgreSQL function.
# The difficult SQL column names remain hidden inside PostgreSQL.
INSERT_FUNCTION_SQL = """
SELECT public.insert_dryer_observation(
    %s, %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s, %s, %s
);
"""


# This verification query avoids directly mentioning the
# Final Moisture (%H2O) identifier in Python.
VERIFY_SQL = """
SELECT
    COUNT(*) AS row_count,
    MAX(("Date" + "Time")::timestamp)
        AS latest_timestamp
FROM public.dryer_map;
"""


LATEST_VIEW_ROW_SQL = """
SELECT *
FROM public.vw_dryer_dashboard_v2
ORDER BY
    "Date" DESC,
    "Time" DESC
LIMIT 1;
"""


# ================================================================
# DATABASE OPERATION
# ================================================================

def insert_one_observation() -> None:
    """Insert exactly one source observation through PostgreSQL."""

    source_row = load_first_source_row()

    # Use the actual current minute for the live prototype.
    event_timestamp = datetime.now().replace(
        second=0,
        microsecond=0,
    )

    parameters = build_function_parameters(
        source_row=source_row,
        event_timestamp=event_timestamp,
    )

    connection_string = build_connection_string()

    with psycopg.connect(
        connection_string,
        autocommit=False,
    ) as connection:

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    INSERT_FUNCTION_SQL,
                    parameters,
                )

                # Consume the VOID function result.
                cursor.fetchone()

                connection.commit()

                cursor.execute(VERIFY_SQL)
                verification_result = cursor.fetchone()

                if verification_result is None:
                    raise RuntimeError(
                        "Could not verify the database insertion."
                    )

                row_count, latest_timestamp = (
                    verification_result
                )

                cursor.execute(LATEST_VIEW_ROW_SQL)
                latest_view_row = cursor.fetchone()

        except Exception:
            connection.rollback()
            raise

    print("\nONE-ROW SQL INSERT: SUCCESS")
    print(f"Current process row count: {row_count}")
    print(f"Inserted timestamp: {event_timestamp}")
    print(f"Latest database timestamp: {latest_timestamp}")

    if latest_view_row is None:
        print("Latest dashboard view row: NO DATA")
    else:
        print(
            "Latest dashboard view row retrieved: YES"
        )


# ================================================================
# MAIN
# ================================================================

def main() -> None:
    insert_one_observation()


if __name__ == "__main__":
    try:
        main()

    except Exception as error:
        print(
            "\nONE-ROW SQL INSERT: FAILED",
            file=sys.stderr,
        )

        print(
            repr(error),
            file=sys.stderr,
        )

        sys.exit(1)