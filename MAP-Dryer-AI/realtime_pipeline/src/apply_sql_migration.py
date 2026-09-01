"""Apply the 5-second schema upgrade to the MAP_DRYER database.

Runs ``powerbi_dashboard/sql/upgrade_5s_schema.sql`` statement by statement
inside one transaction, using the same .env credential handling as the
other pipeline scripts. Idempotent — rerunning is safe.
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
MIGRATION_SQL = (
    PROJECT_ROOT / "powerbi_dashboard" / "sql" / "upgrade_5s_schema.sql"
)

load_dotenv(ENV_PATH)


def require_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        raise RuntimeError(
            f"Missing environment variable {name!r} in {ENV_PATH}."
        )
    return value.strip()


def split_statements(script: str) -> list[str]:
    """Split on top-level semicolons (the script has no function bodies).

    Line comments are removed first so a semicolon inside a comment can
    never split a statement.
    """

    without_comments = "\n".join(
        line
        for line in script.splitlines()
        if not line.lstrip().startswith("--")
    )

    statements = []
    for chunk in without_comments.split(";"):
        if chunk.strip():
            statements.append(chunk.strip())
    return statements


def main() -> None:
    script = MIGRATION_SQL.read_text(encoding="utf-8")
    statements = split_statements(script)

    connection_string = (
        f"host={require_env('DB_HOST')} "
        f"port={require_env('DB_PORT')} "
        f"dbname={require_env('DB_NAME')} "
        f"user={require_env('DB_USER')} "
        f"password={require_env('DB_PASSWORD')}"
    )

    with psycopg.connect(connection_string) as connection:
        with connection.cursor() as cursor:
            for index, statement in enumerate(statements, start=1):
                first_line = statement.splitlines()[0][:76]
                print(f"[{index:02d}/{len(statements)}] {first_line}")
                cursor.execute(statement)
        connection.commit()

    print("\nMigration applied successfully.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"MIGRATION FAILED: {error!r}", file=sys.stderr)
        sys.exit(1)
