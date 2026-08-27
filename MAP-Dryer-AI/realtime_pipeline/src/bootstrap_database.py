"""Create the MAP_DRYER database and its complete schema from scratch.

Runs, in order:

1. ``CREATE DATABASE`` (only when the database does not exist yet);
2. ``POWERBI DASHBOARD/sql/bootstrap_base_schema.sql`` — base tables,
   upsert functions and compatibility views (idempotent);
3. ``POWERBI DASHBOARD/sql/upgrade_5s_schema.sql`` — the 5-second
   multi-rate extension (idempotent).

Credentials come from ``realtime_pipeline/.env`` exactly like every other
pipeline script; nothing is printed or hardcoded.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv

PIPELINE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = PIPELINE_ROOT.parent
ENV_PATH = PIPELINE_ROOT / ".env"
SQL_DIR = PROJECT_ROOT / "POWERBI DASHBOARD" / "sql"
BOOTSTRAP_SQL = SQL_DIR / "bootstrap_base_schema.sql"
UPGRADE_SQL = SQL_DIR / "upgrade_5s_schema.sql"

load_dotenv(ENV_PATH)


def require_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        raise RuntimeError(
            f"Missing environment variable {name!r} in {ENV_PATH}."
        )
    return value.strip()


def connection_string(dbname: str) -> str:
    return (
        f"host={require_env('DB_HOST')} "
        f"port={require_env('DB_PORT')} "
        f"dbname={dbname} "
        f"user={require_env('DB_USER')} "
        f"password={require_env('DB_PASSWORD')}"
    )


def ensure_database_exists(target: str) -> None:
    with psycopg.connect(
        connection_string("postgres"), autocommit=True
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s", (target,)
            )
            if cursor.fetchone() is None:
                # Identifier quoting: the name comes from .env, not user
                # input, but quote it defensively anyway.
                cursor.execute(
                    psycopg.sql.SQL("CREATE DATABASE {}").format(
                        psycopg.sql.Identifier(target)
                    )
                )
                print(f"Created database {target}.")
            else:
                print(f"Database {target} already exists.")


def run_script(dbname: str, script_path: Path) -> None:
    script = script_path.read_text(encoding="utf-8")
    with psycopg.connect(connection_string(dbname)) as connection:
        with connection.cursor() as cursor:
            # One multi-statement execution: the bootstrap file contains
            # function bodies with embedded semicolons, so it must never be
            # split naively.
            cursor.execute(script)
        connection.commit()
    print(f"Applied {script_path.name}.")


def main() -> None:
    target = require_env("DB_NAME")
    ensure_database_exists(target)
    run_script(target, BOOTSTRAP_SQL)
    run_script(target, UPGRADE_SQL)
    print("\nDatabase bootstrap complete.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"BOOTSTRAP FAILED: {error!r}", file=sys.stderr)
        sys.exit(1)
