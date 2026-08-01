"""Row-window persistence logic for anomaly candidates."""

from __future__ import annotations

import pandas as pd


def apply_persistence_logic(
    score_table: pd.DataFrame,
    expected_sample_interval: pd.Timedelta,
    cadence_gap_tolerance: float = 1.5,
    window_observations: int = 3,
    minimum_candidates: int = 2,
) -> pd.DataFrame:
    """Convert raw candidates into gap-aware persistent alarm episodes."""

    if window_observations < 1:
        raise ValueError("window_observations must be positive.")
    if not 1 <= minimum_candidates <= window_observations:
        raise ValueError("minimum_candidates must lie within the persistence window.")
    if cadence_gap_tolerance <= 1:
        raise ValueError("cadence_gap_tolerance must be greater than 1.")

    required = {"timestamp", "Split", "Raw anomaly flag"}
    missing = sorted(required - set(score_table.columns))
    if missing:
        raise KeyError(f"Persistence input columns are missing: {missing}")

    alarm_table = score_table.sort_values("timestamp", kind="stable").copy()
    split_boundary = alarm_table["Split"].ne(alarm_table["Split"].shift())
    cadence_gap = alarm_table["timestamp"].diff().gt(
        expected_sample_interval * cadence_gap_tolerance
    )
    alarm_table["Cadence segment"] = (split_boundary | cadence_gap).cumsum()
    groups = alarm_table.groupby(["Split", "Cadence segment"], sort=False)
    alarm_table["Candidates in persistence window"] = (
        groups["Raw anomaly flag"]
        .transform(
            lambda flags: flags.astype(int)
            .rolling(window=window_observations, min_periods=1)
            .sum()
        )
        .astype(int)
    )
    alarm_table["Persistent alarm"] = (
        alarm_table["Candidates in persistence window"] >= minimum_candidates
    )
    previous_alarm_state = alarm_table.groupby(
        ["Split", "Cadence segment"], sort=False
    )["Persistent alarm"].shift(fill_value=False)
    alarm_starts = alarm_table["Persistent alarm"] & ~previous_alarm_state
    alarm_numbers = alarm_starts.cumsum()
    alarm_table["Alarm episode"] = alarm_numbers.where(
        alarm_table["Persistent alarm"]
    ).astype("Int64")
    return alarm_table.reset_index(drop=True)
