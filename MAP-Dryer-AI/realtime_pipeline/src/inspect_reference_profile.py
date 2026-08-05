from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


PIPELINE_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PIPELINE_ROOT / ".env")


def resolve_reference_profile_path() -> Path:
    configured_path = os.getenv(
        "REFERENCE_PROFILE",
        "../models/anomaly_pipeline/reference_profile.json",
    )

    profile_path = Path(configured_path)

    if not profile_path.is_absolute():
        profile_path = (
            PIPELINE_ROOT
            / profile_path
        )

    return profile_path.resolve()


def describe_value(
    name: str,
    value: Any,
    indent: int = 0,
) -> None:
    prefix = " " * indent

    if isinstance(value, dict):
        print(
            f"{prefix}{name}: "
            f"dictionary ({len(value)} keys)"
        )

        for child_name, child_value in value.items():
            describe_value(
                str(child_name),
                child_value,
                indent + 2,
            )

    elif isinstance(value, list):
        print(
            f"{prefix}{name}: "
            f"list ({len(value)} items)"
        )

        for index, item in enumerate(value[:5]):
            describe_value(
                f"[{index}]",
                item,
                indent + 2,
            )

        if len(value) > 5:
            print(
                f"{prefix}  ... "
                f"{len(value) - 5} additional items"
            )

    else:
        print(
            f"{prefix}{name}: "
            f"{value!r} "
            f"({type(value).__name__})"
        )


def main() -> None:
    profile_path = resolve_reference_profile_path()

    print("REFERENCE PROFILE INSPECTION")
    print("=" * 72)
    print(f"Path: {profile_path}")

    if not profile_path.exists():
        raise FileNotFoundError(
            f"Reference profile was not found:\n{profile_path}"
        )

    with profile_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        reference_profile = json.load(file)

    print("\nTop-level structure:")
    describe_value(
        "reference_profile",
        reference_profile,
    )

    print("\nRaw JSON preview:")
    print(
        json.dumps(
            reference_profile,
            indent=2,
            ensure_ascii=False,
        )[:12000]
    )

    print(
        "\nREFERENCE PROFILE INSPECTION: SUCCESS"
    )


if __name__ == "__main__":
    try:
        main()

    except Exception as error:
        print(
            "\nREFERENCE PROFILE INSPECTION: FAILED",
            file=sys.stderr,
        )
        print(
            repr(error),
            file=sys.stderr,
        )
        sys.exit(1)