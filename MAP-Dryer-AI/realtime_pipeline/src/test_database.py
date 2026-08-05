from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE)


def require_environment_variable(name: str) -> str:
    """Return a required environment variable or stop with a clear error."""

    value = os.getenv(name)

    if value is None or not value.strip():
        raise RuntimeError(
            f"Missing required environment variable: {name}"
        )

    return value.strip()


def build_connection_string() -> str:
    """Build the PostgreSQL connection string from .env values."""

    return (
        f"host={require_environment_variable('DB_HOST')} "
        f"port={require_environment_variable('DB_PORT')} "
        f"dbname={require_environment_variable('DB_NAME')} "
        f"user={require_environment_variable('DB_USER')} "
        f"password={require_environment_variable('DB_PASSWORD')}"
    )


def main() -> None:
    connection_string = build_connection_string()

    try:
        with psycopg.connect(
            connection_string,
            connect_timeout=10,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        current_database(),
                        current_user,
                        version();
                    """
                )

                database_name, user_name, version = cursor.fetchone()

                print("PostgreSQL connection: SUCCESS")
                print(f"Database: {database_name}")
                print(f"User: {user_name}")
                print(f"Server: {version.split(',')[0]}")

                cursor.execute(
                    """
                    SELECT
                        to_regclass('public.dryer_map'),
                        to_regclass('public.dryer_model_outputs'),
                        to_regclass('public.vw_dryer_dashboard_v2');
                    """
                )

                (
                    dryer_table,
                    output_table,
                    dashboard_view,
                ) = cursor.fetchone()

                print("\nDatabase objects:")
                print(f"dryer_map: {dryer_table}")
                print(f"dryer_model_outputs: {output_table}")
                print(f"vw_dryer_dashboard_v2: {dashboard_view}")

                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM public.dryer_map;
                    """
                )
                dryer_rows = cursor.fetchone()[0]

                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM public.dryer_model_outputs;
                    """
                )
                output_rows = cursor.fetchone()[0]

                print("\nCurrent row counts:")
                print(f"dryer_map: {dryer_rows:,}")
                print(f"dryer_model_outputs: {output_rows:,}")

                cursor.execute(
                    """
                    SELECT
                        MAX(("Date" + "Time")::timestamp)
                    FROM public.dryer_map;
                    """
                )

                latest_timestamp = cursor.fetchone()[0]

                print(
                    "Latest process timestamp: "
                    f"{latest_timestamp or 'NO DATA'}"
                )

    except psycopg.OperationalError as error:
        print("PostgreSQL connection: FAILED", file=sys.stderr)
        print(error, file=sys.stderr)
        sys.exit(1)

    except Exception as error:
        print(
            f"Pipeline configuration error: {error}",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()