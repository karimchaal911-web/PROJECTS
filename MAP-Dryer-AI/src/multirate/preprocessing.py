"""Split the raw 5-second CSV into explicit process and laboratory tables.

The raw prototype files keep the original plant column names. They are never
renamed here; snake_case aliases exist only inside engineered feature frames.
All timestamps are naive plant-local time (no timezone conversion happens
anywhere in the pipeline; PostgreSQL stores the same local Date/Time pair).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd


PROCESS_INTERVAL_SECONDS = 5

RAW_SOURCE_COLUMNS = [
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

# Represented every 5 seconds in the prototype process grid and replay.
PROCESS_VARIABLES = [
    "Dryer Air Temperature",
    "Cooler Air Temperature",
    "Air Flow Rate",
    "Wet Product Feed Rate",
    "Product Inlet Temperature",
    "Residence Time",
    "Vacuum",
    "Steam Pressure",
    "Fan Speed",
]

# Only present when a laboratory analysis exists (about every two hours).
QUALITY_VARIABLES = [
    "Product Density",
    "Final Product Temp",
    "Final Moisture (%H2O)",
]

RAW_TO_SNAKE = {
    "Dryer Air Temperature": "dryer_air_temperature",
    "Cooler Air Temperature": "cooler_air_temperature",
    "Air Flow Rate": "air_flow_rate",
    "Wet Product Feed Rate": "wet_product_feed_rate",
    "Product Inlet Temperature": "product_inlet_temperature",
    "Residence Time": "residence_time",
    "Vacuum": "vacuum",
    "Steam Pressure": "steam_pressure",
    "Fan Speed": "fan_speed",
    "Product Density": "product_density",
    "Final Product Temp": "final_product_temp",
    "Final Moisture (%H2O)": "final_moisture",
}

_TIMESTAMP_FORMATS = (
    "%Y-%m-%d %H:%M:%S",
    "%d/%m/%Y %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%d/%m/%Y %H:%M",
)


@dataclass
class ProcessTableReport:
    """Validation outcome of one process-table build."""

    total_source_rows: int
    process_rows: int
    duplicate_timestamps_removed: int
    expected_interval_seconds: int
    gap_count: int
    missing_interval_rows: int
    gaps: list[tuple[pd.Timestamp, pd.Timestamp, int]] = field(
        default_factory=list
    )
    filled_rows: int = 0

    @property
    def interval_is_valid(self) -> bool:
        return self.gap_count == 0


def build_timestamp(dataframe: pd.DataFrame) -> pd.Series:
    """Combine the raw Date and Time columns into a reliable Timestamp.

    One explicit format must parse every row; mixed or partial parses are
    rejected so a silently misread date order can never enter the pipeline.
    """

    combined = (
        dataframe["Date"].astype(str).str.strip()
        + " "
        + dataframe["Time"].astype(str).str.strip()
    )

    for candidate_format in _TIMESTAMP_FORMATS:
        parsed = pd.to_datetime(
            combined, format=candidate_format, errors="coerce"
        )
        if not parsed.isna().any():
            return parsed

    failing = combined[
        pd.to_datetime(combined, format=_TIMESTAMP_FORMATS[0], errors="coerce")
        .isna()
    ]
    raise ValueError(
        "Date/Time could not be parsed with a single consistent format. "
        f"First unparseable values: {failing.head(3).tolist()}"
    )


def load_raw_source(source_path: Path | str) -> pd.DataFrame:
    """Load the raw CSV and verify the exact expected column names."""

    source_path = Path(source_path)
    if not source_path.exists():
        raise FileNotFoundError(f"Source CSV was not found:\n{source_path}")

    dataframe = pd.read_csv(source_path, encoding="utf-8-sig")
    dataframe.columns = [str(column).strip() for column in dataframe.columns]

    missing = [
        column
        for column in RAW_SOURCE_COLUMNS
        if column not in dataframe.columns
    ]
    if missing:
        raise ValueError(f"Source CSV is missing required columns: {missing}")

    return dataframe.loc[:, RAW_SOURCE_COLUMNS].copy()


def build_process_table(
    raw: pd.DataFrame,
    expected_interval_seconds: int = PROCESS_INTERVAL_SECONDS,
    short_gap_fill_limit_intervals: int = 0,
) -> tuple[pd.DataFrame, ProcessTableReport]:
    """Build the 5-second process table: Timestamp + nine process variables.

    Rows are sorted chronologically, exact duplicate timestamps are removed
    (first occurrence wins — the replayed historian value), and process
    variables are coerced to numeric. Gaps in the 5-second grid are
    reported, never silently invented.

    ``short_gap_fill_limit_intervals`` optionally forward-fills gaps of at
    most that many missing grid points from the previous observation (a
    documented, justified last-value-hold). Filling never looks forward, and
    filled rows are flagged in the ``filled_from_previous`` column. The
    default of 0 preserves every real gap.
    """

    timestamps = build_timestamp(raw)

    process = raw.loc[:, PROCESS_VARIABLES].copy()
    for column in PROCESS_VARIABLES:
        process[column] = pd.to_numeric(process[column], errors="coerce")

    process.insert(0, "Timestamp", timestamps)
    process = process.sort_values("Timestamp", kind="stable")

    duplicate_mask = process["Timestamp"].duplicated(keep="first")
    duplicates_removed = int(duplicate_mask.sum())
    process = process.loc[~duplicate_mask].reset_index(drop=True)

    interval = pd.Timedelta(seconds=expected_interval_seconds)
    deltas = process["Timestamp"].diff().dropna()
    gap_mask = deltas != interval

    gaps: list[tuple[pd.Timestamp, pd.Timestamp, int]] = []
    missing_rows = 0
    for position in deltas.index[gap_mask]:
        gap_end = process.loc[position, "Timestamp"]
        gap_start = process.loc[position - 1, "Timestamp"]
        span_seconds = (gap_end - gap_start).total_seconds()
        missing_here = max(
            int(round(span_seconds / expected_interval_seconds)) - 1, 0
        )
        missing_rows += missing_here
        gaps.append((gap_start, gap_end, missing_here))

    process["filled_from_previous"] = False
    filled_rows = 0

    if short_gap_fill_limit_intervals > 0 and gaps:
        fill_frames = []
        for gap_start, gap_end, missing_here in gaps:
            if 0 < missing_here <= short_gap_fill_limit_intervals:
                grid = pd.date_range(
                    gap_start + interval,
                    gap_end - interval,
                    freq=interval,
                )
                # Last-value hold from the observation before the gap only:
                # never from the future side.
                source_row = process.loc[
                    process["Timestamp"] == gap_start, PROCESS_VARIABLES
                ].iloc[0]
                frame = pd.DataFrame(
                    [source_row.to_dict()] * len(grid)
                )
                frame.insert(0, "Timestamp", grid)
                frame["filled_from_previous"] = True
                fill_frames.append(frame)
                filled_rows += len(grid)
        if fill_frames:
            process = (
                pd.concat([process, *fill_frames], ignore_index=True)
                .sort_values("Timestamp", kind="stable")
                .reset_index(drop=True)
            )

    report = ProcessTableReport(
        total_source_rows=len(raw),
        process_rows=len(process),
        duplicate_timestamps_removed=duplicates_removed,
        expected_interval_seconds=expected_interval_seconds,
        gap_count=len(gaps),
        missing_interval_rows=missing_rows,
        gaps=gaps,
        filled_rows=filled_rows,
    )

    return process, report


def build_lab_table(raw: pd.DataFrame) -> pd.DataFrame:
    """Build the laboratory table: one row per actual laboratory sample.

    A row qualifies when at least one quality value exists. Row count must
    therefore match the number of laboratory analyses, never the number of
    process observations.
    """

    timestamps = build_timestamp(raw)

    quality = raw.loc[:, QUALITY_VARIABLES].copy()
    for column in QUALITY_VARIABLES:
        quality[column] = pd.to_numeric(quality[column], errors="coerce")

    has_sample = quality.notna().any(axis=1)

    lab = quality.loc[has_sample].copy()
    lab.insert(0, "Sample Timestamp", timestamps.loc[has_sample])
    lab = (
        lab.sort_values("Sample Timestamp", kind="stable")
        .drop_duplicates(subset="Sample Timestamp", keep="first")
        .reset_index(drop=True)
    )

    return lab
