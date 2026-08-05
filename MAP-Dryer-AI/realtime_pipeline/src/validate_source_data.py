from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv


# ================================================================
# PROJECT CONFIGURATION
# ================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE)

EXPECTED_COLUMNS = [
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

NUMERIC_COLUMNS = EXPECTED_COLUMNS[2:]

EXPECTED_ROW_COUNT = 10_080
EXPECTED_FREQUENCY = pd.Timedelta(minutes=1)


# ================================================================
# SOURCE FILE
# ================================================================

def get_source_path() -> Path:
    """Resolve the CSV path configured in the .env file."""

    source_value = os.getenv("SOURCE_CSV")

    if source_value is None or not source_value.strip():
        raise RuntimeError(
            "SOURCE_CSV is missing from the .env file."
        )

    source_path = Path(source_value.strip())

    if not source_path.is_absolute():
        source_path = PROJECT_ROOT / source_path

    return source_path.resolve()


def load_source_data(source_path: Path) -> pd.DataFrame:
    """Load the replay CSV without modifying its column names."""

    if not source_path.exists():
        raise FileNotFoundError(
            f"Replay CSV does not exist:\n{source_path}"
        )

    return pd.read_csv(
        source_path,
        encoding="utf-8-sig",
        keep_default_na=True,
    )


# ================================================================
# SCHEMA VALIDATION
# ================================================================

def validate_schema(dataframe: pd.DataFrame) -> None:
    """Validate the exact names and order of all 14 columns."""

    actual_columns = list(dataframe.columns)

    print(f"Rows loaded: {len(dataframe):,}")
    print(f"Columns loaded: {len(actual_columns)}")

    if actual_columns == EXPECTED_COLUMNS:
        print("Column schema: PASS")
        return

    print("\nExpected columns:")

    for index, column in enumerate(EXPECTED_COLUMNS, start=1):
        print(f"{index:02d}. {column!r}")

    print("\nActual columns:")

    for index, column in enumerate(actual_columns, start=1):
        print(f"{index:02d}. {column!r}")

    missing_columns = [
        column
        for column in EXPECTED_COLUMNS
        if column not in actual_columns
    ]

    unexpected_columns = [
        column
        for column in actual_columns
        if column not in EXPECTED_COLUMNS
    ]

    if missing_columns:
        print("\nMissing columns:")

        for column in missing_columns:
            print(f"- {column!r}")

    if unexpected_columns:
        print("\nUnexpected columns:")

        for column in unexpected_columns:
            print(f"- {column!r}")

    raise ValueError(
        "CSV columns do not exactly match the expected schema."
    )


# ================================================================
# DATE AND TIME PARSING
# ================================================================

def parse_event_timestamps(
    dataframe: pd.DataFrame,
) -> pd.Series:
    """
    Parse the dataset Date and Time columns.

    Date format:
    - 27/07/2026 = day/month/year

    Supported time formats:
    - 17:30:00
    - 5:30:00 PM
    - 17:30
    - 5:30 PM
    """

    raw_date = (
        dataframe["Date"]
        .astype(str)
        .str.strip()
    )

    raw_time = (
        dataframe["Time"]
        .astype(str)
        .str.strip()
    )

    # Your CSV explicitly uses DD/MM/YYYY.
    parsed_date = pd.to_datetime(
        raw_date,
        format="%d/%m/%Y",
        errors="coerce",
    )

    invalid_dates = int(parsed_date.isna().sum())

    if invalid_dates > 0:
        invalid_examples = (
            raw_date.loc[parsed_date.isna()]
            .drop_duplicates()
            .head(10)
            .tolist()
        )

        raise ValueError(
            f"Invalid Date values found: {invalid_dates:,}\n"
            f"Examples: {invalid_examples}"
        )

    # Try the possible time formats one by one.
    time_formats = [
        "%H:%M:%S",     # 17:30:00
        "%I:%M:%S %p",  # 5:30:00 PM
        "%H:%M",        # 17:30
        "%I:%M %p",     # 5:30 PM
    ]

    parsed_time = None
    selected_time_format = None

    for time_format in time_formats:
        candidate = pd.to_datetime(
            raw_time,
            format=time_format,
            errors="coerce",
        )

        if candidate.notna().all():
            parsed_time = candidate
            selected_time_format = time_format
            break

    if parsed_time is None:
        invalid_examples = (
            raw_time
            .drop_duplicates()
            .head(10)
            .tolist()
        )

        raise ValueError(
            "Could not determine the Time format.\n"
            f"Examples: {invalid_examples}"
        )

    time_delta = (
        pd.to_timedelta(
            parsed_time.dt.hour,
            unit="h",
        )
        + pd.to_timedelta(
            parsed_time.dt.minute,
            unit="m",
        )
        + pd.to_timedelta(
            parsed_time.dt.second,
            unit="s",
        )
    )

    event_timestamp = (
        parsed_date.dt.normalize()
        + time_delta
    )

    print("Detected Date format: %d/%m/%Y")
    print(
        f"Detected Time format: {selected_time_format}"
    )
    print("Date and time parsing: PASS")

    return event_timestamp


# ================================================================
# TIMESTAMP VALIDATION
# ================================================================

def validate_timestamps(
    event_timestamp: pd.Series,
) -> pd.Series:
    """Validate uniqueness and exact one-minute frequency."""

    duplicate_count = int(
        event_timestamp.duplicated().sum()
    )

    if duplicate_count > 0:
        duplicate_examples = (
            event_timestamp[
                event_timestamp.duplicated(
                    keep=False
                )
            ]
            .sort_values()
            .head(10)
            .tolist()
        )

        raise ValueError(
            f"Duplicate timestamps found: "
            f"{duplicate_count:,}\n"
            f"Examples: {duplicate_examples}"
        )

    print("Duplicate timestamps: 0")

    ordered_timestamps = (
        event_timestamp
        .sort_values()
        .reset_index(drop=True)
    )

    timestamp_differences = (
        ordered_timestamps
        .diff()
        .dropna()
    )

    unexpected_gaps = timestamp_differences[
        timestamp_differences
        != EXPECTED_FREQUENCY
    ]

    if not unexpected_gaps.empty:
        print("\nUnexpected timestamp intervals:")

        for gap, count in (
            unexpected_gaps
            .value_counts()
            .head(10)
            .items()
        ):
            print(
                f"- {gap}: {count:,} occurrence(s)"
            )

        raise ValueError(
            f"Found {len(unexpected_gaps):,} intervals "
            "that are not exactly one minute."
        )

    print("One-minute cadence: PASS")

    return ordered_timestamps


# ================================================================
# NUMERIC VALIDATION
# ================================================================

def validate_numeric_columns(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Convert process columns to numeric and reject invalid text."""

    validated_dataframe = dataframe.copy()

    invalid_numeric_values: dict[
        str,
        tuple[int, list[str]],
    ] = {}

    for column in NUMERIC_COLUMNS:
        original_values = validated_dataframe[column]

        converted_values = pd.to_numeric(
            original_values,
            errors="coerce",
        )

        invalid_mask = (
            original_values.notna()
            & converted_values.isna()
        )

        invalid_count = int(
            invalid_mask.sum()
        )

        if invalid_count > 0:
            examples = (
                original_values.loc[invalid_mask]
                .astype(str)
                .head(5)
                .tolist()
            )

            invalid_numeric_values[column] = (
                invalid_count,
                examples,
            )

        validated_dataframe[column] = (
            converted_values
        )

    if invalid_numeric_values:
        print("\nInvalid numeric values:")

        for (
            column,
            (count, examples),
        ) in invalid_numeric_values.items():
            print(
                f"- {column}: {count:,}"
                f" | Examples: {examples}"
            )

        raise ValueError(
            "One or more numeric columns "
            "contain invalid text."
        )

    print("Numeric conversion: PASS")

    return validated_dataframe


# ================================================================
# MISSING VALUES
# ================================================================

def print_missing_value_report(
    dataframe: pd.DataFrame,
) -> None:
    """Display missing values without automatically rejecting them."""

    missing_counts = (
        dataframe[EXPECTED_COLUMNS]
        .isna()
        .sum()
    )

    missing_counts = missing_counts[
        missing_counts > 0
    ]

    print("\nMissing-value report:")

    if missing_counts.empty:
        print("No missing values.")
        return

    for column, count in missing_counts.items():
        percentage = (
            count
            / len(dataframe)
            * 100
        )

        print(
            f"- {column}: "
            f"{count:,} "
            f"({percentage:.3f}%)"
        )


# ================================================================
# FINAL REPORT
# ================================================================

def print_final_report(
    dataframe: pd.DataFrame,
    ordered_timestamps: pd.Series,
) -> None:
    """Print the validated dataset summary."""

    print("\nDataset time range:")

    print(
        "First timestamp: "
        f"{ordered_timestamps.iloc[0]}"
    )

    print(
        "Last timestamp:  "
        f"{ordered_timestamps.iloc[-1]}"
    )

    if len(dataframe) != EXPECTED_ROW_COUNT:
        raise ValueError(
            "Unexpected row count.\n"
            f"Expected: {EXPECTED_ROW_COUNT:,}\n"
            f"Found: {len(dataframe):,}"
        )

    print(
        f"Expected row count: PASS "
        f"({EXPECTED_ROW_COUNT:,})"
    )

    print(
        "\nREPLAY DATASET VALIDATION: SUCCESS"
    )


# ================================================================
# MAIN
# ================================================================

def main() -> None:
    source_path = get_source_path()

    print(f"Source file: {source_path}")

    dataframe = load_source_data(
        source_path
    )

    validate_schema(
        dataframe
    )

    event_timestamp = parse_event_timestamps(
        dataframe
    )

    ordered_timestamps = validate_timestamps(
        event_timestamp
    )

    dataframe = validate_numeric_columns(
        dataframe
    )

    dataframe["Event Timestamp"] = (
        event_timestamp
    )

    print_missing_value_report(
        dataframe
    )

    print_final_report(
        dataframe=dataframe,
        ordered_timestamps=ordered_timestamps,
    )


if __name__ == "__main__":
    try:
        main()

    except Exception as error:
        print(
            "\nREPLAY DATASET VALIDATION: FAILED",
            file=sys.stderr,
        )

        print(
            error,
            file=sys.stderr,
        )

        sys.exit(1)